import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import grpc
from google.protobuf.timestamp_pb2 import Timestamp

service_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, service_dir)
sys.path.insert(0, os.path.join(service_dir, "app", "generated"))

from app import service
from app.generated.rental.v1 import rental_pb2


class RpcAbort(Exception):
    def __init__(self, code, details):
        self.code = code
        self.details = details


def abort_rpc(code, details):
    raise RpcAbort(code, details)


def make_request():
    start = datetime.now(timezone.utc) + timedelta(days=2)
    end = start + timedelta(days=3)
    start_timestamp = Timestamp()
    end_timestamp = Timestamp()
    start_timestamp.FromDatetime(start)
    end_timestamp.FromDatetime(end)
    return rental_pb2.CrearRentaRequest(
        cliente_id="cliente-1",
        vehiculo_id="15",
        fecha_inicio=start_timestamp,
        fecha_fin=end_timestamp,
        precio_diario=100,
    )


class RentalOperativityGuardTests(unittest.TestCase):
    def setUp(self):
        self.context = Mock()
        self.context.abort.side_effect = abort_rpc
        self.servicer = service.RentalServiceServicer()

    def test_rejects_non_operational_vehicle_before_creating_rental(self):
        with (
            patch.object(service.vehicle_client, "is_operational", return_value=False),
            patch.object(service, "SessionLocal") as session_local,
            patch.object(service.RentalRepository, "crear_renta") as create_rental,
            self.assertRaises(RpcAbort) as raised,
        ):
            self.servicer.CrearRenta(make_request(), self.context)

        self.assertEqual(raised.exception.code, grpc.StatusCode.FAILED_PRECONDITION)
        session_local.assert_not_called()
        create_rental.assert_not_called()

    def test_fails_closed_when_vehicle_service_is_unavailable(self):
        unavailable = grpc.RpcError()
        unavailable.code = lambda: grpc.StatusCode.UNAVAILABLE
        unavailable.details = lambda: "Vehicle Service unavailable"

        with (
            patch.object(service.vehicle_client, "is_operational", side_effect=unavailable),
            patch.object(service, "SessionLocal") as session_local,
            self.assertRaises(RpcAbort) as raised,
        ):
            self.servicer.CrearRenta(make_request(), self.context)

        self.assertEqual(raised.exception.code, grpc.StatusCode.UNAVAILABLE)
        self.assertEqual(raised.exception.details, "Vehicle Service unavailable")
        session_local.assert_not_called()

    def test_creates_rental_when_vehicle_is_operational(self):
        db = Mock()
        created_rental = rental_pb2.Renta(id="renta-1")

        with (
            patch.object(service.vehicle_client, "is_operational", return_value=True) as check,
            patch.object(service, "SessionLocal", return_value=db),
            patch.object(service.RentalRepository, "crear_renta", return_value=Mock()) as create_rental,
            patch.object(service, "publicareventoreservaconfirmada"),
            patch.object(
                service.RentalServiceServicer,
                "_to_proto",
                return_value=created_rental,
            ),
        ):
            response = self.servicer.CrearRenta(make_request(), self.context)

        check.assert_called_once_with("15")
        create_rental.assert_called_once()
        self.assertEqual(response.renta.id, "renta-1")
        db.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
