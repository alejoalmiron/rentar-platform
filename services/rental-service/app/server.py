import sys
import os
import time
from concurrent import futures
import grpc
from sqlalchemy.exc import OperationalError

currentdir = os.path.dirname(os.path.abspath(__file__))
parentdir = os.path.dirname(currentdir)
if parentdir not in sys.path:
    sys.path.insert(0, parentdir)

from app.db import engine, Base, SessionLocal
from app.repository import RentalModel
from app.generated.rental.v1 import rental_pb2_grpc
from app.service import RentalServiceServicer
from app.messaging import EventBus, COLA_MANTENIMIENTO_RESULTADOS as COLAMANTENIMIENTO, EVENTO_MANTENIMIENTO_RESULTADO as EVENTOMANTENIMIENTO

def serve():
    conexionestablecida = False
    while not conexionestablecida:
        try:
            Base.metadata.create_all(bind=engine)
            conexionestablecida = True
            print("Conexion a la base de datos establecida exitosamente.")
        except OperationalError:
            print("Base de datos no disponible todavia. Reintentando en 3 segundos...")
            time.sleep(3)

    # Iniciar el consumidor usando messaging.py (Punto 3 resuelto asíncronamente)
    try:
        def alrecibirresultado(payload):
            idreserva = payload.get("id_reserva") or payload.get("reservaId")
            resultadomantenimiento = payload.get("resultado")
            print(f"Recibiendo resultado de mantenimiento para reserva {idreserva}: {resultadomantenimiento}")
            sesiondb = SessionLocal()
            try:
                reservaencontrada = sesiondb.query(RentalModel).filter(RentalModel.id == idreserva).first()
                if reservaencontrada:
                    reservaencontrada.resultadomantenimiento = resultadomantenimiento
                    sesiondb.commit()
                    print(f"Reserva {idreserva} actualizada con mantenimiento: {resultadomantenimiento}")
            except Exception as ex:
                sesiondb.rollback()
                print(f"Error al actualizar la base de datos: {ex}")
            finally:
                sesiondb.close()

        busdeventos = EventBus()
        busdeventos.start_consumer(
            queue_name=COLAMANTENIMIENTO,
            routing_key=EVENTOMANTENIMIENTO,
            on_event=alrecibirresultado
        )
        print("Consumidor de RabbitMQ iniciado correctamente mediante messaging.py.")
    except Exception as err:
        print(f"Aviso: No se pudo iniciar el consumidor de RabbitMQ: {err}")

    servidorgrpc = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rental_pb2_grpc.add_RentalServiceServicer_to_server(RentalServiceServicer(), servidorgrpc)
    puertoescucha = "[::]:50053"
    servidorgrpc.add_insecure_port(puertoescucha)
    print(f"Rental Service gRPC corriendo y escuchando en el puerto {puertoescucha}...")
    servidorgrpc.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        servidorgrpc.stop(0)

if __name__ == "__main__":
    serve()