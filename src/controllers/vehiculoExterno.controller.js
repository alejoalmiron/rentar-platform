import { vehicleClient } from '../grpc/vehicle.client.js';
import { toHttpError } from '../grpc/httpErrors.js';
import { customerClient } from '../grpc/customer.client.js';

export const registrarVehiculoExterno = async (req, res) => {
  try {
    const clienteId = req.auth?.customerId;
    if (!clienteId) {
      return res.status(401).json({ error: 'No autorizado: Falta el ID del cliente en el token' });
    }
    const cliente = await customerClient.getById(clienteId);

    const payload = {
      clienteId: clienteId, 
      marca: req.body.marca,
      modelo: req.body.modelo,
      patente: req.body.patente,
      anio: req.body.anio ? Number(req.body.anio) : null,
      color: req.body.color,
      tipo: req.body.tipo,
    };

    const vehiculoCreado = await vehicleClient.createExternal(payload);

    return res.status(201).json({
      mensaje: 'Vehículo externo registrado exitosamente en estado PENDIENTE',
      vehiculo: vehiculoCreado,
      vehiculoExternoId: vehiculoCreado.vehiculoExternoId
    });

  } catch (error) {
    const mapped = toHttpError(error);
    return res.status(mapped.status).json(mapped.body);
  }
};

export const listarVehiculosExternos = async (req, res) => {
  try {
    const clienteId = req.auth?.customerId;
    if (!clienteId) {
      return res.status(401).json({ error: 'No autorizado: Falta el ID del cliente en el token' });
    }
    const vehiculos = await vehicleClient.listExternal(clienteId);
    return res.json(vehiculos);
  } catch (error) {
    const mapped = toHttpError(error);
    return res.status(mapped.status).json(mapped.body);
  }
};