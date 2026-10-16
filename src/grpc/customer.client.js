import { callGrpc } from './clientFactory.js';
import { normalizeDates } from './timestamps.js';

const unwrap = (response, key) => normalizeDates(response?.[key] ?? response);

export const customerClient = {
  authenticate(username, password) {
    return callGrpc('customer', 'AuthenticateUser', { username, password });
  },
  async list() {
    const response = await callGrpc('customer', 'ListCustomers', {});
    return normalizeDates(response.customers || []);
  },
  async getById(id) {
    return unwrap(await callGrpc('customer', 'GetCustomerById', { id: String(id) }), 'customer');
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
    return unwrap(await callGrpc('customer', 'CreateCustomer', {
      dni: cliente.dni || cliente.documento,
      nombre: cliente.nombre,
      apellido: cliente.apellido,
      email: cliente.email,
      telefono: cliente.telefono || '',
    }), 'customer');
  },
  async update(id, cliente) {
    return unwrap(await callGrpc('customer', 'UpdateCustomer', {
      id: String(id),
      nombre: cliente.nombre || '',
      apellido: cliente.apellido || '',
      email: cliente.email || '',
      telefono: cliente.telefono || '',
    }), 'customer');
  },
  async deactivate(id) {
    return unwrap(await callGrpc('customer', 'DeactivateCustomer', { id: String(id) }), 'customer');
  },
  validate({ id }) {
    return callGrpc('customer', 'ValidateActiveCustomer', { id: String(id) })
      .then((response) => ({
        exists: response.exists,
        active: response.isActive,
        canRent: response.isActive,
        message: response.message,
      }));
  },
};