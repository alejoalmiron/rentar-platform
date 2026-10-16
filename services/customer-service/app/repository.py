import uuid
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Boolean, ForeignKey, inspect, text
from .db import Base, engine

class CustomerModel(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True)
    dni = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(50), nullable=False)
    apellido = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    telefono = Column(String(30), nullable=True)
    activo = Column(Boolean, default=True)

class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    customer_id = Column(String(36), ForeignKey("customers.id"), unique=True, nullable=True)
    activo = Column(Boolean, default=True, nullable=False)

# Crea automáticamente las tablas si no existen
Base.metadata.create_all(bind=engine)
customer_columns = {column["name"] for column in inspect(engine).get_columns("customers")}
if "telefono" not in customer_columns:
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE customers ADD COLUMN telefono VARCHAR(30) NULL"))
unique_constraints = inspect(engine).get_unique_constraints("customers")
if not any(constraint["column_names"] == ["email"] for constraint in unique_constraints):
    with engine.begin() as connection:
        duplicate_email = connection.execute(text(
            "SELECT email FROM customers GROUP BY email HAVING COUNT(*) > 1 LIMIT 1"
        )).scalar()
        if duplicate_email:
            raise RuntimeError(
                "Customer DB contiene emails duplicados; corregilos antes de agregar la restricción unique"
            )
        connection.execute(text(
            "ALTER TABLE customers ADD CONSTRAINT uq_customers_email UNIQUE (email)"
        ))

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
    def get_by_email(db: Session, email: str):
        return db.query(CustomerModel).filter(CustomerModel.email == email).first()

    @staticmethod
    def get_user_by_username(db: Session, username: str):
        return db.query(UserModel).filter(UserModel.username == username).first()

    @staticmethod
    def save_user(db: Session, user: UserModel):
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

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