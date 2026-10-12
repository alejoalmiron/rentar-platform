import uuid
from .repository import CustomerRepository, CustomerModel
from .db import SessionLocal

class CustomerServiceLogic:
    @staticmethod
    def list_customers():
        db = SessionLocal()
        try:
            return CustomerRepository.get_all(db)
        finally:
            db.close()

    @staticmethod
    def get_customer_by_id(customer_id: str):
        db = SessionLocal()
        try:
            return CustomerRepository.get_by_id(db, customer_id)
        finally:
            db.close()

    @staticmethod
    def create_customer(data):
        db = SessionLocal()
        try:
            if not data.dni or not data.nombre or not data.apellido or not data.email:
                raise ValueError("Todos los campos obligatorios (dni, nombre, apellido, email) deben estar completos")

            existing = CustomerRepository.get_by_dni(db, data.dni)
            if existing:
                raise ValueError("Ya existe un cliente registrado con ese DNI")

            new_customer = CustomerModel(
                id=str(uuid.uuid4()),
                dni=data.dni,
                nombre=data.nombre,
                apellido=data.apellido,
                email=data.email,
                activo=True
            )
            return CustomerRepository.save(db, new_customer)
        finally:
            db.close()

    @staticmethod
    def update_customer(customer_id, data):
        db = SessionLocal()
        try:
            customer = CustomerRepository.get_by_id(db, customer_id)
            if not customer:
                raise ValueError("Cliente no encontrado")

            customer.nombre = data.nombre or customer.nombre
            customer.apellido = data.apellido or customer.apellido
            customer.email = data.email or customer.email
            
            return CustomerRepository.update(db, customer)
        finally:
            db.close()

    @staticmethod
    def deactivate_customer(customer_id: str):
        db = SessionLocal()
        try:
            customer = CustomerRepository.get_by_id(db, customer_id)
            if not customer:
                raise ValueError("Cliente no encontrado")
            
            customer.activo = False
            return CustomerRepository.update(db, customer)
        finally:
            db.close()

    @staticmethod
    def validate_customer_active(customer_id: str):
        db = SessionLocal()
        try:
            customer = CustomerRepository.get_by_id(db, customer_id)
            if not customer:
                return {"exists": False, "is_active": False, "message": "Cliente no encontrado"}
            if not customer.activo:
                return {"exists": True, "is_active": False, "message": "El cliente se encuentra dado de baja"}
            return {"exists": True, "is_active": True, "message": "Cliente activo y habilitado"}
        finally:
            db.close()