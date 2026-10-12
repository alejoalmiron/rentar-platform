import grpc
from concurrent import futures
from dotenv import load_dotenv
import os

load_dotenv()

from app.db import Base, engine
from app.generated import vehicle_pb2_grpc
from app.service import VehicleServiceServicer

def serve():
    Base.metadata.create_all(bind=engine)
    port = os.getenv("PORT", "50051")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    vehicle_pb2_grpc.add_VehicleServiceServicer_to_server(VehicleServiceServicer(), server)
    
    if server.add_insecure_port(f'[::]:{port}') == 0:
        raise RuntimeError(f"No se pudo abrir el puerto gRPC {port}")
    print(f"Iniciando Vehicle Service en el puerto {port}...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()