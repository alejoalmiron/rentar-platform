import os

import grpc

import vehicle_pb2
import vehicle_pb2_grpc


_channel = grpc.insecure_channel(
    os.getenv("VEHICLE_GRPC_ADDRESS", "localhost:50051")
)
_stub = vehicle_pb2_grpc.VehicleServiceStub(_channel)


def is_operational(vehicle_id):
    try:
        numeric_vehicle_id = int(vehicle_id)
    except (TypeError, ValueError) as error:
        raise ValueError("El id del vehículo debe ser numérico") from error

    if numeric_vehicle_id <= 0 or numeric_vehicle_id > 2_147_483_647:
        raise ValueError("El id del vehículo debe ser un entero positivo válido")

    response = _stub.VerificarOperatividad(
        vehicle_pb2.VerificarOperatividadRequest(id=numeric_vehicle_id),
        timeout=5,
    )
    return response.operativo
