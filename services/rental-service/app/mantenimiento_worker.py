import os
import json
import time
import uuid
import pika
from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker, declarative_base
from app.repository import RentalRepository

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@rental-db:3306/rental_db")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class MantenimientoLogModel(Base):
    __tablename__ = "mantenimiento_logs"
    id = Column(String(36), primary_key=True)
    renta_id = Column(String(36), nullable=False)
    vehiculo_id = Column(String(36), nullable=False)
    resultado = Column(String(30), nullable=False)

Base.metadata.create_all(bind=engine)

def callback(ch, method, properties, body):
    data = json.loads(body)
    renta_id = data.get("renta_id")
    vehiculo_id = data.get("vehiculo_id")
    print(f" [x] Procesando mantenimiento preventivo para Renta: {renta_id}, Vehículo: {vehiculo_id}")

    # Simular procesamiento asíncrono
    time.sleep(3)
    resultado_mantenimiento = "REALIZADO"

    db = SessionLocal()
    try:
        log_entry = MantenimientoLogModel(
            id=str(uuid.uuid4()),
            renta_id=renta_id,
            vehiculo_id=vehiculo_id,
            resultado=resultado_mantenimiento
        )
        db.add(log_entry)
        db.commit()

        RentalRepository.actualizar_mantenimiento(db, renta_id, resultado_mantenimiento)
        print(f" [✔] Mantenimiento {resultado_mantenimiento} guardado para la renta {renta_id}")
    except Exception as e:
        db.rollback()
        print(f" [!] Error en worker de mantenimiento: {e}")
    finally:
        db.close()

    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    params = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue='reserva.confirmada', durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='reserva.confirmada', on_message_callback=callback)
    print(' [*] Worker de Mantenimiento Preventivo esperando eventos...')
    channel.start_consuming()

if __name__ == '__main__':
    main()