from sqlalchemy import Column, Integer, String, Boolean, Float
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
    anio = Column(Integer, nullable=True)
    color = Column(String(50), nullable=True)
    tipo = Column(String(20), nullable=True)
    precio_diario = Column(Float, nullable=True)
    estado = Column(String(20), nullable=False, default="DISPONIBLE")

def get_all(db: Session):
    return db.query(VehicleModel).filter(VehicleModel.activo == True).all()

def get_by_id(db: Session, vehicle_id: int):
    return db.query(VehicleModel).filter(VehicleModel.id == vehicle_id, VehicleModel.activo == True).first()

def create(db: Session, vehicle_data: dict):
    new_vehicle = VehicleModel(**vehicle_data)
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)
    return new_vehicle

def update(db: Session, vehicle_id: int, vehicle_data: dict):
    vehicle = get_by_id(db, vehicle_id)
    if vehicle:
        for field, value in vehicle_data.items():
            setattr(vehicle, field, value)
        db.commit()
        db.refresh(vehicle)
    return vehicle

def delete(db: Session, vehicle_id: int):
    vehicle = get_by_id(db, vehicle_id)
    if vehicle:
        vehicle.activo = False # Se da de baja sin borrar el registro
        db.commit()
    return vehicle