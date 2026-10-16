import os
import uuid

import bcrypt

from app.db import Base, SessionLocal, engine
from app.repository import CustomerModel, UserModel


def seed_users():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin_username = os.getenv("SEED_ADMIN_USERNAME", "admin").strip().lower()
        admin_password = os.getenv("SEED_ADMIN_PASSWORD", "AdminRentar2026!")
        client_username = os.getenv("SEED_CLIENT_USERNAME", "cliente").strip().lower()
        client_password = os.getenv("SEED_CLIENT_PASSWORD", "ClienteRentar2026!")
        client_dni = os.getenv("SEED_CLIENT_DNI", "40999000")

        demo_customer = db.query(CustomerModel).filter(CustomerModel.dni == client_dni).first()
        if not demo_customer:
            demo_customer = CustomerModel(
                id=str(uuid.uuid4()),
                dni=client_dni,
                nombre="Cliente",
                apellido="Demo",
                email="cliente.demo@rentar.local",
                telefono=None,
                activo=True,
            )
            db.add(demo_customer)
            db.flush()

        seed_accounts = (
            (admin_username, admin_password, "ADMIN", None),
            (client_username, client_password, "CLIENTE", demo_customer.id),
        )
        for username, password, role, customer_id in seed_accounts:
            account = db.query(UserModel).filter(UserModel.username == username).first()
            if account:
                continue
            password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            db.add(UserModel(
                id=str(uuid.uuid4()),
                username=username,
                password_hash=password_hash,
                role=role,
                customer_id=customer_id,
                activo=True,
            ))
        db.commit()
        print("Usuarios de desarrollo verificados en Customer Service")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_users()