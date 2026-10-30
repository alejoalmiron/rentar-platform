// Conexión con los microservicios: todos los clientes gRPC pasan por callGrpc.
import path from 'node:path';
import grpc from '@grpc/grpc-js';
import protoLoader from '@grpc/proto-loader';
import { grpcConfig } from '../config/grpc.js';

const clients = new Map();

function getNestedValue(root, dottedPath) {
  return dottedPath.split('.').reduce((value, key) => value?.[key], root);
}

// Crea la conexión a cada servicio una sola vez y después la reutiliza.
function getClient(serviceKey) {
  if (clients.has(serviceKey)) return clients.get(serviceKey);

  const serviceConfig = grpcConfig.services[serviceKey];
  if (!serviceConfig) throw new Error(`Servicio gRPC desconocido: ${serviceKey}`);

  const protoPath = path.join(serviceConfig.protoRoot || grpcConfig.protoRoot, serviceConfig.file);
  let packageDefinition;
  try {
    packageDefinition = protoLoader.loadSync(protoPath, {
      longs: String,
      enums: String,
      defaults: true,
      oneofs: true,
    });
  } catch (cause) {
    const error = new Error(`No se pudo cargar el contrato gRPC ${protoPath}`, { cause });
    error.code = grpc.status.UNAVAILABLE;
    throw error;
  }

  const loadedPackage = grpc.loadPackageDefinition(packageDefinition);
  const Service = getNestedValue(loadedPackage, serviceConfig.packageName)?.[serviceConfig.serviceName];
  if (!Service) {
    const error = new Error(`No se encontró ${serviceConfig.packageName}.${serviceConfig.serviceName} en ${protoPath}`);
    error.code = grpc.status.UNAVAILABLE;
    throw error;
  }

  const client = new Service(serviceConfig.address, grpc.credentials.createInsecure());
  clients.set(serviceKey, client);
  return client;
}

// Convierte la llamada gRPC en una Promise y le aplica el plazo máximo de respuesta.
export function callGrpc(serviceKey, method, request = {}) {
  return new Promise((resolve, reject) => {
    let client;
    try {
      client = getClient(serviceKey);
    } catch (error) {
      reject(error);
      return;
    }

    const clientMethod = method[0].toLowerCase() + method.slice(1);
    const rpcMethod = client[clientMethod];
    if (typeof rpcMethod !== 'function') {
      const error = new Error(`El método ${method} no está definido en ${serviceKey}`);
      error.code = grpc.status.UNIMPLEMENTED;
      reject(error);
      return;
    }

    rpcMethod.call(
      client,
      request,
      { deadline: new Date(Date.now() + grpcConfig.timeoutMs) },
      (error, response) => (error ? reject(error) : resolve(response)),
    );
  });
}

export function closeGrpcClients() {
  for (const client of clients.values()) client.close();
  clients.clear();
}