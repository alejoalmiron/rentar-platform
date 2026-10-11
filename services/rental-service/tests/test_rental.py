import sys
import os
import grpc
import pytest

current_dir = os.path.dirname(os.path.abspath(__file__))
rental_service_dir = os.path.abspath(os.path.join(current_dir, ".."))
generated_dir = os.path.join(rental_service_dir, "app", "generated")

sys.path.insert(0, rental_service_dir)
sys.path.insert(0, generated_dir)

from app.generated.rental.v1 import rental_pb2, rental_pb2_grpc

@pytest.fixture(scope="module")
def pyt_channel():
    channel = grpc.insecure_channel('localhost:50053')
    yield channel
    channel.close()

@pytest.fixture(scope="module")
def stub(pyt_channel):
    return rental_pb2_grpc.RentalServiceStub(pyt_channel)

def test_crear_y_cancelar_renta(stub):
    response = stub.CrearRenta(rental_pb2.CrearRentaRequest(
        clienteId="cliente-test-1",
        vehiculoId="vehiculo-test-A",
        fechaInicio="2026-12-01",
        fechaFin="2026-12-05",
        precioTotal=250.0
    ))
    assert response.id != ""
    assert response.estado == "CONFIRMADA"
    renta_id = response.id

    cancel_response = stub.CancelarRenta(rental_pb2.CancelarRentaRequest(id=renta_id))
    assert cancel_response.estado == "CANCELADA"

def test_solapamiento_reservas(stub):
    stub.CrearRenta(rental_pb2.CrearRentaRequest(
        clienteId="cliente-test-2",
        vehiculoId="vehiculo-test-B",
        fechaInicio="2026-12-10",
        fechaFin="2026-12-15",
        precioTotal=300.0
    ))

    with pytest.raises(grpc.RpcError) as exc_info:
        stub.CrearRenta(rental_pb2.CrearRentaRequest(
            clienteId="cliente-test-3",
            vehiculoId="vehiculo-test-B",  
            fechaInicio="2026-12-12",     
            fechaFin="2026-12-18",
            precioTotal=350.0
        ))
    
    assert exc_info.value.code() == grpc.StatusCode.ALREADY_EXISTS