import unittest
from unittest.mock import Mock, patch

import grpc
from sqlalchemy.exc import IntegrityError

from app.db import engine
from app import service
from app.generated import vehicle_pb2


class RpcAbort(Exception):
    def __init__(self, status, details):
        self.status = status
        self.details = details


def abort_rpc(status, details):
    raise RpcAbort(status, details)


class VehicleServiceTests(unittest.TestCase):
    def setUp(self):
        self.servicer = service.VehicleServiceServicer()
        self.context = Mock()
        self.context.abort.side_effect = abort_rpc
        self.db = Mock()

    def test_database_pool_checks_connections_before_reusing_them(self):
        self.assertTrue(engine.pool._pre_ping)

    def test_stolen_verification_disables_vehicle(self):
        with patch.object(service, "SessionLocal", return_value=self.db):
            service.handle_verificacion_resultado({"vehiculoId": 15, "resultado": "ROBADO"})

        statement, parameters = self.db.execute.call_args.args
        self.assertIn("operativo = FALSE", str(statement))
        self.assertEqual(parameters, {"resultado": "ROBADO", "id": 15})
        self.db.commit.assert_called_once()

    def test_valid_verification_does_not_change_operability(self):
        with patch.object(service, "SessionLocal", return_value=self.db):
            service.handle_verificacion_resultado({"vehiculoId": 15, "resultado": "VALIDADO"})

        statement, parameters = self.db.execute.call_args.args
        self.assertNotIn("operativo", str(statement))
        self.assertEqual(parameters, {"resultado": "VALIDADO", "id": 15})
        self.db.commit.assert_called_once()

    def test_get_vehicles_returns_data_and_closes_session(self):
        vehicle = Mock(
            id=7,
            marca="Toyota",
            modelo="Corolla",
            patente="AA123BB",
            operativo=True,
            activo=True,
            anio=2024,
            color="Gris",
            tipo="SEDAN",
            precio_diario=45000.0,
            estado="DISPONIBLE",
            estado_verificacion="VALIDADO",
        )

        with (
            patch.object(service, "SessionLocal", return_value=self.db),
            patch.object(service.repository, "get_all", return_value=[vehicle]),
        ):
            response = self.servicer.ListarVehiculos(vehicle_pb2.ListarVehiculosRequest(), self.context)

        self.assertEqual(len(response.vehiculos), 1)
        self.assertEqual(response.vehiculos[0].id, 7)
        self.assertEqual(response.vehiculos[0].patente, "AA123BB")
        self.assertEqual(response.vehiculos[0].tipo, vehicle_pb2.TIPO_VEHICULO_SEDAN)
        self.assertEqual(response.vehiculos[0].estado, vehicle_pb2.ESTADO_VEHICULO_DISPONIBLE)
        self.db.close.assert_called_once()

    def test_create_vehicle_starts_available_and_stores_domain_type(self):
        created = Mock(
            id=8, marca="Ford", modelo="Ranger", patente="AC456DE", operativo=True, activo=True,
            anio=2023, color=None, tipo="PICKUP", precio_diario=60000.0, estado="DISPONIBLE",
            estado_verificacion="PENDIENTE",
        )
        with (
            patch.object(service, "SessionLocal", return_value=self.db),
            patch.object(service.repository, "create", return_value=created) as create,
            patch.object(service, "publicar"),
        ):
            response = self.servicer.CrearVehiculo(
                vehicle_pb2.CrearVehiculoRequest(
                    marca="Ford",
                    modelo="Ranger",
                    patente="ac456de",
                    anio=2023,
                    tipo=vehicle_pb2.TIPO_VEHICULO_PICKUP,
                    precio_diario=60000.0,
                ),
                self.context,
            )

        data = create.call_args.args[1]
        self.assertEqual(data["estado"], "DISPONIBLE")
        self.assertEqual(data["tipo"], "PICKUP")
        self.assertEqual(data["patente"], "AC456DE")
        self.assertEqual(response.vehiculo.tipo, vehicle_pb2.TIPO_VEHICULO_PICKUP)

    def test_create_vehicle_rejects_unspecified_type(self):
        with self.assertRaises(RpcAbort) as raised:
            self.servicer.CrearVehiculo(
                vehicle_pb2.CrearVehiculoRequest(
                    marca="Ford", modelo="Ka", patente="AD789FG", anio=2020, precio_diario=30000.0,
                ),
                self.context,
            )

        self.assertEqual(raised.exception.status, grpc.StatusCode.INVALID_ARGUMENT)

    def test_update_vehicle_rejects_unspecified_state(self):
        with self.assertRaises(RpcAbort) as raised:
            self.servicer.ActualizarVehiculo(
                vehicle_pb2.ActualizarVehiculoRequest(
                    id=7, marca="Toyota", modelo="Corolla", anio=2024,
                    tipo=vehicle_pb2.TIPO_VEHICULO_SEDAN, precio_diario=45000.0,
                ),
                self.context,
            )

        self.assertEqual(raised.exception.status, grpc.StatusCode.INVALID_ARGUMENT)

    def test_get_vehicle_by_id_returns_not_found_and_closes_session(self):
        with (
            patch.object(service, "SessionLocal", return_value=self.db),
            patch.object(service.repository, "get_by_id", return_value=None),
            self.assertRaises(RpcAbort) as raised,
        ):
            self.servicer.ObtenerVehiculo(vehicle_pb2.ObtenerVehiculoRequest(id=42), self.context)

        self.assertEqual(raised.exception.status, grpc.StatusCode.NOT_FOUND)
        self.db.close.assert_called_once()

    def test_duplicate_plate_aborts_create_and_rolls_back(self):
        error = IntegrityError("insert", {}, Exception("duplicate"))
        with (
            patch.object(service, "SessionLocal", return_value=self.db),
            patch.object(service.repository, "create", side_effect=error),
            self.assertRaises(RpcAbort) as raised,
        ):
            self.servicer.CrearVehiculo(
                vehicle_pb2.CrearVehiculoRequest(
                    marca="Toyota",
                    modelo="Corolla",
                    patente="AA123BB",
                    anio=2024,
                    color="Gris",
                    tipo=vehicle_pb2.TIPO_VEHICULO_SEDAN,
                    precio_diario=45000.0,
                ),
                self.context,
            )

        self.assertEqual(raised.exception.status, grpc.StatusCode.ALREADY_EXISTS)
        self.db.rollback.assert_called_once()
        self.db.close.assert_called_once()

    def test_delete_missing_vehicle_returns_not_found(self):
        with (
            patch.object(service, "SessionLocal", return_value=self.db),
            patch.object(service.repository, "delete", return_value=None),
            self.assertRaises(RpcAbort) as raised,
        ):
            self.servicer.DarDeBajaVehiculo(vehicle_pb2.DarDeBajaVehiculoRequest(id=42), self.context)

        self.assertEqual(raised.exception.status, grpc.StatusCode.NOT_FOUND)
        self.db.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
