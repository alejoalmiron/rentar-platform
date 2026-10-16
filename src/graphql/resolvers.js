import { customerClient } from '../grpc/customer.client.js';
import { rentalClient } from '../grpc/rental.client.js';
import { toGraphqlError } from '../grpc/httpErrors.js';
import { vehicleClient } from '../grpc/vehicle.client.js';

function requireGraphqlAuth(context) {
  if (!context.auth) {
    const error = new Error('Se requiere iniciar sesión');
    error.code = 16;
    throw error;
  }
  return context.auth;
}

async function hydrateReservation(reservation) {
  const customerId = reservation.customerId ?? reservation.clienteId;
  const vehicleId = reservation.vehicleId ?? reservation.vehiculoId;
  const [cliente, vehiculo] = await Promise.all([
    reservation.cliente || customerId === undefined
      ? reservation.cliente
      : customerClient.getById(customerId),
    reservation.vehiculo || vehicleId === undefined
      ? reservation.vehiculo
      : vehicleClient.getById(vehicleId),
  ]);

  return { ...reservation, cliente, vehiculo };
}

async function resolverGraphql(operation) {
  try {
    return await operation();
  } catch (error) {
    throw toGraphqlError(error);
  }
}

export const resolvers = {
  Query: {
    vehiculosDisponibles: (_, filters, context) => resolverGraphql(async () => {
      requireGraphqlAuth(context);
      const { fechaInicio, fechaFin, ...vehicleFilters } = filters;
      const vehicles = await vehicleClient.list(vehicleFilters);
      const checks = await Promise.all(vehicles.map(async (vehicle) => {
        const [operational, reservationAvailability] = await Promise.all([
          vehicleClient.checkOperational({ id: vehicle.id, patente: vehicle.patente }),
          rentalClient.checkAvailability({ vehiculoId: vehicle.id, fechaInicio, fechaFin }),
        ]);

        const isOperational = operational.operational !== false
          && operational.active !== false
          && vehicle.activo !== false;
        return isOperational && reservationAvailability.available !== false ? vehicle : null;
      }));

      return checks.filter(Boolean);
    }),
    reservasPorCliente: (_, { dni }, context) => resolverGraphql(async () => {
      const auth = requireGraphqlAuth(context);
      if (auth.role === 'ADMIN' && !dni) {
        const error = new Error('El administrador debe indicar un DNI para consultar reservas');
        error.code = 3;
        throw error;
      }
      const customer = auth.role === 'CLIENTE'
        ? await customerClient.getById(auth.customerId)
        : await customerClient.getByDocument(dni);
      if (auth.role === 'CLIENTE' && dni && customer.dni !== dni) {
        const error = new Error('Solo podés consultar tus propias reservas');
        error.code = 7;
        throw error;
      }
      const reservations = await rentalClient.list({ clienteId: customer.id });
      return Promise.all(reservations.map(hydrateReservation));
    }),
    historialReservas: (_, { estado, patente }, context) => resolverGraphql(async () => {
      const auth = requireGraphqlAuth(context);
      const reservations = await rentalClient.history({
        clienteId: auth.role === 'CLIENTE' ? auth.customerId : undefined,
        estado,
      });
      const hydrated = await Promise.all(reservations.map(hydrateReservation));
      return hydrated.filter((reservation) => (
        (!estado || reservation.estado === estado)
        && (!patente || reservation.vehiculo?.patente === patente)
      ));
    }),
  },
  Mutation: {
    cancelarReserva: (_, { id }, context) => resolverGraphql(async () => {
      const auth = requireGraphqlAuth(context);
      const current = await rentalClient.getById(id);
      if (auth.role === 'CLIENTE' && current.clienteId !== auth.customerId) {
        const error = new Error('Solo podés cancelar tus propias reservas');
        error.code = 7;
        throw error;
      }
      const reservation = await rentalClient.cancel(id);
      return hydrateReservation(reservation);
    }),
  },
  Cliente: {
    dni: (cliente) => cliente.dni || cliente.documento,
  },
  Reserva: {
    montoTotal: (reserva) => reserva.montoTotal ?? reserva.importeTotal ?? reserva.precioTotal,
  },
};