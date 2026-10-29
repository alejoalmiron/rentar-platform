import grpc
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

from . import repository
from .db import SessionLocal
from .generated import vehicle_pb2, vehicle_pb2_grpc
from .messaging import event_bus, EVENTO_VERIFICACION_SOLICITADA

def handle_verificacion_resultado(payload):
    """Procesa el resultado asíncrono de la verificación de patente."""
    vehiculo_id = payload.get("vehiculoId")
    resultado = payload.get("resultado")
    
    if not vehiculo_id or not resultado:
        return

    print(f"Recibido resultado de verificación: Vehículo {vehiculo_id} -> {resultado}")
    db = SessionLocal()
    try:
        query = text("UPDATE vehiculos SET estado_verificacion = :resultado WHERE id = :id")
        result = db.execute(query, {"resultado": resultado, "id": vehiculo_id})
        db.commit()
        
        # Esto nos dirá si realmente encontró el vehículo en la tabla
        print(f"Vehículo {vehiculo_id} procesado. Filas modificadas en BD: {result.rowcount}")
        
    except Exception as e:
        db.rollback()
        print(f"ERROR AL ACTUALIZAR EN BD: {e}")
    finally:
        db.close()

class VehicleServiceServicer(vehicle_pb2_grpc.VehicleServiceServicer):

    def _to_proto(self, vehicle):
        return vehicle_pb2.Vehicle(
            id=vehicle.id,
            marca=vehicle.marca,
            modelo=vehicle.modelo,
            patente=vehicle.patente,
            operativo=vehicle.operativo,
            activo=vehicle.activo,
            anio=vehicle.anio or 0,
            color=vehicle.color or "",
            tipo=vehicle.tipo or "",
            precio_diario=vehicle.precio_diario or 0,
            estado=vehicle.estado,
        )

    def _vehicle_data(self, request):
        data = {
            "marca": request.marca.strip(),
            "modelo": request.modelo.strip(),
            "patente": request.patente.strip().upper(),
            "anio": request.anio,
            "color": request.color.strip() or None,
            "tipo": request.tipo,
            "precio_diario": request.precio_diario,
            "estado": request.estado or "DISPONIBLE",
        }
        if not data["marca"] or not data["modelo"] or not data["patente"]:
            return None
        if data["anio"] < 1886 or data["precio_diario"] < 0:
            return None
        if data["tipo"] not in {"SEDAN", "SUV", "PICKUP", "COUPE", "HATCHBACK"}:
            return None
        if data["estado"] not in {"DISPONIBLE", "RESERVADO", "EN_ALQUILER"}:
            return None
        return data
    
    def GetVehicles(self, request, context):
        db = SessionLocal()
        try:
            vehicles = repository.get_all(db)
        finally:
            db.close()
        return vehicle_pb2.VehicleList(
            vehicles=[self._to_proto(vehicle) for vehicle in vehicles]
        )

    def GetVehicleById(self, request, context):
        db = SessionLocal()
        try:
            v = repository.get_by_id(db, request.id)
        finally:
            db.close()
        if not v:
            context.abort(grpc.StatusCode.NOT_FOUND, "Vehículo no encontrado")
        return self._to_proto(v)

    def CreateVehicle(self, request, context):
        data = self._vehicle_data(request)
        if data is None:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Los datos del vehículo son inválidos")
        
        db = SessionLocal()
        vehiculo_id = None
        patente = None
        
        try:
            v = repository.create(db, data)
            # Guardamos los datos antes de cerrar la sesión para usarlos en el evento
            vehiculo_id = v.id
            patente = v.patente
        except IntegrityError:
            db.rollback()
            context.abort(grpc.StatusCode.ALREADY_EXISTS, "La patente ya está registrada")
        finally:
            db.close()
            
        # Generar evento asíncrono solicitando verificación
        if vehiculo_id and patente:
            try:
                event_bus.publish(
                    EVENTO_VERIFICACION_SOLICITADA,
                    {"vehiculoId": vehiculo_id, "patente": patente}
                )
            except Exception as e:
                print(f"Advertencia: Error publicando evento de verificación - {e}")
        return self._to_proto(v)

    def UpdateVehicle(self, request, context):
        data = self._vehicle_data(request)
        if data is None:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Los datos del vehículo son inválidos")
        data["operativo"] = request.operativo
        db = SessionLocal()
        try:
            v = repository.update(db, request.id, data)
        except IntegrityError:
            db.rollback()
            context.abort(grpc.StatusCode.ALREADY_EXISTS, "La patente ya está registrada")
        finally:
            db.close()
        if not v:
            context.abort(grpc.StatusCode.NOT_FOUND, "Vehículo no encontrado")
        return self._to_proto(v)

    def DeleteVehicle(self, request, context):
        db = SessionLocal()
        try:
            vehicle = repository.delete(db, request.id)
        finally:
            db.close()
        if not vehicle:
            context.abort(grpc.StatusCode.NOT_FOUND, "Vehículo no encontrado")
        return vehicle_pb2.Empty()

    def CheckOperative(self, request, context):
        db = SessionLocal()
        try:
            v = repository.get_by_id(db, request.id)
        finally:
            db.close()
        if not v:
            context.abort(grpc.StatusCode.NOT_FOUND, "Vehículo no encontrado")
        return vehicle_pb2.OperativeResponse(operativo=v.operativo)