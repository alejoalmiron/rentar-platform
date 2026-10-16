import { rentalClient } from '../grpc/rental.client.js';
import { createReservation } from '../orchestrators/reserva.orchestrator.js';
import { respondWithRpc } from './rpcResponse.js';

export const crearReserva = async (req, res) => {
  const reservationInput = { ...(req.body || {}) };
  if (req.auth.role === 'CLIENTE') {
    reservationInput.clienteId = req.auth.customerId;
    delete reservationInput.clienteDni;
  }
  return respondWithRpc(res, () => createReservation(reservationInput), undefined, 201);
};

export const cancelarReserva = async (req, res) => {
  return respondWithRpc(
    res,
    async () => {
      const reserva = await rentalClient.getById(req.params.id);
      if (req.auth.role === 'CLIENTE' && reserva.clienteId !== req.auth.customerId) {
        const error = new Error('Solo podés cancelar tus propias reservas');
        error.code = 7;
        throw error;
      }
      return rentalClient.cancel(req.params.id);
    },
    (reserva) => ({ mensaje: 'Reserva cancelada correctamente', reserva }),
  );
};