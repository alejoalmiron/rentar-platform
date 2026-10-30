from concurrent import futures
import os
import time

# pylint: disable=import-error, no-name-in-module, wrong-import-position, no-member
import grpc
from sqlalchemy.exc import OperationalError

from app.customer.v1 import customer_pb2 as pb2
from app.customer.v1 import customer_pb2_grpc as pb2_grpc
from .service import CustomerNotFoundError, CustomerServiceLogic, DuplicateCustomerError
from .seed import seed_users

ROLES_PROTO = {"ADMIN": pb2.ROL_ADMIN, "CLIENTE": pb2.ROL_CLIENTE}


def seed_with_retry(max_attempts=20, delay_seconds=3):
    """Espera a que MySQL esté disponible antes de ejecutar el seed."""
    for attempt in range(1, max_attempts + 1):
        try:
            seed_users()
            return
        except OperationalError:
            print(f"Base de datos no disponible (intento {attempt}/{max_attempts}). Reintentando en {delay_seconds}s...")
            if attempt == max_attempts:
                raise
            time.sleep(delay_seconds)


def _a_proto(c):
    return pb2.Cliente(
        id=c.id, dni=c.dni, nombre=c.nombre, apellido=c.apellido,
        email=c.email, activo=c.activo, telefono=c.telefono or ""
    )


class CustomerServiceServicer(pb2_grpc.CustomerServiceServicer):
    def ListarClientes(self, request, context):
        customers = CustomerServiceLogic.list_customers()
        return pb2.ListarClientesResponse(clientes=[_a_proto(c) for c in customers])

    def ObtenerCliente(self, request, context):
        c = CustomerServiceLogic.get_customer_by_id(request.id)
        if not c:
            context.abort(grpc.StatusCode.NOT_FOUND, "Cliente no encontrado")
        return pb2.ObtenerClienteResponse(cliente=_a_proto(c))

    def CrearCliente(self, request, context):
        try:
            c = CustomerServiceLogic.create_customer(request)
            return pb2.CrearClienteResponse(cliente=_a_proto(c))
        except DuplicateCustomerError as e:
            context.abort(grpc.StatusCode.ALREADY_EXISTS, str(e))
        except ValueError as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))

    def ActualizarCliente(self, request, context):
        try:
            c = CustomerServiceLogic.update_customer(request.id, request)
            return pb2.ActualizarClienteResponse(cliente=_a_proto(c))
        except CustomerNotFoundError as e:
            context.abort(grpc.StatusCode.NOT_FOUND, str(e))
        except DuplicateCustomerError as e:
            context.abort(grpc.StatusCode.ALREADY_EXISTS, str(e))

    def DarDeBajaCliente(self, request, context):
        try:
            c = CustomerServiceLogic.deactivate_customer(request.id)
            return pb2.DarDeBajaClienteResponse(cliente=_a_proto(c))
        except CustomerNotFoundError as e:
            context.abort(grpc.StatusCode.NOT_FOUND, str(e))

    def ValidarClienteActivo(self, request, context):
        result = CustomerServiceLogic.validate_customer_active(request.id)
        return pb2.ValidarClienteActivoResponse(
            existe=result["exists"],
            activo=result["is_active"],
            mensaje=result["message"]
        )

    def AutenticarUsuario(self, request, context):
        if not request.usuario or not request.contrasena:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Usuario y contraseña son obligatorios")
        user = CustomerServiceLogic.authenticate_user(request.usuario, request.contrasena)
        if not user:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Usuario o contraseña inválidos")
        if user["role"] not in ROLES_PROTO:
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "El rol de la cuenta no es válido")
        return pb2.AutenticarUsuarioResponse(
            usuario_id=user["id"],
            usuario=user["username"],
            rol=ROLES_PROTO[user["role"]],
            cliente_id=user["customer_id"],
        )

def serve():
    seed_with_retry()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_CustomerServiceServicer_to_server(CustomerServiceServicer(), server)
    port = os.getenv('PORT', '50052')
    if server.add_insecure_port(f'[::]:{port}') == 0:
        raise RuntimeError(f'No se pudo abrir el puerto gRPC {port}')
    server.start()
    print(f"Customer Service gRPC corriendo en el puerto {port}...")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
