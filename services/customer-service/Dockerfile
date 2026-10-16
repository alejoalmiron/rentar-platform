FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python -m grpc_tools.protoc -I proto --python_out=. --grpc_python_out=. proto/customer/v1/customer.proto \
	&& python -m grpc_tools.protoc -I proto --python_out=app --grpc_python_out=app proto/customer/v1/customer.proto

EXPOSE 50052

CMD ["python", "-m", "app.server"]