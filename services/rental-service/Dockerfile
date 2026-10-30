FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc default-libmysqlclient-dev build-essential pkg-config && rm -rf /var/lib/apt/lists/*

COPY services/rental-service/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/rental-service/ /app/
COPY services/vehicle-service/proto/vehicle/v1/vehicle.proto /tmp/vehicle.proto
RUN python -m grpc_tools.protoc -I /app/proto --python_out=/app/app/generated --grpc_python_out=/app/app/generated /app/proto/rental/v1/rental.proto \
    && python -m grpc_tools.protoc -I /tmp --python_out=/app/app/generated --grpc_python_out=/app/app/generated /tmp/vehicle.proto

EXPOSE 50053

CMD ["python", "-m", "app.server"]