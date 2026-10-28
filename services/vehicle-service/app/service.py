import grpc
from sqlalchemy.exc import IntegrityError

from .db import SessionLocal
from .generated import vehicle_pb2, vehicle_pb2_grpc
from . import external_repository, repository

TIPOS_VALIDOS = {"SEDAN", "SUV", "PICKUP", "COUPE", "HATCHBACK"}
ESTADOS_VALIDOS = {"DISPONIBLE", "RESERVADO", "EN_ALQUILER"}


def _enum_a_texto(enum_type, prefijo, valor):
    """Convierte un valor de enum proto (TIPO_VEHICULO_SEDAN) al texto de dominio (SEDAN)."""
    return enum_type.Name(valor).removeprefix(prefijo)


def _texto_a_enum(enum_type, prefijo, texto):
    """Convierte el texto de dominio guardado en la base al valor de enum proto."""
    try:
        return enum_type.Value(f"{prefijo}{texto}")
    except ValueError:
        return 0


class VehicleServiceServicer(vehicle_pb2_grpc.VehicleServiceServicer):

    def _to_proto(self, vehicle):
        return vehicle_pb2.Vehiculo(
            id=vehicle.id,
            marca=vehicle.marca,
            modelo=vehicle.modelo,
            patente=vehicle.patente,
            operativo=vehicle.operativo,
            activo=vehicle.activo,
            anio=vehicle.anio or 0,
            color=vehicle.color or "",
            tipo=_texto_a_enum(vehicle_pb2.TipoVehiculo, "TIPO_VEHICULO_", vehicle.tipo or ""),
            precio_diario=vehicle.precio_diario or 0,
            estado=_texto_a_enum(vehicle_pb2.EstadoVehiculo, "ESTADO_VEHICULO_", vehicle.estado),
        )

    def _vehicle_data(self, request, estado):
        data = {
            "marca": request.marca.strip(),
            "modelo": request.modelo.strip(),
            "anio": request.anio,
            "color": request.color.strip() or None,
            "tipo": _enum_a_texto(vehicle_pb2.TipoVehiculo, "TIPO_VEHICULO_", request.tipo),
            "precio_diario": request.precio_diario,
            "estado": estado,
        }
        if not data["marca"] or not data["modelo"]:
            return None
        if data["anio"] < 1886 or data["precio_diario"] < 0:
            return None
        if data["tipo"] not in TIPOS_VALIDOS:
            return None
        if data["estado"] not in ESTADOS_VALIDOS:
            return None
        return data

    def ListarVehiculos(self, request, context):
        db = SessionLocal()
        try:
            vehicles = repository.get_all(db)
        finally:
            db.close()
        return vehicle_pb2.ListarVehiculosResponse(
            vehiculos=[self._to_proto(vehicle) for vehicle in vehicles]
        )

    def ObtenerVehiculo(self, request, context):
        db = SessionLocal()
        try:
            v = repository.get_by_id(db, request.id)
        finally:
            db.close()
        if not v:
            context.abort(grpc.StatusCode.NOT_FOUND, "Vehículo no encontrado")
        return vehicle_pb2.ObtenerVehiculoResponse(vehiculo=self._to_proto(v))

    def CrearVehiculo(self, request, context):
        # Todo vehículo nuevo comienza DISPONIBLE (regla del Hito 1).
        data = self._vehicle_data(request, "DISPONIBLE")
        patente = request.patente.strip().upper()
        if data is None or not patente:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Los datos del vehículo son inválidos")
        data["patente"] = patente
        db = SessionLocal()
        try:
            v = repository.create(db, data)
        except IntegrityError:
            db.rollback()
            context.abort(grpc.StatusCode.ALREADY_EXISTS, "La patente ya está registrada")
        finally:
            db.close()
        return vehicle_pb2.CrearVehiculoResponse(vehiculo=self._to_proto(v))

    def ActualizarVehiculo(self, request, context):
        estado = _enum_a_texto(vehicle_pb2.EstadoVehiculo, "ESTADO_VEHICULO_", request.estado)
        data = self._vehicle_data(request, estado)
        if data is None:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Los datos del vehículo son inválidos")
        data["operativo"] = request.operativo
        db = SessionLocal()
        try:
            v = repository.update(db, request.id, data)
        finally:
            db.close()
        if not v:
            context.abort(grpc.StatusCode.NOT_FOUND, "Vehículo no encontrado")
        return vehicle_pb2.ActualizarVehiculoResponse(vehiculo=self._to_proto(v))

    def DarDeBajaVehiculo(self, request, context):
        db = SessionLocal()
        try:
            vehicle = repository.delete(db, request.id)
        finally:
            db.close()
        if not vehicle:
            context.abort(grpc.StatusCode.NOT_FOUND, "Vehículo no encontrado")
        return vehicle_pb2.DarDeBajaVehiculoResponse(vehiculo=self._to_proto(vehicle))

    def VerificarOperatividad(self, request, context):
        db = SessionLocal()
        try:
            v = repository.get_by_id(db, request.id)
        finally:
            db.close()
        if not v:
            context.abort(grpc.StatusCode.NOT_FOUND, "Vehículo no encontrado")
        return vehicle_pb2.VerificarOperatividadResponse(operativo=v.operativo)
    
    def _to_proto_externo(self, vehicle):
        return vehicle_pb2.VehiculoExterno(
            id=vehicle.id,
            vehiculo_externo_id=vehicle.vehiculo_externo_id,
            cliente_id=vehicle.cliente_id,
            marca=vehicle.marca,
            modelo=vehicle.modelo,
            patente=vehicle.patente,
            anio=vehicle.anio or 0,
            color=vehicle.color or "",
            tipo=_texto_a_enum(vehicle_pb2.TipoVehiculo, "TIPO_VEHICULO_", vehicle.tipo or ""),
            estado=_texto_a_enum(vehicle_pb2.EstadoIncorporacion, "ESTADO_INCORPORACION_", vehicle.estado),
        )

    def CrearVehiculoExterno(self, request, context):
        data = {
            "vehiculo_externo_id": request.vehiculo_externo_id.strip(),
            "cliente_id": request.cliente_id.strip(),
            "marca": request.marca.strip(),
            "modelo": request.modelo.strip(),
            "patente": request.patente.strip().upper(),
            "anio": request.anio if request.anio > 0 else None,
            "color": request.color.strip() or None,
            "tipo": _enum_a_texto(vehicle_pb2.TipoVehiculo, "TIPO_VEHICULO_", request.tipo),
            "estado": "PENDIENTE",
        }

        if (not data["cliente_id"] or data["tipo"] not in TIPOS_VALIDOS
                or not data["marca"] or not data["modelo"] or not data["patente"]):
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Los datos obligatorios del vehículo externo son inválidos")

        db = SessionLocal()
        try:
            v = external_repository.create(db, data)
        except IntegrityError:
            db.rollback()
            context.abort(grpc.StatusCode.ALREADY_EXISTS, "La patente o el ID externo ya están registrados")
        finally:
            db.close()

        from .messaging import EVENTO_EXTERNO_REGISTRADO, EventBus
        EventBus().publish(EVENTO_EXTERNO_REGISTRADO, {
            "vehiculoExternoId": v.id,
            "clienteId": v.cliente_id,
            "patente": v.patente,
        })
        return vehicle_pb2.CrearVehiculoExternoResponse(vehiculo=self._to_proto_externo(v))

    def ListarVehiculosExternos(self, request, context):
        cliente_id = request.cliente_id.strip()
        if not cliente_id:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "El cliente es obligatorio")
        db = SessionLocal()
        try:
            vehicles = external_repository.get_by_client_id(db, cliente_id)
        finally:
            db.close()
        return vehicle_pb2.ListarVehiculosExternosResponse(
            vehiculos=[self._to_proto_externo(vehicle) for vehicle in vehicles],
        )
