# Rentar: alquiler de vehículos

Proyecto de la Universidad Nacional de Lanús para **Desarrollo de Software en Sistemas Distribuidos**, Hito 2 (RPC/gRPC). Se conserva la aplicación React del Hito 1 y se la conecta a un API Gateway Node.js. El Gateway entrega REST y GraphQL al frontend y llama por gRPC a tres servicios Python. Cada servicio es propietario de una base MySQL propia; el Gateway no accede a ellas.

## Arquitectura implementada

- `front/mi-app`: interfaz React 19 y Vite 8.
- `src`: API Gateway Express 5 / Apollo Server 5, clientes gRPC, JWT, autorización y orquestación de reservas.
- `services/vehicle-service`: Python 3.10, gRPC, SQLAlchemy y MySQL `vehicle_db`.
- `services/customer-service`: Python 3.10, gRPC, SQLAlchemy, bcrypt y MySQL `customer_db`; autentica cuentas y administra sus hashes.
- `services/rental-service`: Python 3.10, gRPC, SQLAlchemy y MySQL `rental_db`; aplica disponibilidad temporal, calcula importes y gestiona el ciclo de vida de reservas.
- Contratos canónicos: `services/<servicio>/proto/<dominio>/v1/*.proto`. Los contenedores generan sus stubs Python desde estos archivos al construirse.
- `prisma/schema.prisma` conserva el modelo del Hito 1 como referencia; el Gateway y los servicios de Hito 2 no lo usan para acceder a datos.
- **Hito 3:** RabbitMQ como broker de eventos. El exchange `rentar.events` (topic) conecta productores y consumidores. Al arrancar, `broker-init` declara la topología (colas + dead-letter). Contratos en [docs/eventos/README.md](docs/eventos/README.md) y [docs/eventos/contratos.schema.json](docs/eventos/contratos.schema.json). Helpers en `workers/common/` (workers), `app/messaging.py` de Vehicle/Rental y `src/messaging/rabbitmq.js` (Gateway).

La interfaz web se comunica exclusivamente con el Gateway. El Gateway orquesta las validaciones de cliente, vehículo y período; Rental Service vuelve a comprobar solapamientos al guardar para protegerse de solicitudes concurrentes.

## Requisitos

- Docker Engine y Docker Compose.
- Para ejecutar Gateway/frontend fuera de Docker: Node.js 22 o superior.
- Para ejecutar servicios Python fuera de Docker: Python 3.10 o superior y MySQL 8.

## Inicio completo con Docker

Desde la raíz del repositorio, cargar la plantilla local de entorno y levantar el sistema:

```powershell
docker compose --env-file .env.example up --build -d
```

Si vas a personalizar valores, copiá `.env.example` a `.env`, editá ese archivo ignorado por Git y ejecutá `docker compose up --build -d`. No publiques `.env` ni uses las credenciales de ejemplo fuera de desarrollo.

URLs y puertos:

| Componente | URL/puerto local |
| --- | --- |
| Frontend | `http://localhost:5173` |
| API Gateway REST | `http://localhost:5000/api` |
| GraphQL | `http://localhost:5000/graphql` |
| Swagger REST | `http://localhost:5000/api-docs` |
| Vehicle Service gRPC | `localhost:50051` |
| Customer Service gRPC | `localhost:50052` |
| Rental Service gRPC | `localhost:50053` |
| RabbitMQ (AMQP) | `localhost:5672` |
| RabbitMQ Management | `http://localhost:15672` |
| MySQL Customer / Vehicle / Rental | `localhost:3307` / `3308` / `3309` |

Detener los contenedores con `docker compose down`. Los datos persisten en volúmenes Docker. Para borrar también esos datos de desarrollo, usar `docker compose down -v`.

## Usuarios de desarrollo

Customer Service crea estas cuentas al iniciar por primera vez. Las contraseñas se guardan con bcrypt; las credenciales siguientes son únicamente para desarrollo local:

| Rol | Usuario | Contraseña |
| --- | --- | --- |
| Administrador | `admin` | `AdminRentar2026!` |
| Cliente | `cliente` | `ClienteRentar2026!` |

Se pueden cambiar mediante `SEED_ADMIN_USERNAME`, `SEED_ADMIN_PASSWORD`, `SEED_CLIENT_USERNAME`, `SEED_CLIENT_PASSWORD` y `SEED_CLIENT_DNI` antes del primer arranque. El seed no reemplaza contraseñas de cuentas que ya existen. Configurá `JWT_SECRET` en `.env` con un valor aleatorio de al menos 32 caracteres antes de un despliegue no local. El secreto por defecto de Compose es solo para desarrollo.

El inicio de sesión se hace en `POST /api/auth/login`; se devuelve un JWT que el frontend envía como `Authorization: Bearer <token>`. `POST /api/auth/logout` revoca el token en la instancia actual del Gateway y el frontend elimina su copia local.

Permisos aplicados en backend además de la interfaz:

- `ADMIN`: alta, modificación y baja de vehículos/clientes; consulta global del historial; puede cancelar cualquier reserva.
- `CLIENTE`: consulta vehículos/disponibilidad; crea reservas asociadas a su cuenta; ve y cancela solo sus propias reservas; accede a su historial.
- Las operaciones REST protegidas devuelven `401` si falta un token válido y `403` si el rol no tiene permiso. GraphQL informa los mismos códigos en `errors[].extensions`.

## Funcionalidades

La interfaz mantiene las operaciones del Hito 1: gestión y listado de vehículos, disponibilidad por fechas, gestión/listado de clientes, alta de reserva, consulta de reservas, cancelación e historial. Los perfiles cliente y administrador ven navegación distinta; el Gateway vuelve a verificar identidad, rol y propiedad de reservas.

## Pruebas

Desde la raíz:

```bash
npm test
npm --prefix front/mi-app run lint
npm --prefix front/mi-app run build
```

`npm test` verifica sintaxis del Gateway y ejecuta pruebas unitarias JWT. Con los contenedores arriba, las pruebas gRPC de servicios se pueden ejecutar así:

```bash
docker compose exec vehicle-service python -m unittest discover -s /app/tests
docker compose exec customer-service python -m pytest /app/tests/test_customer_service.py
docker compose exec rental-service python -m pytest /app/tests/test_rental.py
```

Las pruebas Python son de integración con sus servicios y bases MySQL, por lo que requieren el stack levantado. Antes de entregar, comprobar desde el navegador disponibilidad, altas/gestión de clientes y vehículos según rol, alta de reserva, consulta/cancelación propia y el historial; guardar capturas reales de cada caso.

Para verificar el broker de eventos (Hito 3), con el stack levantado:

```bash
docker compose run --rm --entrypoint python broker-init smoke_test.py
docker compose exec vehicle-service python -m app.smoke_broker
```

El primero declara/usa la topología compartida; el segundo prueba el helper de Vehicle Service. En el panel `http://localhost:15672` (usuario y clave de `RABBITMQ_USER` / `RABBITMQ_PASS`) tienen que verse el exchange `rentar.events`, el DLX `rentar.dlx`, la cola `rentar.dlq` y las colas de cada consumidor. Los flujos de verificación, incorporación externa y mantenimiento los implementan los otros integrantes sobre estos contratos.

## REST y GraphQL

Las rutas REST del Gateway están montadas en `/api/vehiculos`, `/api/clientes`, `/api/reservas` y `/api/auth`. Las operaciones GraphQL, ejemplos, tipos, permisos, validaciones y errores están documentados en [docs/GRAPHQL.md](docs/GRAPHQL.md). El Gateway también expone SDL introspection en `/graphql`.

## Persistencia

- Vehicle Service escribe solamente en `vehicle_db`; aplica sus migraciones Alembic al iniciar. Los datos descriptivos opcionales ausentes en filas antiguas quedan nulos, mientras que las altas nuevas validan los campos del modelo Hito 1.
- Customer Service escribe solamente en `customer_db`, incluidas cuentas y hashes de autenticación.
- Rental Service escribe solamente en `rental_db`; guarda IDs de cliente y vehículo sin claves foráneas entre servicios.
- No configures `DATABASE_URL` en el Gateway. Las variables de conexión de cada servicio se inyectan desde Compose.

## Estructura principal

```text
src/                         API Gateway Node.js (incluye src/messaging/rabbitmq.js)
services/vehicle-service/    Servicio gRPC Python + vehicle_db + app/messaging.py
services/customer-service/  Servicio gRPC Python + customer_db + autenticación
services/rental-service/    Servicio gRPC Python + rental_db + app/messaging.py
workers/common/              Topología, helper pika y declaración de colas
docs/eventos/                Contratos JSON de los eventos del Hito 3
front/mi-app/                Interfaz React/Vite
prisma/schema.prisma         Referencia del modelo Hito 1
```
