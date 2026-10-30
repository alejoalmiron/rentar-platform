"""Worker de mantenimiento preventivo (Hito 3).

Consume reserva.confirmada, registra la solicitud en su propia tabla, simula el
procesamiento y publica mantenimiento.resultado. Rental Service es quien asocia
el resultado a la reserva, por lo que este componente no toca la tabla rentals.
"""

import os
import threading
import time
import uuid
from datetime import datetime, timedelta

from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.messaging import (
    COLA_RESERVAS_CONFIRMADAS,
    EVENTO_MANTENIMIENTO_RESULTADO,
    EVENTO_RESERVA_CONFIRMADA,
    EventBus,
    publicar,
)

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@rental-db:3306/rental_db")
SEGUNDOS_PROCESAMIENTO = int(os.getenv("MANTENIMIENTO_SEGUNDOS", "3"))
# El taller simulado necesita un dia de margen antes de entregar el vehiculo.
ANTICIPACION_MINIMA = timedelta(hours=24)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class SolicitudMantenimientoModel(Base):
    __tablename__ = "mantenimiento_solicitudes"

    id = Column(String(36), primary_key=True)
    reserva_id = Column(String(36), nullable=False)
    vehiculo_id = Column(String(36), nullable=False)
    fecha_inicio = Column(String(50), nullable=False)
    fecha_fin = Column(String(50), nullable=False)
    estado = Column(String(30), nullable=False, default="SOLICITADO")


def determinar_resultado(fecha_inicio):
    margen = datetime.fromisoformat(fecha_inicio) - datetime.utcnow()
    return "REALIZADO" if margen >= ANTICIPACION_MINIMA else "NO_REALIZADO"


def procesar_reserva_confirmada(evento):
    reserva_id = evento["reservaId"]
    vehiculo_id = evento["vehiculoId"]
    print(f"Procesando mantenimiento preventivo: reserva {reserva_id}, vehículo {vehiculo_id}")

    db = SessionLocal()
    try:
        solicitud = SolicitudMantenimientoModel(
            id=str(uuid.uuid4()),
            reserva_id=reserva_id,
            vehiculo_id=str(vehiculo_id),
            fecha_inicio=evento["fechaInicio"],
            fecha_fin=evento["fechaFin"],
            estado="SOLICITADO",
        )
        db.add(solicitud)
        db.commit()

        time.sleep(SEGUNDOS_PROCESAMIENTO)
        resultado = determinar_resultado(evento["fechaInicio"])

        solicitud.estado = resultado
        db.commit()
    finally:
        db.close()

    publicar(EVENTO_MANTENIMIENTO_RESULTADO, {
        "reservaId": reserva_id,
        "vehiculoId": vehiculo_id,
        "resultado": resultado,
    })


def main():
    Base.metadata.create_all(bind=engine)
    EventBus().start_consumer(
        COLA_RESERVAS_CONFIRMADAS,
        EVENTO_RESERVA_CONFIRMADA,
        procesar_reserva_confirmada,
    )
    print("Worker de mantenimiento esperando eventos reserva.confirmada...")
    threading.Event().wait()


if __name__ == "__main__":
    main()
