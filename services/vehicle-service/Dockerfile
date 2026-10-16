FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para conectores MySQL
RUN apt-get update && apt-get install -y gcc default-libmysqlclient-dev pkg-config && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python -m grpc_tools.protoc -I proto/vehicle/v1 --python_out=app/generated --grpc_python_out=app/generated proto/vehicle/v1/vehicle.proto

ENV PYTHONPATH=/app/app/generated

EXPOSE 50051

CMD ["python", "-m", "app.server"]