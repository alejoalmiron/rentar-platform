import 'dotenv/config';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');

export const grpcConfig = {
  protoRoot: path.resolve(projectRoot, process.env.GRPC_PROTO_ROOT || 'proto'),
  timeoutMs: Number(process.env.GRPC_TIMEOUT_MS || 5000),
  services: {
    vehicle: {
      address: process.env.VEHICLE_GRPC_ADDRESS || 'localhost:50051',
      protoRoot: path.resolve(projectRoot, 'services/vehicle-service/proto'),
      file: 'vehicle/v1/vehicle.proto',
      packageName: 'vehicle.v1',
      serviceName: 'VehicleService',
    },
    customer: {
      address: process.env.CUSTOMER_GRPC_ADDRESS || 'localhost:50052',
      file: 'customer/v1/customer.proto',
      packageName: 'rentar.customer.v1',
      serviceName: 'CustomerService',
    },
    rental: {
      address: process.env.RENTAL_GRPC_ADDRESS || 'localhost:50053',
      file: 'rental/v1/rental.proto',
      packageName: 'rentar.rental.v1',
      serviceName: 'RentalService',
    },
  },
};