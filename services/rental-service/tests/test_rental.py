import sys
import os
import uuid
from datetime import datetime, timezone
import grpc
import pytest
from google.protobuf.timestamp_pb2 import Timestamp

current_dir = os.path.dirname(os.path.abspath(__file__))
rental_service_dir = os.path.abspath(os.path.join(current_dir, ".."))
generated_dir = os.path.join(rental_service_dir, "app", "generated")

sys.path.insert(0, rental_service_dir)
sys.path.insert(0, generated_dir)

from app.generated.rental.v1 import rental_pb2, rental_pb2_grpc
import vehicle_pb2
import vehicle_pb2_grpc

from app.db import SessionLocal
from app.repository import RentalModel


def ts(year, month, day):
    timestamp = Timestamp()
    timestamp.FromDatetime(datetime(year, month, day, tzinfo=timezone.utc))
    return timestamp


@pytest.fixture
def vehiculo_id():
    # Rental Service valida la operatividad contra Vehicle Service: necesita un vehículo real.
    channel = grpc.insecure_channel(os.getenv("VEHICLE_GRPC_ADDRESS", "localhost:50051"))
    stub = vehicle_pb2_grpc.VehicleServiceStub(channel)
    vehiculo = stub.CrearVehiculo(vehicle_pb2.CrearVehiculoRequest(
        marca="Test",
        modelo="Rental",
        patente=f"T{uuid.uuid4().hex[:10].upper()}",
        anio=2024,
        tipo=vehicle_pb2.TIPO_VEHICULO_SEDAN,
        precio_diario=100,
    )).vehiculo
    yield str(vehiculo.id)
    db = SessionLocal()
    try:
        # Solo las reservas de prueba: los tests corren contra la base del stack.
        db.query(RentalModel).filter(RentalModel.vehiculo_id == str(vehiculo.id)).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()
    stub.DarDeBajaVehiculo(vehicle_pb2.DarDeBajaVehiculoRequest(id=vehiculo.id))
    channel.close()

@pytest.fixture(scope="module")
def pyt_channel():
    channel = grpc.insecure_channel('localhost:50053')
    yield channel
    channel.close()

@pytest.fixture(scope="module")
def stub(pyt_channel):
    return rental_pb2_grpc.RentalServiceStub(pyt_channel)

def test_crear_y_cancelar_renta(stub, vehiculo_id):
    response = stub.CrearRenta(rental_pb2.CrearRentaRequest(
        cliente_id="cliente-test-1",
        vehiculo_id=vehiculo_id,
        fecha_inicio=ts(2030, 12, 1),
        fecha_fin=ts(2030, 12, 5),
        precio_diario=62.5
    )).renta
    assert response.id != ""
    assert response.estado == rental_pb2.ESTADO_RENTA_CONFIRMADA
    assert response.precio_total == 250.0
    assert response.fecha_inicio == ts(2030, 12, 1)

    cancelada = stub.CancelarRenta(rental_pb2.CancelarRentaRequest(id=response.id)).renta
    assert cancelada.estado == rental_pb2.ESTADO_RENTA_CANCELADA

def test_solapamiento_reservas(stub, vehiculo_id):
    stub.CrearRenta(rental_pb2.CrearRentaRequest(
        cliente_id="cliente-test-2",
        vehiculo_id=vehiculo_id,
        fecha_inicio=ts(2030, 12, 10),
        fecha_fin=ts(2030, 12, 15),
        precio_diario=60.0
    ))

    solapamiento = stub.VerificarSolapamiento(rental_pb2.VerificarSolapamientoRequest(
        vehiculo_id=vehiculo_id,
        fecha_inicio=ts(2030, 12, 12),
        fecha_fin=ts(2030, 12, 18),
    ))
    assert solapamiento.hay_solapamiento is True

    with pytest.raises(grpc.RpcError) as exc_info:
        stub.CrearRenta(rental_pb2.CrearRentaRequest(
            cliente_id="cliente-test-3",
            vehiculo_id=vehiculo_id,
            fecha_inicio=ts(2030, 12, 12),
            fecha_fin=ts(2030, 12, 18),
            precio_diario=60.0
        ))

    assert exc_info.value.code() == grpc.StatusCode.ALREADY_EXISTS

def test_rechaza_fin_anterior_al_inicio(stub):
    with pytest.raises(grpc.RpcError) as exc_info:
        stub.CrearRenta(rental_pb2.CrearRentaRequest(
            cliente_id="cliente-test-4",
            vehiculo_id="1",
            fecha_inicio=ts(2030, 12, 20),
            fecha_fin=ts(2030, 12, 19),
            precio_diario=60.0
        ))

    assert exc_info.value.code() == grpc.StatusCode.INVALID_ARGUMENT

def test_rechaza_fechas_faltantes(stub):
    with pytest.raises(grpc.RpcError) as exc_info:
        stub.CrearRenta(rental_pb2.CrearRentaRequest(
            cliente_id="cliente-test-5",
            vehiculo_id="1",
            precio_diario=60.0
        ))

    assert exc_info.value.code() == grpc.StatusCode.INVALID_ARGUMENT
