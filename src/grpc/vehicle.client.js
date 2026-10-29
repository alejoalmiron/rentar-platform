import grpc from '@grpc/grpc-js';
import { callGrpc } from './clientFactory.js';
import { fromProtoEnum, toProtoEnum } from './enums.js';

function fromProtoVehicle(vehicle) {
  return {
    ...vehicle,
    tipo: fromProtoEnum('TIPO_VEHICULO', vehicle.tipo),
    estado: fromProtoEnum('ESTADO_VEHICULO', vehicle.estado),
  };
}

function fromProtoExternalVehicle(vehicle) {
  return {
    ...vehicle,
    tipo: fromProtoEnum('TIPO_VEHICULO', vehicle.tipo),
    estado: fromProtoEnum('ESTADO_INCORPORACION', vehicle.estado),
  };
}

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

function validateRequiredFields(vehicle, fields = ['marca', 'modelo', 'patente']) {
  for (const field of fields) {
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
    const response = await callGrpc('vehicle', 'ListarVehiculos', {});
    return filterVehicles((response.vehiculos || []).map(fromProtoVehicle), filters);
  },
  async getById(id) {
    const response = await callGrpc('vehicle', 'ObtenerVehiculo', { id: toVehicleId(id) });
    return fromProtoVehicle(response.vehiculo);
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
    const response = await callGrpc('vehicle', 'CrearVehiculo', {
      marca: vehiculo.marca.trim(),
      modelo: vehiculo.modelo.trim(),
      patente: vehiculo.patente.trim(),
      anio: Number(vehiculo.anio),
      color: vehiculo.color || '',
      tipo: toProtoEnum('TIPO_VEHICULO', vehiculo.tipo),
      precioDiario: Number(vehiculo.precioDiario),
    });
    return fromProtoVehicle(response.vehiculo);
  },
  async update(id, vehiculo) {
    const vehicleId = toVehicleId(id);
    const current = await this.getById(vehicleId);
    if (vehiculo.patente !== undefined
      && String(vehiculo.patente).trim().toUpperCase() !== current.patente) {
      throw invalidArgument('La patente no puede modificarse una vez registrado el vehículo');
    }
    const updated = {
      marca: vehiculo.marca ?? current.marca,
      modelo: vehiculo.modelo ?? current.modelo,
      operativo: vehiculo.operativo ?? current.operativo,
      anio: vehiculo.anio ?? current.anio,
      color: vehiculo.color ?? current.color,
      tipo: vehiculo.tipo ?? current.tipo,
      precioDiario: vehiculo.precioDiario ?? current.precioDiario,
      estado: vehiculo.estado ?? current.estado,
    };
    validateRequiredFields(updated, ['marca', 'modelo']);
    if (typeof updated.operativo !== 'boolean') {
      throw invalidArgument('El campo operativo debe ser booleano');
    }

    const response = await callGrpc('vehicle', 'ActualizarVehiculo', {
      id: vehicleId,
      marca: updated.marca.trim(),
      modelo: updated.modelo.trim(),
      operativo: updated.operativo,
      anio: updated.anio,
      color: updated.color || '',
      tipo: toProtoEnum('TIPO_VEHICULO', updated.tipo),
      precioDiario: updated.precioDiario,
      estado: toProtoEnum('ESTADO_VEHICULO', updated.estado),
    });
    return fromProtoVehicle(response.vehiculo);
  },
  async deactivate(id) {
    const response = await callGrpc('vehicle', 'DarDeBajaVehiculo', { id: toVehicleId(id) });
    return fromProtoVehicle(response.vehiculo);
  },
  async checkOperational({ id, patente }) {
    const vehicle = id !== undefined
      ? await this.getById(id)
      : await this.getByPlate(patente);
    const response = await callGrpc('vehicle', 'VerificarOperatividad', { id: toVehicleId(vehicle.id) });
    return {
      exists: true,
      active: vehicle.activo,
      operational: response.operativo,
      operativo: response.operativo,
    };
  },

  async createExternal(payload) {
    const response = await callGrpc('vehicle', 'CrearVehiculoExterno', {
      vehiculoExternoId: payload.vehiculoExternoId || '',
      clienteId: String(payload.clienteId),
      marca: payload.marca,
      modelo: payload.modelo,
      patente: payload.patente,
      anio: payload.anio || 0,
      color: payload.color || '',
      tipo: toProtoEnum('TIPO_VEHICULO', payload.tipo),
      documento: payload.documento || '',
    });
    return fromProtoExternalVehicle(response.vehiculo);
  },

  async listExternal(clienteId) {
    const response = await callGrpc('vehicle', 'ListarVehiculosExternos', {
      clienteId: String(clienteId),
    });
    return (response.vehiculos || []).map(fromProtoExternalVehicle);
  },
};