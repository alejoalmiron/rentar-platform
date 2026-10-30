import { customerClient } from '../grpc/customer.client.js';
import { respondWithRpc } from './rpcResponse.js';

export const getClientes = async (req, res) => {
  // El rol CLIENTE solo ve sus propios datos.
  if (req.auth.role === 'CLIENTE') {
    return respondWithRpc(
      res,
      () => customerClient.getById(req.auth.customerId),
      (cliente) => [withDni(cliente)],
    );
  }
  return respondWithRpc(res, customerClient.list, (clientes) => clientes.map(withDni));
};

export const getClienteById = async (req, res) => {
  return respondWithRpc(res, () => customerClient.getById(req.params.id), withDni);
};

export const createCliente = async (req, res) => {
  return respondWithRpc(res, () => customerClient.create(req.body || {}), withDni, 201);
};

export const updateCliente = async (req, res) => {
  return respondWithRpc(res, () => customerClient.update(req.params.id, req.body || {}), withDni);
};

export const deleteCliente = async (req, res) => {
  return respondWithRpc(
    res,
    () => customerClient.deactivate(req.params.id),
    (cliente) => ({ mensaje: 'Cliente dado de baja correctamente', cliente: withDni(cliente) }),
  );
};

function withDni(cliente) {
  return { ...cliente, dni: cliente.dni || cliente.documento };
}