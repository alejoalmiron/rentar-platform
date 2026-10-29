from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import Session
from .db import Base

class VehiculoExternoModel(Base):
    __tablename__ = "vehiculos_externos"

    id = Column(Integer, primary_key=True, index=True)
    vehiculo_externo_id = Column(String(36), unique=True, index=True, nullable=False) 
    cliente_id = Column(String(36), nullable=False)
    marca = Column(String(50), nullable=False)
    modelo = Column(String(50), nullable=False)
    patente = Column(String(20), unique=True, nullable=False)
    anio = Column(Integer, nullable=True)
    color = Column(String(50), nullable=True)
    tipo = Column(String(20), nullable=True)
    estado = Column(String(20), nullable=False, default="PENDIENTE") 
    activo = Column(Boolean, nullable=False, default=True)
    patente_validada = Column(Boolean, nullable=False, default=False)
    titularidad_validada = Column(Boolean, nullable=False, default=False)

def get_all(db: Session):
    return db.query(VehiculoExternoModel).filter(VehiculoExternoModel.activo == True).all()

def get_by_id(db: Session, vehicle_id: int):
    return db.query(VehiculoExternoModel).filter(VehiculoExternoModel.id == vehicle_id, VehiculoExternoModel.activo == True).first()

def get_by_correlation_id(db: Session, vehiculo_externo_id):
    return db.query(VehiculoExternoModel).filter(VehiculoExternoModel.vehiculo_externo_id == vehiculo_externo_id, VehiculoExternoModel.activo == True).first()

def get_by_client_id(db: Session, cliente_id: str):
    return db.query(VehiculoExternoModel).filter(
        VehiculoExternoModel.cliente_id == cliente_id,
        VehiculoExternoModel.activo == True,
    ).order_by(VehiculoExternoModel.id.desc()).all()

def create(db: Session, vehicle_data: dict):
    new_vehicle = VehiculoExternoModel(**vehicle_data)
    db.add(new_vehicle)
    db.flush()
    if not new_vehicle.vehiculo_externo_id:
        new_vehicle.vehiculo_externo_id = str(new_vehicle.id)
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

def incorporate(db: Session, vehiculo_externo_id: str):
    vehicle = get_by_correlation_id(db, vehiculo_externo_id)
    if not vehicle:
        return None
    from .repository import VehicleModel
    incorporated = db.query(VehicleModel).filter(VehicleModel.patente == vehicle.patente).first()
    if not incorporated:
        incorporated = VehicleModel(
            marca=vehicle.marca,
            modelo=vehicle.modelo,
            patente=vehicle.patente,
            operativo=True,
            activo=True,
            anio=vehicle.anio,
            color=vehicle.color,
            tipo=vehicle.tipo,
            precio_diario=0,
            estado="DISPONIBLE",
        )
        db.add(incorporated)
    vehicle.estado = "DISPONIBLE"
    db.commit()
    db.refresh(incorporated)
    return incorporated

def update_estado_by_correlation(db: Session, vehiculo_externo_id: str, nuevo_estado: str):
    vehicle = get_by_correlation_id(db, vehiculo_externo_id)
    if vehicle:
        vehicle.estado = nuevo_estado
        db.commit()
        db.refresh(vehicle)
    return vehicle

def incorporate(db: Session, vehiculo_externo_id: str):
    vehicle = get_by_correlation_id(db, vehiculo_externo_id)
    if not vehicle:
        return None
    from .repository import VehicleModel
    incorporated = db.query(VehicleModel).filter(VehicleModel.patente == vehicle.patente).first()
    if incorporated:
        vehicle.estado = "DISPONIBLE"
        db.commit()
        return incorporated
    incorporated = VehicleModel(
        marca=vehicle.marca,
        modelo=vehicle.modelo,
        patente=vehicle.patente,
        operativo=True,
        activo=True,
        anio=vehicle.anio,
        color=vehicle.color,
        tipo=vehicle.tipo,
        precio_diario=0,
        estado="DISPONIBLE",
    )
    db.add(incorporated)
    vehicle.estado = "DISPONIBLE"
    db.commit()
    db.refresh(incorporated)
    return incorporated

def update_validacion(db: Session, vehiculo_externo_id: str, tipo: str, valida: bool):
    vehicle = get_by_correlation_id(db, vehiculo_externo_id)
    if vehicle:
        setattr(vehicle, tipo, valida)
        db.commit()
        db.refresh(vehicle)
    return vehicle

def delete(db: Session, vehicle_id: int):
    vehicle = get_by_id(db, vehicle_id)
    if vehicle:
        vehicle.activo = False 
        db.commit()
    return vehicle