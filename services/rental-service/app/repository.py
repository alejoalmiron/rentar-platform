from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Float
from app.db import Base
import uuid

class RentalModel(Base):
    __tablename__ = "rentals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cliente_id = Column("clienteId", String(36), nullable=False)
    vehiculo_id = Column("vehiculoId", String(36), nullable=False)
    fecha_inicio = Column("fechaInicio", String(50), nullable=False)
    fecha_fin = Column("fechaFin", String(50), nullable=False)
    estado = Column("estado", String(20), default="CONFIRMADA")
    precio_total = Column("precioTotal", Float, nullable=False)

class RentalRepository:
    @staticmethod
    def verificar_solapamiento(db: Session, vehiculo_id: str, fecha_inicio: str, fecha_fin: str) -> bool:
        existing = db.query(RentalModel).filter(
            RentalModel.vehiculo_id == vehiculo_id,
            RentalModel.estado == "CONFIRMADA",
            RentalModel.fecha_inicio < fecha_fin,
            RentalModel.fecha_fin > fecha_inicio
        ).first()
        return existing is not None

    @staticmethod
    def crear_renta(db: Session, datos_renta: dict) -> RentalModel:
        renta = RentalModel(
            id=str(uuid.uuid4()),
            cliente_id=datos_renta["clienteId"],
            vehiculo_id=datos_renta["vehiculoId"],
            fecha_inicio=datos_renta["fechaInicio"],
            fecha_fin=datos_renta["fechaFin"],
            precio_total=datos_renta["precioTotal"],
            estado="CONFIRMADA"
        )
        db.add(renta)
        db.commit()
        db.refresh(renta)
        return renta

    @staticmethod
    def obtener_renta(db: Session, renta_id: str) -> RentalModel:
        return db.query(RentalModel).filter(RentalModel.id == renta_id).first()

    @staticmethod
    def listar_por_cliente(db: Session, cliente_id: str):
        return db.query(RentalModel).filter(RentalModel.cliente_id == cliente_id).all()

    @staticmethod
    def cancelar_renta(db: Session, renta_id: str) -> RentalModel:
        renta = db.query(RentalModel).filter(RentalModel.id == renta_id).first()
        if renta:
            renta.estado = "CANCELADA"
            db.commit()
            db.refresh(renta)
        return renta