import grpc from '@grpc/grpc-js';
import { callGrpc } from './clientFactory.js';
import { normalizeDates } from './timestamps.js';

const unwrap = (response, key) => normalizeDates(response?.[key] ?? response);

function invalidArgument(message) {
  const error = new Error(message);
  error.code = grpc.status.INVALID_ARGUMENT;
  return error;
}

function toVehicleId(id) {
  const value = Number(id);
  if (!Number.isInteger(value) || value < 1 || value > 2147483647) {
    throw invalidArgument('El id del vehículo debe ser un entero positivo');
  }
  return value;
}

function validateRequiredFields(vehicle) {
  for (const field of ['marca', 'modelo', 'patente']) {
    if (typeof vehicle[field] !== 'string' || vehicle[field].trim() === '') {
      throw invalidArgument(`El campo ${field} es obligatorio`);
    }
  }
}

function filterVehicles(vehicles, filters) {
  const supportedFilters = new Set([
    'marca', 'modelo', 'patente', 'operativo', 'activo', 'tipo', 'precioMin', 'precioMax',
  ]);
  const entries = Object.entries(filters).filter(([, value]) => value !== undefined && value !== '');
  const unsupportedFilter = entries.find(([key]) => !supportedFilters.has(key));
  if (unsupportedFilter) {
    const error = new Error(`El filtro ${unsupportedFilter[0]} no está soportado por el servicio de Vehículos`);
    error.code = grpc.status.UNIMPLEMENTED;
    throw error;
  }

  return vehicles.filter((vehicle) => entries.every(([key, value]) => {
    if (key === 'precioMin') return vehicle.precioDiario >= Number(value);
    if (key === 'precioMax') return vehicle.precioDiario <= Number(value);
    return String(vehicle[key]).toLowerCase() === String(value).toLowerCase();
  }));
}

export const vehicleClient = {
  async list(filters = {}) {
    const response = await callGrpc('vehicle', 'GetVehicles', {});
    return filterVehicles(normalizeDates(response.vehicles || []), filters);
  },
  async getById(id) {
    return unwrap(await callGrpc('vehicle', 'GetVehicleById', { id: toVehicleId(id) }), 'vehicle');
  },
  async getByPlate(patente) {
    const vehicles = await this.list();
    const vehicle = vehicles.find((item) => item.patente === patente);
    if (!vehicle) {
      const error = new Error('Vehículo no encontrado');
      error.code = grpc.status.NOT_FOUND;
      throw error;
    }
    return vehicle;
  },
  async create(vehiculo) {
    validateRequiredFields(vehiculo);
    const response = await callGrpc('vehicle', 'CreateVehicle', {
      marca: vehiculo.marca.trim(),
      modelo: vehiculo.modelo.trim(),
      patente: vehiculo.patente.trim(),
      anio: Number(vehiculo.anio),
      color: vehiculo.color || '',
      tipo: vehiculo.tipo,
      precioDiario: Number(vehiculo.precioDiario),
      estado: vehiculo.estado || 'DISPONIBLE',
    });
    return unwrap(response, 'vehicle');
  },
  async update(id, vehiculo) {
    const vehicleId = toVehicleId(id);
    const current = await this.getById(vehicleId);
    const updated = {
      marca: vehiculo.marca ?? current.marca,
      modelo: vehiculo.modelo ?? current.modelo,
      patente: vehiculo.patente ?? current.patente,
      operativo: vehiculo.operativo ?? current.operativo,
      anio: vehiculo.anio ?? current.anio,
      color: vehiculo.color ?? current.color,
      tipo: vehiculo.tipo ?? current.tipo,
      precioDiario: vehiculo.precioDiario ?? current.precioDiario,
      estado: vehiculo.estado ?? current.estado,
    };
    validateRequiredFields(updated);
    if (typeof updated.operativo !== 'boolean') {
      throw invalidArgument('El campo operativo debe ser booleano');
    }

    const response = await callGrpc('vehicle', 'UpdateVehicle', {
      id: vehicleId,
      marca: updated.marca.trim(),
      modelo: updated.modelo.trim(),
      patente: updated.patente.trim(),
      operativo: updated.operativo,
      anio: updated.anio,
      color: updated.color || '',
      tipo: updated.tipo,
      precioDiario: updated.precioDiario,
      estado: updated.estado,
    });
    return unwrap(response, 'vehicle');
  },
  async deactivate(id) {
    const vehicleId = toVehicleId(id);
    const vehicle = await this.getById(vehicleId);
    await callGrpc('vehicle', 'DeleteVehicle', { id: vehicleId });
    return { ...vehicle, activo: false };
  },
  async checkOperational({ id, patente }) {
    const vehicle = id !== undefined
      ? await this.getById(id)
      : await this.getByPlate(patente);
    const response = await callGrpc('vehicle', 'CheckOperative', { id: toVehicleId(vehicle.id) });
    return {
      exists: true,
      active: vehicle.activo,
      operational: response.operativo,
      operativo: response.operativo,
    };
  },
};