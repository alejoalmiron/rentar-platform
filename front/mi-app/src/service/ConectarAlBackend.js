const URL_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';
const URL_BASE_REST = `${URL_BASE}/api`;
const URL_BASE_GRAPHQL = `${URL_BASE}/graphql`;

function headersConSesion(headers = {}) {
  const token = localStorage.getItem('rentar.token');
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
    ...headers,
  };
}

export async function consumirEndpoint(url, opciones = {}) {
  try {
    const { headers, ...requestOptions } = opciones;
    const respuesta = await fetch(url, {
      ...requestOptions,
      headers: headersConSesion(headers),
    });

    const cuerpo = respuesta.status === 204 ? null : await respuesta.json();
    if (respuesta.status === 401) {
      localStorage.removeItem('rentar.token');
      localStorage.removeItem('rentar.user');
      window.dispatchEvent(new Event('rentar:unauthorized'));
    }
    if (!respuesta.ok) {
      throw new Error(cuerpo?.error || `Error ${respuesta.status}: ${respuesta.statusText}`);
    }
    if (cuerpo?.errors?.length) throw new Error(cuerpo.errors[0].message);
    return cuerpo;
  } catch (error) {
    console.error(`Error en petición a ${url}:`, error.message);
    throw error;
  }
}

// --- SERVICIOS REST ---
export const getVehiculos = () => consumirEndpoint(`${URL_BASE_REST}/vehiculos`);
export const crearVehiculo = (data) => consumirEndpoint(`${URL_BASE_REST}/vehiculos`, { method: 'POST', body: JSON.stringify(data) });

export const getClientes = () => consumirEndpoint(`${URL_BASE_REST}/clientes`);
export const crearCliente = (data) => consumirEndpoint(`${URL_BASE_REST}/clientes`, { method: 'POST', body: JSON.stringify(data) });

export const crearReserva = (data) => consumirEndpoint(`${URL_BASE_REST}/reservas`, { method: 'POST', body: JSON.stringify(data) });

export const iniciarSesionApi = (data) => consumirEndpoint(`${URL_BASE_REST}/auth/login`, {
  method: 'POST',
  body: JSON.stringify(data),
});

export const cerrarSesionApi = () => consumirEndpoint(`${URL_BASE_REST}/auth/logout`, { method: 'POST' });

// --- SERVICIO GRAPHQL ---
export const consultarGraphQL = (query, variables = {}) => {
  return consumirEndpoint(URL_BASE_GRAPHQL, {
    method: 'POST',
    body: JSON.stringify({ query, variables }),
  });
};