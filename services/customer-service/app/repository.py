import uuid
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Boolean
from .db import Base, engine

class CustomerModel(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True)
    dni = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(50), nullable=False)
    apellido = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)
    activo = Column(Boolean, default=True)

# Crea automáticamente las tablas si no existen
Base.metadata.create_all(bind=engine)

class CustomerRepository:
    @staticmethod
    def get_all(db: Session):
        return db.query(CustomerModel).all()

    @staticmethod
    def get_by_id(db: Session, customer_id: str):
        return db.query(CustomerModel).filter(CustomerModel.id == customer_id).first()

    @staticmethod
    def get_by_dni(db: Session, dni: str):
        return db.query(CustomerModel).filter(CustomerModel.dni == dni).first()

    @staticmethod
    def save(db: Session, customer: CustomerModel):
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def update(db: Session, customer: CustomerModel):
        db.commit()
        db.refresh(customer)
        return customer