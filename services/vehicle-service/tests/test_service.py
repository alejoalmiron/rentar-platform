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
        )

        with (
            patch.object(service, "SessionLocal", return_value=self.db),
            patch.object(service.repository, "get_all", return_value=[vehicle]),
        ):
            response = self.servicer.GetVehicles(vehicle_pb2.Empty(), self.context)

        self.assertEqual(len(response.vehicles), 1)
        self.assertEqual(response.vehicles[0].id, 7)
        self.assertEqual(response.vehicles[0].patente, "AA123BB")
        self.db.close.assert_called_once()

    def test_get_vehicle_by_id_returns_not_found_and_closes_session(self):
        with (
            patch.object(service, "SessionLocal", return_value=self.db),
            patch.object(service.repository, "get_by_id", return_value=None),
            self.assertRaises(RpcAbort) as raised,
        ):
            self.servicer.GetVehicleById(vehicle_pb2.VehicleIdRequest(id=42), self.context)

        self.assertEqual(raised.exception.status, grpc.StatusCode.NOT_FOUND)
        self.db.close.assert_called_once()

    def test_duplicate_plate_aborts_create_and_rolls_back(self):
        error = IntegrityError("insert", {}, Exception("duplicate"))
        with (
            patch.object(service, "SessionLocal", return_value=self.db),
            patch.object(service.repository, "create", side_effect=error),
            self.assertRaises(RpcAbort) as raised,
        ):
            self.servicer.CreateVehicle(
                vehicle_pb2.CreateVehicleRequest(
                    marca="Toyota",
                    modelo="Corolla",
                    patente="AA123BB",
                    anio=2024,
                    color="Gris",
                    tipo="SEDAN",
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
            self.servicer.DeleteVehicle(vehicle_pb2.VehicleIdRequest(id=42), self.context)

        self.assertEqual(raised.exception.status, grpc.StatusCode.NOT_FOUND)
        self.db.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
