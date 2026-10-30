import { callGrpc } from './clientFactory.js';
import { fromProtoEnum } from './enums.js';

export const customerClient = {
  async authenticate(username, password) {
    const response = await callGrpc('customer', 'AutenticarUsuario', { usuario: username, contrasena: password });
    return {
      userId: response.usuarioId,
      username: response.usuario,
      role: fromProtoEnum('ROL', response.rol),
      customerId: response.clienteId,
    };
  },
  async list() {
    const response = await callGrpc('customer', 'ListarClientes', {});
    return response.clientes || [];
  },
  async getById(id) {
    return (await callGrpc('customer', 'ObtenerCliente', { id: String(id) })).cliente;
  },
  async getByDocument(documento) {
    const customers = await this.list();
    const customer = customers.find((item) => item.dni === documento);
    if (!customer) {
      const error = new Error('Cliente no encontrado');
      error.code = 5;
      throw error;
    }
    return customer;
  },
  async create(cliente) {
    return (await callGrpc('customer', 'CrearCliente', {
      dni: cliente.dni || cliente.documento,
      nombre: cliente.nombre,
      apellido: cliente.apellido,
      email: cliente.email,
      telefono: cliente.telefono || '',
    })).cliente;
  },
  async update(id, cliente) {
    return (await callGrpc('customer', 'ActualizarCliente', {
      id: String(id),
      nombre: cliente.nombre || '',
      apellido: cliente.apellido || '',
      email: cliente.email || '',
      telefono: cliente.telefono || '',
    })).cliente;
  },
  async deactivate(id) {
    return (await callGrpc('customer', 'DarDeBajaCliente', { id: String(id) })).cliente;
  },
  validate({ id }) {
    return callGrpc('customer', 'ValidarClienteActivo', { id: String(id) })
      .then((response) => ({
        exists: response.existe,
        active: response.activo,
        canRent: response.activo,
        message: response.mensaje,
      }));
  },
};
