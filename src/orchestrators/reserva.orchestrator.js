import { customerClient } from '../grpc/customer.client.js';
import { rentalClient } from '../grpc/rental.client.js';
import { vehicleClient } from '../grpc/vehicle.client.js';

function assertAllowed(result, description) {
  if (result?.exists === false || result?.active === false || result?.canRent === false) {
    const error = new Error(`${description} no válido o inactivo`);
    error.code = 9;
    throw error;
  }
}

export async function createReservation(input) {
  const { clienteId, vehiculoId, clienteDni, vehiculoPatente, fechaInicio, fechaFin } = input;
  const [customer, vehicle] = await Promise.all([
    clienteId !== undefined
      ? customerClient.getById(clienteId)
      : customerClient.getByDocument(clienteDni),
    vehiculoId !== undefined
      ? vehicleClient.getById(vehiculoId)
      : vehicleClient.getByPlate(vehiculoPatente),
  ]);

  const [customerValidation, vehicleValidation, reservationAvailability] = await Promise.all([
    customerClient.validate({ id: customer.id, documento: customer.documento || customer.dni }),
    vehicleClient.checkOperational({ id: vehicle.id, patente: vehicle.patente }),
    rentalClient.checkAvailability({ vehiculoId: vehicle.id, fechaInicio, fechaFin }),
  ]);

  assertAllowed(customerValidation, 'El cliente');
  assertAllowed(vehicleValidation, 'El vehículo');
  if (vehicle.activo === false) {
    const error = new Error('El vehículo no existe o no se encuentra activo');
    error.code = 9;
    throw error;
  }
  if (vehicleValidation?.operational === false || vehicleValidation?.available === false) {
    const error = new Error('El vehículo no se encuentra operativo');
    error.code = 9;
    throw error;
  }
  if (reservationAvailability?.available === false) {
    const error = new Error('El vehículo no está disponible en las fechas solicitadas');
    error.code = 9;
    throw error;
  }

  return rentalClient.create({
    clienteId: customer.id,
    vehiculoId: vehicle.id,
    fechaInicio,
    fechaFin,
    precioDiario: vehicle.precioDiario,
  });
}