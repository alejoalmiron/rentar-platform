import { callGrpc } from './clientFactory.js';
import { normalizeDates } from './timestamps.js';

const unwrap = (response, key) => normalizeDates(response?.[key] ?? response);

function toIsoDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    const error = new Error('Las fechas de la reserva deben ser válidas');
    error.code = 3;
    throw error;
  }
  return date.toISOString();
}

export const rentalClient = {
  async checkAvailability({ vehiculoId, fechaInicio, fechaFin }) {
    const response = await callGrpc('rental', 'VerificarSolapamiento', {
      vehiculoId: String(vehiculoId),
      fechaInicio: toIsoDate(fechaInicio),
      fechaFin: toIsoDate(fechaFin),
    });
    return { available: !response.haySolapamiento };
  },
  async create({ clienteId, vehiculoId, fechaInicio, fechaFin, precioDiario }) {
    const response = await callGrpc('rental', 'CrearRenta', {
      clienteId: String(clienteId),
      vehiculoId: String(vehiculoId),
      fechaInicio: toIsoDate(fechaInicio),
      fechaFin: toIsoDate(fechaFin),
      precioDiario: Number(precioDiario),
    });
    return unwrap(response, 'renta');
  },
  async getById(id) {
    return unwrap(await callGrpc('rental', 'ObtenerRenta', { id: String(id) }), 'renta');
  },
  async list({ clienteId, estado } = {}) {
    const response = await callGrpc('rental', 'ListarRentasPorCliente', {
      clienteId: String(clienteId),
    });
    const reservations = normalizeDates(response.rentas || []);
    return estado ? reservations.filter((reservation) => reservation.estado === estado) : reservations;
  },
  async cancel(id) {
    return unwrap(await callGrpc('rental', 'CancelarRenta', { id: String(id) }), 'renta');
  },
  async history({ clienteId, estado } = {}) {
    const response = await callGrpc('rental', 'ObtenerHistorialRentas', {
      ...(clienteId !== undefined && { clienteId: String(clienteId) }),
    });
    const reservations = normalizeDates(response.rentas || []);
    return estado ? reservations.filter((reservation) => reservation.estado === estado) : reservations;
  },
};