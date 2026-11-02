// Carga datos de prueba a través del API Gateway, como lo haría un usuario.
// Pasa por las mismas validaciones y dispara los mismos eventos que la interfaz,
// sin acceder a las bases de los servicios. Se puede ejecutar más de una vez:
// lo que ya existe no se vuelve a crear.

const GATEWAY_URL = process.env.GATEWAY_URL || 'http://localhost:5000';
const ADMIN = {
  username: process.env.SEED_ADMIN_USERNAME || 'admin',
  password: process.env.SEED_ADMIN_PASSWORD || 'AdminRentar2026!',
};
const CLIENT = {
  username: process.env.SEED_CLIENT_USERNAME || 'cliente',
  password: process.env.SEED_CLIENT_PASSWORD || 'ClienteRentar2026!',
  dni: process.env.SEED_CLIENT_DNI || '40999000',
};

// XYZ999 figura denunciada en el registro policial simulado: termina ROBADO.
// ABC123 y AA123BB quedan libres para probar la incorporación de externos en vivo.
const VEHICULOS = [
  { patente: 'AB123CD', marca: 'Toyota', modelo: 'Corolla', anio: 2022, color: 'Blanco', tipo: 'SEDAN', precioDiario: 45000 },
  { patente: 'AC456EF', marca: 'Volkswagen', modelo: 'Amarok', anio: 2021, color: 'Gris', tipo: 'PICKUP', precioDiario: 70000 },
  { patente: 'AD789GH', marca: 'Jeep', modelo: 'Compass', anio: 2023, color: 'Negro', tipo: 'SUV', precioDiario: 65000 },
  { patente: 'AE012IJ', marca: 'Fiat', modelo: 'Cronos', anio: 2020, color: 'Rojo', tipo: 'SEDAN', precioDiario: 38000 },
  { patente: 'AF345KL', marca: 'Peugeot', modelo: '208', anio: 2022, color: 'Azul', tipo: 'HATCHBACK', precioDiario: 40000 },
  { patente: 'AG678MN', marca: 'Ford', modelo: 'Mustang', anio: 2019, color: 'Amarillo', tipo: 'COUPE', precioDiario: 120000 },
  { patente: 'XYZ999', marca: 'Chevrolet', modelo: 'Onix', anio: 2018, color: 'Plata', tipo: 'HATCHBACK', precioDiario: 30000 },
];

const CLIENTES = [
  { dni: '30123456', nombre: 'María', apellido: 'González', email: 'maria.gonzalez@rentar.local', telefono: '1145678901' },
  { dni: '33444555', nombre: 'Juan', apellido: 'Pérez', email: 'juan.perez@rentar.local', telefono: '1156789012' },
  { dni: '35666777', nombre: 'Lucía', apellido: 'Fernández', email: 'lucia.fernandez@rentar.local', telefono: '1167890123' },
];

// Fechas relativas al momento de la carga, así siempre son futuras.
// La de 12 horas empieza en menos de 24 h: su mantenimiento termina NO_REALIZADO.
const RESERVAS = [
  { clienteDni: CLIENT.dni, vehiculoPatente: 'AB123CD', desdeHoras: 48, dias: 3 },
  { clienteDni: CLIENT.dni, vehiculoPatente: 'AD789GH', desdeHoras: 12, dias: 2 },
  { clienteDni: CLIENT.dni, vehiculoPatente: 'AC456EF', desdeHoras: 240, dias: 2, cancelar: true },
  { clienteDni: '30123456', vehiculoPatente: 'AB123CD', desdeHoras: 168, dias: 2 },
  { clienteDni: '33444555', vehiculoPatente: 'AE012IJ', desdeHoras: 72, dias: 1 },
  { clienteDni: '35666777', vehiculoPatente: 'AF345KL', desdeHoras: 120, dias: 4 },
];

// Vehículos propios del usuario cliente: DEF456 se incorpora; GHI789 se rechaza por titularidad.
const EXTERNOS = [
  { patente: 'DEF456', marca: 'Renault', modelo: 'Kangoo', anio: 2021, color: 'Blanco', tipo: 'PICKUP', precioDiario: 35000 },
  { patente: 'GHI789', marca: 'Citroën', modelo: 'C3', anio: 2019, color: 'Gris', tipo: 'HATCHBACK', precioDiario: 32000 },
];

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function request(method, path, { token, body } = {}) {
  const response = await fetch(`${GATEWAY_URL}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const error = new Error(data?.error || `HTTP ${response.status}`);
    error.status = response.status;
    throw error;
  }
  return data;
}

// Al levantar el stack, el Gateway y los servicios tardan en estar listos:
// se reintenta el login hasta que responde.
async function loginWithRetry(credentials, attempts = 60) {
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      return (await request('POST', '/api/auth/login', { body: credentials })).token;
    } catch (error) {
      if (attempt === attempts) throw error;
      console.log(`Esperando al API Gateway (intento ${attempt}/${attempts}): ${error.message}`);
      await sleep(3000);
    }
  }
  return null;
}

function periodo(desdeHoras, dias) {
  const inicio = new Date(Date.now() + desdeHoras * 3600 * 1000);
  inicio.setMinutes(0, 0, 0);
  const fin = new Date(inicio.getTime() + dias * 24 * 3600 * 1000);
  return { fechaInicio: inicio.toISOString(), fechaFin: fin.toISOString() };
}

async function seedVehiculos(token) {
  const existentes = new Set((await request('GET', '/api/vehiculos', { token })).map((v) => v.patente));
  let creados = 0;
  for (const vehiculo of VEHICULOS) {
    if (existentes.has(vehiculo.patente)) continue;
    await request('POST', '/api/vehiculos', { token, body: vehiculo });
    creados += 1;
  }
  console.log(`Vehículos: ${creados} creados, ${VEHICULOS.length - creados} ya existían.`);
  return creados;
}

async function seedClientes(token) {
  const existentes = new Set((await request('GET', '/api/clientes', { token })).map((c) => c.dni));
  let creados = 0;
  for (const cliente of CLIENTES) {
    if (existentes.has(cliente.dni)) continue;
    await request('POST', '/api/clientes', { token, body: cliente });
    creados += 1;
  }
  console.log(`Clientes: ${creados} creados, ${CLIENTES.length - creados} ya existían.`);
}

async function seedReservas(token) {
  for (const reserva of RESERVAS) {
    const { desdeHoras, dias, cancelar, ...datos } = reserva;
    try {
      const creada = await request('POST', '/api/reservas', {
        token,
        body: { ...datos, ...periodo(desdeHoras, dias) },
      });
      if (cancelar) {
        await request('PATCH', `/api/reservas/${creada.id}/cancelar`, { token });
      }
      console.log(`Reserva ${datos.vehiculoPatente} para DNI ${datos.clienteDni}: ${cancelar ? 'CANCELADA' : 'CONFIRMADA'}.`);
    } catch (error) {
      console.log(`Reserva ${datos.vehiculoPatente} para DNI ${datos.clienteDni} omitida: ${error.message}`);
    }
  }
}

async function seedExternos(token) {
  const existentes = new Set((await request('GET', '/api/vehiculos-externos', { token })).map((v) => v.patente));
  let creados = 0;
  for (const vehiculo of EXTERNOS) {
    if (existentes.has(vehiculo.patente)) continue;
    await request('POST', '/api/vehiculos-externos', { token, body: vehiculo });
    creados += 1;
  }
  console.log(`Vehículos externos: ${creados} registrados, ${EXTERNOS.length - creados} ya existían.`);
}

async function main() {
  console.log(`Cargando datos de prueba en ${GATEWAY_URL}...`);
  const adminToken = await loginWithRetry(ADMIN);

  const vehiculosCreados = await seedVehiculos(adminToken);
  await seedClientes(adminToken);

  // Las reservas solo se cargan sobre una flota recién creada, para no duplicarlas
  // si el script se vuelve a ejecutar con datos de una carga anterior.
  if (vehiculosCreados === VEHICULOS.length) {
    await seedReservas(adminToken);
  } else {
    console.log('Reservas: se omiten porque la flota ya tenía datos.');
  }

  const clientToken = await loginWithRetry(CLIENT);
  await seedExternos(clientToken);

  console.log('Datos de prueba cargados.');
}

main().catch((error) => {
  console.error('No se pudieron cargar los datos de prueba:', error.message);
  process.exitCode = 1;
});
