import grpc
from app.db import SessionLocal
from app.repository import RentalRepository
from app.generated.rental.v1 import rental_pb2, rental_pb2_grpc

class RentalServiceServicer(rental_pb2_grpc.RentalServiceServicer):

    def CrearRenta(self, request, context):
        db = SessionLocal()
        try:
            hay_solapamiento = RentalRepository.verificar_solapamiento(
                db, request.vehiculoId, request.fechaInicio, request.fechaFin
            )
            
            if hay_solapamiento:
                context.set_code(grpc.StatusCode.ALREADY_EXISTS)
                context.set_details("El vehículo ya se encuentra reservado en esas fechas.")
                return rental_pb2.RentaResponse()

            datos_renta = {
                "clienteId": request.clienteId,
                "vehiculoId": request.vehiculoId,
                "fechaInicio": request.fechaInicio,
                "fechaFin": request.fechaFin,
                "precioTotal": request.precioTotal
            }
            
            nueva_renta = RentalRepository.crear_renta(db, datos_renta)
            
            return rental_pb2.RentaResponse(
                id=nueva_renta.id,
                clienteId=nueva_renta.cliente_id,
                vehiculoId=nueva_renta.vehiculo_id,
                fechaInicio=nueva_renta.fecha_inicio,
                fechaFin=nueva_renta.fecha_fin,
                estado=nueva_renta.estado,
                precioTotal=nueva_renta.precio_total
            )
        finally:
            db.close()

    def ObtenerRenta(self, request, context):
        db = SessionLocal()
        try:
            renta = RentalRepository.obtener_renta(db, request.id)
            if not renta:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Renta no encontrada.")
                return rental_pb2.RentaResponse()

            return rental_pb2.RentaResponse(
                id=renta.id,
                clienteId=renta.cliente_id,
                vehiculoId=renta.vehiculo_id,
                fechaInicio=renta.fecha_inicio,
                fechaFin=renta.fecha_fin,
                estado=renta.estado,
                precioTotal=renta.precio_total
            )
        finally:
            db.close()

    def ListarRentasPorCliente(self, request, context):
        db = SessionLocal()
        try:
            rentas = RentalRepository.listar_por_cliente(db, request.clienteId)
            lista_respuesta = [
                rental_pb2.RentaResponse(
                    id=r.id,
                    clienteId=r.cliente_id,
                    vehiculoId=r.vehiculo_id,
                    fechaInicio=r.fecha_inicio,
                    fechaFin=r.fecha_fin,
                    estado=r.estado,
                    precioTotal=r.precio_total
                ) for r in rentas
            ]
            return rental_pb2.ListarRentasResponse(rentas=lista_respuesta)
        finally:
            db.close()

    def CancelarRenta(self, request, context):
        db = SessionLocal()
        try:
            renta = RentalRepository.cancelar_renta(db, request.id)
            if not renta:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Renta no encontrada para cancelar.")
                return rental_pb2.RentaResponse()

            return rental_pb2.RentaResponse(
                id=renta.id,
                clienteId=renta.cliente_id,
                vehiculoId=renta.vehiculo_id,
                fechaInicio=renta.fecha_inicio,
                fechaFin=renta.fecha_fin,
                estado=renta.estado,
                precioTotal=renta.precio_total
            )
        finally:
            db.close()

    def VerificarSolapamiento(self, request, context):
        db = SessionLocal()
        try:
            solapado = RentalRepository.verificar_solapamiento(
                db, request.vehiculoId, request.fechaInicio, request.fechaFin
            )
            return rental_pb2.CheckOverlapResponse(haySolapamiento=solapado)
        finally:
            db.close()