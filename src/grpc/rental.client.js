// Cliente de Rental Service: reservas, disponibilidad e historial.
import { callGrpc } from './clientFactory.js';
import { fromProtoEnum } from './enums.js';
import { normalizeDates, toTimestamp } from './timestamps.js';

function toProtoTimestamp(value) {
  const timestamp = toTimestamp(value);
  if (!timestamp) {
    const error = new Error('Las fechas de la reserva deben ser válidas');
    error.code = 3;
    throw error;
  }
  return timestamp;
}

function fromProtoRenta(renta) {
  return normalizeDates({ ...renta, estado: fromProtoEnum('ESTADO_RENTA', renta.estado) });
}

function filterByEstado(rentas, estado) {
  const reservations = (rentas || []).map(fromProtoRenta);
  return estado ? reservations.filter((reservation) => reservation.estado === estado) : reservations;
}

export const rentalClient = {
  async checkAvailability({ vehiculoId, fechaInicio, fechaFin }) {
    const response = await callGrpc('rental', 'VerificarSolapamiento', {
      vehiculoId: String(vehiculoId),
      fechaInicio: toProtoTimestamp(fechaInicio),
      fechaFin: toProtoTimestamp(fechaFin),
    });
    return { available: !response.haySolapamiento };
  },
  async create({ clienteId, vehiculoId, fechaInicio, fechaFin, precioDiario }) {
    const response = await callGrpc('rental', 'CrearRenta', {
      clienteId: String(clienteId),
      vehiculoId: String(vehiculoId),
      fechaInicio: toProtoTimestamp(fechaInicio),
      fechaFin: toProtoTimestamp(fechaFin),
      precioDiario: Number(precioDiario),
    });
    return fromProtoRenta(response.renta);
  },
  async getById(id) {
    return fromProtoRenta((await callGrpc('rental', 'ObtenerRenta', { id: String(id) })).renta);
  },
  async list({ clienteId, estado } = {}) {
    const response = await callGrpc('rental', 'ListarRentasPorCliente', {
      clienteId: String(clienteId),
    });
    return filterByEstado(response.rentas, estado);
  },
  async cancel(id) {
    return fromProtoRenta((await callGrpc('rental', 'CancelarRenta', { id: String(id) })).renta);
  },
  async history({ clienteId, estado } = {}) {
    const response = await callGrpc('rental', 'ObtenerHistorialRentas', {
      ...(clienteId !== undefined && { clienteId: String(clienteId) }),
    });
    return filterByEstado(response.rentas, estado);
  },
};
