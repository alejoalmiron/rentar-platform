FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc default-libmysqlclient-dev build-essential pkg-config && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python -m grpc_tools.protoc -I proto --python_out=app/generated --grpc_python_out=app/generated proto/rental/v1/rental.proto

EXPOSE 50053

CMD ["python", "-m", "app.server"]