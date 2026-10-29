from datetime import datetime, timezone
import math
import grpc
from google.protobuf.timestamp_pb2 import Timestamp
from app.db import SessionLocal
from app.repository import RentalRepository
from app.generated.rental.v1 import rental_pb2, rental_pb2_grpc

class RentalServiceServicer(rental_pb2_grpc.RentalServiceServicer):

    @staticmethod
    def _parse_date(value):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (AttributeError, TypeError, ValueError):
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _to_storage(moment):
        # Formato canónico en la base: ISO-8601 UTC con milisegundos
        # (igual a Date.toISOString), para que las comparaciones de texto
        # del control de solapamiento respeten el orden cronológico.
        return moment.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    @classmethod
    def _to_timestamp(cls, stored):
        timestamp = Timestamp()
        moment = cls._parse_date(stored)
        if moment is not None:
            timestamp.FromDatetime(moment)
        return timestamp

    @classmethod
    def _validated_period(cls, request, context):
        if not request.HasField("fecha_inicio") or not request.HasField("fecha_fin"):
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Las fechas de inicio y fin son obligatorias")
        start = request.fecha_inicio.ToDatetime(tzinfo=timezone.utc)
        end = request.fecha_fin.ToDatetime(tzinfo=timezone.utc)
        if start <= datetime.now(timezone.utc):
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "La fecha de inicio debe ser futura")
        if end <= start:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "La fecha de fin debe ser posterior al inicio")
        return start, end

    @classmethod
    def _to_proto(cls, renta):
        return rental_pb2.Renta(
            id=renta.id,
            cliente_id=renta.cliente_id,
            vehiculo_id=renta.vehiculo_id,
            fecha_inicio=cls._to_timestamp(renta.fecha_inicio),
            fecha_fin=cls._to_timestamp(renta.fecha_fin),
            estado=rental_pb2.EstadoRenta.Value(f"ESTADO_RENTA_{renta.estado}"),
            precio_total=renta.precio_total,
        )

    def CrearRenta(self, request, context):
        start, end = self._validated_period(request, context)
        if not request.cliente_id or not request.vehiculo_id:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Cliente y vehículo son obligatorios")
        if not math.isfinite(request.precio_diario) or request.precio_diario <= 0:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "El precio diario debe ser mayor que cero")

        days = math.ceil((end - start).total_seconds() / 86400)
        total = days * request.precio_diario
        db = SessionLocal()
        try:
            datos_renta = {
                "clienteId": request.cliente_id,
                "vehiculoId": request.vehiculo_id,
                "fechaInicio": self._to_storage(start),
                "fechaFin": self._to_storage(end),
                "precioTotal": total,
            }
            try:
                nueva_renta = RentalRepository.crear_renta(db, datos_renta)
            except ValueError as error:
                context.abort(grpc.StatusCode.ALREADY_EXISTS, str(error))
            except TimeoutError as error:
                context.abort(grpc.StatusCode.UNAVAILABLE, str(error))

            return rental_pb2.CrearRentaResponse(renta=self._to_proto(nueva_renta))
        finally:
            db.close()

    def ObtenerRenta(self, request, context):
        db = SessionLocal()
        try:
            renta = RentalRepository.obtener_renta(db, request.id)
            if not renta:
                context.abort(grpc.StatusCode.NOT_FOUND, "Renta no encontrada.")
            return rental_pb2.ObtenerRentaResponse(renta=self._to_proto(renta))
        finally:
            db.close()

    def ListarRentasPorCliente(self, request, context):
        db = SessionLocal()
        try:
            rentas = RentalRepository.listar_por_cliente(db, request.cliente_id)
            return rental_pb2.ListarRentasPorClienteResponse(rentas=[self._to_proto(r) for r in rentas])
        finally:
            db.close()

    def ObtenerHistorialRentas(self, request, context):
        db = SessionLocal()
        try:
            rentas = RentalRepository.obtener_historial(db, request.cliente_id)
            return rental_pb2.ObtenerHistorialRentasResponse(rentas=[self._to_proto(r) for r in rentas])
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

            return rental_pb2.CancelarRentaResponse(renta=self._to_proto(renta))
        finally:
            db.close()

    def VerificarSolapamiento(self, request, context):
        start, end = self._validated_period(request, context)
        db = SessionLocal()
        try:
            solapado = RentalRepository.verificar_solapamiento(
                db, request.vehiculo_id, self._to_storage(start), self._to_storage(end)
            )
            return rental_pb2.VerificarSolapamientoResponse(hay_solapamiento=solapado)
        finally:
            db.close()
