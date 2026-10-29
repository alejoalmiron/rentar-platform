import sys
import os
import random
import pytest
import grpc


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import customer.v1.customer_pb2 as pb2
import customer.v1.customer_pb2_grpc as pb2_grpc

# Usamos un diccionario o variable compartida para guardar el ID creado dinámicamente
test_state = {"created_id": None}

@pytest.fixture(scope="module")
def grpc_channel():
    channel = grpc.insecure_channel('localhost:50052')
    stub = pb2_grpc.CustomerServiceStub(channel)
    yield stub
    channel.close()

def test_create_customer(grpc_channel):
    stub = grpc_channel
    
    # Generamos un DNI aleatorio para evitar conflictos de duplicados en MySQL
    random_dni = str(random.randint(40000000, 49999999))
    
    new_customer = pb2.CrearClienteRequest(
        dni=random_dni,
        nombre="Carlos",
        apellido="Gómez",
        email=f"carlos.{random_dni}@example.com"
    )
    created = stub.CrearCliente(new_customer).cliente
    
    assert created.id != ""
    assert created.nombre == "Carlos"
    assert created.activo is True
    
    # Guardamos el ID para las siguientes pruebas
    test_state["created_id"] = created.id

def test_get_customer_by_id(grpc_channel):
    assert test_state["created_id"] is not None, "Debe correrse después de crear el cliente"
    
    stub = grpc_channel
    found = stub.ObtenerCliente(pb2.ObtenerClienteRequest(id=test_state["created_id"])).cliente
    
    assert found.id == test_state["created_id"]
    assert found.nombre == "Carlos"

def test_update_customer(grpc_channel):
    assert test_state["created_id"] is not None
    
    stub = grpc_channel
    updated = stub.ActualizarCliente(pb2.ActualizarClienteRequest(
        id=test_state["created_id"],
        nombre="Carlos Alberto",
        apellido="Gómez",
        email="carlos.alberto@example.com"
    )).cliente

    assert updated.nombre == "Carlos Alberto"
    assert updated.email == "carlos.alberto@example.com"

def test_list_customers(grpc_channel):
    stub = grpc_channel
    response = stub.ListarClientes(pb2.ListarClientesRequest())
    
    # 🖨️ Agregamos esto para ver los datos en la terminal
    print("\n" + "="*40)
    print(f"📋 LISTADO DE CLIENTES (Total: {len(response.clientes)})")
    print("="*40)
    for c in response.clientes:
        print(f"ID: {c.id} | Nombre: {c.nombre} {c.apellido} | DNI: {c.dni} | Email: {c.email} | Activo: {c.activo}")
    print("="*40 + "\n")
    
    assert len(response.clientes) > 0

def test_deactivate_customer(grpc_channel):
    assert test_state["created_id"] is not None
    
    stub = grpc_channel
    deactivated = stub.DarDeBajaCliente(pb2.DarDeBajaClienteRequest(id=test_state["created_id"])).cliente
    
    assert deactivated.activo is False

def test_authenticate_admin(grpc_channel):
    response = grpc_channel.AutenticarUsuario(pb2.AutenticarUsuarioRequest(
        usuario=os.environ["SEED_ADMIN_USERNAME"],
        contrasena=os.environ["SEED_ADMIN_PASSWORD"],
    ))

    assert response.rol == pb2.ROL_ADMIN
    assert response.cliente_id == ""

def test_authenticate_demo_customer(grpc_channel):
    response = grpc_channel.AutenticarUsuario(pb2.AutenticarUsuarioRequest(
        usuario=os.environ["SEED_CLIENT_USERNAME"],
        contrasena=os.environ["SEED_CLIENT_PASSWORD"],
    ))

    assert response.rol == pb2.ROL_CLIENTE
    assert response.cliente_id != ""

def test_reject_invalid_credentials(grpc_channel):
    with pytest.raises(grpc.RpcError) as exc_info:
        grpc_channel.AutenticarUsuario(pb2.AutenticarUsuarioRequest(
            usuario=os.environ["SEED_ADMIN_USERNAME"],
            contrasena="incorrecta",
        ))

    assert exc_info.value.code() == grpc.StatusCode.UNAUTHENTICATED