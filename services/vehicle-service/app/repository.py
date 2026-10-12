from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import Session
from .db import Base

class VehicleModel(Base):
    __tablename__ = "vehiculos"

    id = Column(Integer, primary_key=True, index=True)
    marca = Column(String(50), nullable=False)
    modelo = Column(String(50), nullable=False)
    patente = Column(String(20), unique=True, nullable=False)
    operativo = Column(Boolean, default=True)
    activo = Column(Boolean, default=True) # Baja lógica del Hito 1

def get_all(db: Session):
    return db.query(VehicleModel).filter(VehicleModel.activo == True).all()

def get_by_id(db: Session, vehicle_id: int):
    return db.query(VehicleModel).filter(VehicleModel.id == vehicle_id, VehicleModel.activo == True).first()

def create(db: Session, marca: str, modelo: str, patente: str):
    new_vehicle = VehicleModel(marca=marca, modelo=modelo, patente=patente)
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)
    return new_vehicle

def update(db: Session, vehicle_id: int, marca: str, modelo: str, patente: str, operativo: bool):
    vehicle = get_by_id(db, vehicle_id)
    if vehicle:
        vehicle.marca = marca
        vehicle.modelo = modelo
        vehicle.patente = patente
        vehicle.operativo = operativo
        db.commit()
        db.refresh(vehicle)
    return vehicle

def delete(db: Session, vehicle_id: int):
    vehicle = get_by_id(db, vehicle_id)
    if vehicle:
        vehicle.activo = False # Se da de baja sin borrar el registro
        db.commit()
    return vehicle