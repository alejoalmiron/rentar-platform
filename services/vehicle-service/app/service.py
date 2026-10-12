import grpc
from sqlalchemy.exc import IntegrityError

from . import repository
from .db import SessionLocal
from .generated import vehicle_pb2, vehicle_pb2_grpc

class VehicleServiceServicer(vehicle_pb2_grpc.VehicleServiceServicer):
    
    def GetVehicles(self, request, context):
        db = SessionLocal()
        try:
            vehicles = repository.get_all(db)
        finally:
            db.close()
        return vehicle_pb2.VehicleList(
            vehicles=[vehicle_pb2.Vehicle(
                id=v.id, marca=v.marca, modelo=v.modelo,
                patente=v.patente, operativo=v.operativo, activo=v.activo
            ) for v in vehicles]
        )

    def GetVehicleById(self, request, context):
        db = SessionLocal()
        try:
            v = repository.get_by_id(db, request.id)
        finally:
            db.close()
        if not v:
            context.abort(grpc.StatusCode.NOT_FOUND, "Vehículo no encontrado")
        return vehicle_pb2.Vehicle(
            id=v.id, marca=v.marca, modelo=v.modelo,
            patente=v.patente, operativo=v.operativo, activo=v.activo
        )

    def CreateVehicle(self, request, context):
        db = SessionLocal()
        try:
            v = repository.create(db, request.marca, request.modelo, request.patente)
        except IntegrityError:
            db.rollback()
            context.abort(grpc.StatusCode.ALREADY_EXISTS, "La patente ya está registrada")
        finally:
            db.close()
        return vehicle_pb2.Vehicle(
            id=v.id, marca=v.marca, modelo=v.modelo,
            patente=v.patente, operativo=v.operativo, activo=v.activo
        )

    def UpdateVehicle(self, request, context):
        db = SessionLocal()
        try:
            v = repository.update(db, request.id, request.marca, request.modelo, request.patente, request.operativo)
        except IntegrityError:
            db.rollback()
            context.abort(grpc.StatusCode.ALREADY_EXISTS, "La patente ya está registrada")
        finally:
            db.close()
        if not v:
            context.abort(grpc.StatusCode.NOT_FOUND, "Vehículo no encontrado")
        return vehicle_pb2.Vehicle(
            id=v.id, marca=v.marca, modelo=v.modelo,
            patente=v.patente, operativo=v.operativo, activo=v.activo
        )

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