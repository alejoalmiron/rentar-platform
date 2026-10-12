from concurrent import futures
import time

# pylint: disable=import-error, no-name-in-module, wrong-import-position, no-member
import grpc

from app.customer.v1 import customer_pb2 as pb2
from app.customer.v1 import customer_pb2_grpc as pb2_grpc
from .service import CustomerServiceLogic


class CustomerServiceServicer(pb2_grpc.CustomerServiceServicer):
    def ListCustomers(self, request, context):
        customers = CustomerServiceLogic.list_customers()
        response_list = [
            pb2.CustomerResponse(
                id=c.id, dni=c.dni, nombre=c.nombre, apellido=c.apellido, email=c.email, activo=c.activo
            ) for c in customers
        ]
        return pb2.CustomerListResponse(customers=response_list)

    def GetCustomerById(self, request, context):
        c = CustomerServiceLogic.get_customer_by_id(request.id)
        if not c:
            context.abort(grpc.StatusCode.NOT_FOUND, "Cliente no encontrado")
        return pb2.CustomerResponse(id=c.id, dni=c.dni, nombre=c.nombre, apellido=c.apellido, email=c.email, activo=c.activo)

    def CreateCustomer(self, request, context):
        try:
            c = CustomerServiceLogic.create_customer(request)
            return pb2.CustomerResponse(id=c.id, dni=c.dni, nombre=c.nombre, apellido=c.apellido, email=c.email, activo=c.activo)
        except ValueError as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))

    def UpdateCustomer(self, request, context):
        try:
            c = CustomerServiceLogic.update_customer(request.id, request)
            return pb2.CustomerResponse(id=c.id, dni=c.dni, nombre=c.nombre, apellido=c.apellido, email=c.email, activo=c.activo)
        except ValueError as e:
            context.abort(grpc.StatusCode.NOT_FOUND, str(e))

    def DeactivateCustomer(self, request, context):
        try:
            c = CustomerServiceLogic.deactivate_customer(request.id)
            return pb2.CustomerResponse(id=c.id, dni=c.dni, nombre=c.nombre, apellido=c.apellido, email=c.email, activo=c.activo)
        except ValueError as e:
            context.abort(grpc.StatusCode.NOT_FOUND, str(e))

    def ValidateActiveCustomer(self, request, context):
        result = CustomerServiceLogic.validate_customer_active(request.id)
        return pb2.ValidateCustomerResponse(
            exists=result["exists"],
            is_active=result["is_active"],
            message=result["message"]
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_CustomerServiceServicer_to_server(CustomerServiceServicer(), server)
    server.add_insecure_port('[::]:50052')
    server.start()
    print("🚀 Customer Service gRPC corriendo en el puerto 50052...")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()