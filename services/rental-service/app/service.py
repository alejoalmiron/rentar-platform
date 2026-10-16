from datetime import datetime, timezone
import math
import grpc
from app.db import SessionLocal
from app.repository import RentalRepository
from app.generated.rental.v1 import rental_pb2, rental_pb2_grpc

class RentalServiceServicer(rental_pb2_grpc.RentalServiceServicer):

    @staticmethod
    def _parse_date(value):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    @classmethod
    def _validated_period(cls, fecha_inicio, fecha_fin, context):
        start = cls._parse_date(fecha_inicio)
        end = cls._parse_date(fecha_fin)
        if start is None or end is None:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Las fechas deben ser ISO-8601 válidas")
        if start <= datetime.now(timezone.utc):
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "La fecha de inicio debe ser futura")
        if end <= start:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "La fecha de fin debe ser posterior al inicio")
        return start, end

    def CrearRenta(self, request, context):
        start, end = self._validated_period(request.fechaInicio, request.fechaFin, context)
        if not request.clienteId or not request.vehiculoId:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Cliente y vehículo son obligatorios")
        if not math.isfinite(request.precioDiario) or request.precioDiario <= 0:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "El precio diario debe ser mayor que cero")

        days = math.ceil((end - start).total_seconds() / 86400)
        total = days * request.precioDiario
        db = SessionLocal()
        try:
            datos_renta = {
                "clienteId": request.clienteId,
                "vehiculoId": request.vehiculoId,
                "fechaInicio": request.fechaInicio,
                "fechaFin": request.fechaFin,
                "precioTotal": total,
            }
            try:
                nueva_renta = RentalRepository.crear_renta(db, datos_renta)
            except ValueError as error:
                context.abort(grpc.StatusCode.ALREADY_EXISTS, str(error))
            except TimeoutError as error:
                context.abort(grpc.StatusCode.UNAVAILABLE, str(error))

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

    def ObtenerHistorialRentas(self, request, context):
        db = SessionLocal()
        try:
            rentas = RentalRepository.obtener_historial(db, request.clienteId)
            lista_respuesta = [
                rental_pb2.RentaResponse(
                    id=r.id,
                    clienteId=r.cliente_id,
                    vehiculoId=r.vehiculo_id,
                    fechaInicio=r.fecha_inicio,
                    fechaFin=r.fecha_fin,
                    estado=r.estado,
                    precioTotal=r.precio_total,
                ) for r in rentas
            ]
            return rental_pb2.ListarRentasResponse(rentas=lista_respuesta)
        finally:
            db.close()

    def CancelarRenta(self, request, context):
        db = SessionLocal()
        try:
            renta = RentalRepository.obtener_renta(db, request.id)
            if not renta:
                context.abort(grpc.StatusCode.NOT_FOUND, "Renta no encontrada para cancelar")
            if renta.estado == "CANCELADA":
                context.abort(grpc.StatusCode.FAILED_PRECONDITION, "La reserva ya está cancelada")
            start = self._parse_date(renta.fecha_inicio)
            if start is not None and start <= datetime.now(timezone.utc):
                context.abort(grpc.StatusCode.FAILED_PRECONDITION, "No se puede cancelar una reserva ya iniciada")
            renta = RentalRepository.cancelar_renta(db, request.id)

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
        self._validated_period(request.fechaInicio, request.fechaFin, context)
        db = SessionLocal()
        try:
            solapado = RentalRepository.verificar_solapamiento(
                db, request.vehiculoId, request.fechaInicio, request.fechaFin
            )
            return rental_pb2.VerificarSolapamientoResponse(haySolapamiento=solapado)
        finally:
            db.close()