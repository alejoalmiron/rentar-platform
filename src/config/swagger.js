import swaggerJSDoc from 'swagger-jsdoc';

const options = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'API Rentar - Sistema de Alquiler de Vehículos',
      version: '1.0.0',
      description: 'Documentación de los endpoints REST para el Hito 1 (UNLa)',
    },
    servers: [
      {
        url: 'http://localhost:5000',
        description: 'Servidor Local',
      },
    ],
    security: [{ bearerAuth: [] }],
    tags: [
      { name: 'Vehiculos', description: 'ABM de vehiculos' },
      { name: 'Clientes', description: 'ABM de clientes' },
      { name: 'Reservas', description: 'Creacion y cancelacion de reservas' },
    ],
    components: {
      securitySchemes: {
        bearerAuth: {
          type: 'http',
          scheme: 'bearer',
          bearerFormat: 'JWT',
          description: 'Obtené el token en POST /api/auth/login y enviá Authorization: Bearer <token>.',
        },
      },
      schemas: {
        LoginRequest: {
          type: 'object',
          required: ['username', 'password'],
          properties: {
            username: { type: 'string', example: 'cliente' },
            password: { type: 'string', format: 'password' },
          },
        },
        LoginResponse: {
          type: 'object',
          properties: {
            token: { type: 'string', description: 'JWT firmado por el API Gateway.' },
            expiresIn: { type: 'integer', example: 28800 },
            user: {
              type: 'object',
              properties: {
                id: { type: 'string' },
                username: { type: 'string' },
                role: { type: 'string', enum: ['ADMIN', 'CLIENTE'] },
                customerId: { type: 'string', nullable: true },
              },
            },
          },
        },
        Vehiculo: {
          type: 'object',
          properties: {
            id: { type: 'integer', example: 1 },
            patente: { type: 'string', example: 'AA123BC' },
            marca: { type: 'string', example: 'Toyota' },
            modelo: { type: 'string', example: 'Corolla' },
            anio: { type: 'integer', example: 2024 },
            color: { type: 'string', nullable: true, example: 'Gris' },
            tipo: { type: 'string', enum: ['SEDAN', 'SUV', 'PICKUP', 'COUPE', 'HATCHBACK'] },
            precioDiario: { type: 'number', format: 'float', example: 45000 },
            estado: { type: 'string', example: 'DISPONIBLE' },
            activo: { type: 'boolean', example: true },
          },
        },
        Cliente: {
          type: 'object',
          properties: {
            id: { type: 'string', format: 'uuid', example: 'e3c157dd-7cc8-4a34-8bb3-833bcb43b8e2' },
            documento: { type: 'string', example: '40123456' },
            dni: { type: 'string', example: '40123456' },
            nombre: { type: 'string', example: 'Carlos' },
            apellido: { type: 'string', example: 'Gomez' },
            email: { type: 'string', format: 'email', example: 'carlos@email.com' },
            telefono: { type: 'string', example: '1144445555' },
          },
        },
        Reserva: {
          type: 'object',
          properties: {
            id: { type: 'string', format: 'uuid', example: '85647a01-0483-48f4-87b9-4035cac1af7c' },
            clienteId: { type: 'string', format: 'uuid', example: 'e3c157dd-7cc8-4a34-8bb3-833bcb43b8e2' },
            vehiculoId: { type: 'integer', example: 1 },
            clienteDni: { type: 'string', example: '40123456' },
            vehiculoPatente: { type: 'string', example: 'AA123BC' },
            fechaInicio: { type: 'string', format: 'date', example: '2030-01-10' },
            fechaFin: { type: 'string', format: 'date', example: '2030-01-13' },
            precioTotal: { type: 'number', format: 'float', example: 135000 },
            estado: { type: 'string', example: 'CONFIRMADA' },
          },
        },
      },
    },
    paths: {
      '/api/auth/login': {
        post: {
          security: [],
          tags: ['Autenticación'],
          summary: 'Iniciar sesión y obtener un JWT',
          requestBody: { required: true, content: { 'application/json': { schema: { $ref: '#/components/schemas/LoginRequest' } } } },
          responses: {
            200: { description: 'Credenciales válidas', content: { 'application/json': { schema: { $ref: '#/components/schemas/LoginResponse' } } } },
            400: { description: 'Falta usuario o contraseña' },
            401: { description: 'Usuario o contraseña inválidos' },
            503: { description: 'Customer Service no disponible' },
          },
        },
      },
      '/api/auth/logout': {
        post: {
          tags: ['Autenticación'],
          summary: 'Revocar el JWT de la instancia actual y cerrar sesión',
          responses: {
            204: { description: 'Sesión cerrada' },
            401: { description: 'Token ausente, inválido o vencido' },
          },
        },
      },
      '/api/vehiculos': {
        get: {
          tags: ['Vehiculos'], summary: 'Listar vehiculos activos',
          responses: { 200: { description: 'Lista de vehiculos', content: { 'application/json': { schema: { type: 'array', items: { $ref: '#/components/schemas/Vehiculo' } } } } } },
        },
        post: {
          tags: ['Vehiculos'], summary: 'Crear vehiculo',
          requestBody: { required: true, content: { 'application/json': { schema: { $ref: '#/components/schemas/Vehiculo' } } } },
          responses: { 201: { description: 'Vehiculo creado' }, 500: { description: 'Error de servidor' } },
        },
      },
      '/api/vehiculos/{id}': {
        parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'integer' } }],
        get: { tags: ['Vehiculos'], summary: 'Obtener vehiculo', responses: { 200: { description: 'Vehiculo encontrado' }, 404: { description: 'No encontrado' } } },
        put: { tags: ['Vehiculos'], summary: 'Modificar vehiculo', requestBody: { required: true, content: { 'application/json': { schema: { $ref: '#/components/schemas/Vehiculo' } } } }, responses: { 200: { description: 'Vehiculo actualizado' }, 400: { description: 'Operacion invalida' } } },
        delete: { tags: ['Vehiculos'], summary: 'Dar de baja vehiculo', responses: { 200: { description: 'Baja logica realizada' } } },
      },
      '/api/clientes': {
        get: { tags: ['Clientes'], summary: 'Listar clientes activos', responses: { 200: { description: 'Lista de clientes', content: { 'application/json': { schema: { type: 'array', items: { $ref: '#/components/schemas/Cliente' } } } } } } },
        post: { tags: ['Clientes'], summary: 'Crear cliente', requestBody: { required: true, content: { 'application/json': { schema: { $ref: '#/components/schemas/Cliente' } } } }, responses: { 201: { description: 'Cliente creado' }, 500: { description: 'Error de servidor' } } },
      },
      '/api/clientes/{id}': {
        parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } }],
        get: { tags: ['Clientes'], summary: 'Obtener cliente', responses: { 200: { description: 'Cliente encontrado' }, 404: { description: 'No encontrado' } } },
        put: { tags: ['Clientes'], summary: 'Modificar cliente', requestBody: { required: true, content: { 'application/json': { schema: { $ref: '#/components/schemas/Cliente' } } } }, responses: { 200: { description: 'Cliente actualizado' } } },
        delete: { tags: ['Clientes'], summary: 'Dar de baja cliente', responses: { 200: { description: 'Baja logica realizada' } } },
      },
      '/api/reservas': {
        post: { tags: ['Reservas'], summary: 'Crear reserva', requestBody: { required: true, content: { 'application/json': { schema: { $ref: '#/components/schemas/Reserva' }, example: { clienteDni: '40123456', vehiculoPatente: 'AA123BC', fechaInicio: '2030-01-10', fechaFin: '2030-01-13' } } } }, responses: { 201: { description: 'Reserva creada' }, 400: { description: 'Validacion fallida' } } },
      },
      '/api/reservas/{id}/cancelar': {
        parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } }],
        patch: { tags: ['Reservas'], summary: 'Cancelar reserva', responses: { 200: { description: 'Reserva cancelada' }, 400: { description: 'No se puede cancelar' }, 404: { description: 'No encontrada' } } },
      },
    },
  },
  apis: [],
};

export const swaggerSpec = swaggerJSDoc(options);