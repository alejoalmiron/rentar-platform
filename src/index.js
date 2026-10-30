// Punto de entrada del API Gateway: monta REST, GraphQL y Swagger sobre Express.
import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import swaggerUi from 'swagger-ui-express';
import { swaggerSpec } from './config/swagger.js';
import authRoutes from './routes/auth.routes.js';
import { closeGrpcClients } from './grpc/clientFactory.js';
import { optionalAuthentication, validateJwtConfiguration } from './auth/jwt.js';
import vehiculoRoutes from './routes/vehiculo.routes.js';
import clienteRoutes from './routes/cliente.routes.js';

import reservaRoutes from './routes/reserva.routes.js';
import vehiculoExternoRoutes from './routes/vehiculoExterno.routes.js';

// GraphQL
import { ApolloServer } from '@apollo/server';
import { expressMiddleware } from '@as-integrations/express5';
import { typeDefs } from './graphql/schema.js';
import { resolvers } from './graphql/resolvers.js';

dotenv.config();

const app = express();
let httpServer;

app.use(cors({ origin: '*' }));
app.use(express.json());


app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// Rutas REST: cada grupo de URLs se delega a su archivo en routes/.
app.use('/api/auth', authRoutes);
app.use('/api/vehiculos', vehiculoRoutes);
app.use('/api/clientes', clienteRoutes);
app.use('/api/reservas', reservaRoutes);
app.use('/api', vehiculoExternoRoutes);

app.get('/', (req, res) => {
  res.json({ mensaje: 'API Rentar funcionando correctamente' });
});

// Apollo debe arrancar antes de montarse; el contexto le pasa a los resolvers la sesión del JWT.
async function startServer() {
  if (process.env.NODE_ENV === 'production') validateJwtConfiguration();
  const server = new ApolloServer({ 
    typeDefs, 
    resolvers,
    introspection: true
  });
  
  await server.start();
  app.use('/graphql', express.json(), expressMiddleware(server, {
    context: async ({ req }) => ({ auth: optionalAuthentication(req) }),
  }));

  const PORT = process.env.PORT || 5000;
  httpServer = app.listen(PORT, () => {
    console.log(`🚀 Servidor corriendo en http://localhost:${PORT}`);
    console.log(`📄 Documentación Swagger lista en http://localhost:${PORT}/api-docs`);
    console.log(`🎯 GraphQL Sandbox listo en http://localhost:${PORT}/graphql`);
  });
}

startServer().catch((error) => {
  console.error('No se pudo iniciar el API Gateway:', error);
  process.exitCode = 1;
});

// Apagado ordenado: termina los pedidos en curso y cierra las conexiones gRPC.
for (const signal of ['SIGINT', 'SIGTERM']) {
  process.once(signal, () => {
    httpServer?.close(() => {
      closeGrpcClients();
      process.exit(0);
    });
  });
}

