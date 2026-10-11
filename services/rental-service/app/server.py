from concurrent import futures
import time
import grpc
from sqlalchemy.exc import OperationalError
from app.db import engine, Base
from app.repository import RentalModel  # <--- ¡ESTO ES LO QUE FALTABA IMPORTAR!
from app.generated.rental.v1 import rental_pb2_grpc
from app.service import RentalServiceServicer

def serve():
    connected = False
    while not connected:
        try:
            Base.metadata.create_all(bind=engine)
            connected = True
            print("Conexión a la base de datos establecida exitosamente.")
        except OperationalError:
            print("Base de datos no disponible todavía. Reintentando en 3 segundos...")
            time.sleep(3)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    rental_pb2_grpc.add_RentalServiceServicer_to_server(RentalServiceServicer(), server)

    puerto = "[::]:50053"
    server.add_insecure_port(puerto)
    
    print(f"Rental Service gRPC corriendo y escuchando en el puerto {puerto}...")
    server.start()
    
    try:
        while True:
            time.sleep(86400) 
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    serve()