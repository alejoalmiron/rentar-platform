# Rentar: sistema distribuido de alquiler de vehículos

Trabajo práctico de **Desarrollo de Software en Sistemas Distribuidos**, Universidad Nacional de Lanús (UNLa).

Rentar administra la flota de vehículos, los clientes y las reservas de una empresa de alquiler. El sistema se construyó de forma incremental en tres hitos. En cada uno se incorporó un mecanismo de comunicación distinto entre componentes, manteniendo las funcionalidades y la interfaz web de los anteriores.

| Hito | Mecanismo | Qué incorporó |
| --- | --- | --- |
| **1** | REST / GraphQL | Interfaz web y API con las 7 funcionalidades del negocio. REST documentado con Swagger y GraphQL con tipos y operaciones documentados. |
| **2** | RPC (gRPC) | Separación en tres servicios independientes (vehículos, clientes, reservas), cada uno con su base de datos, detrás de un API Gateway. Contratos `.proto` documentados. Gateway en Node.js y servicios en Python. |
| **3** | RabbitMQ | Comunicación asíncrona basada en eventos para procesos que no deben bloquear el flujo principal: verificación de patentes, incorporación de vehículos de propietarios externos y mantenimiento preventivo. |

## Inicio rápido

Requisitos: [Docker Desktop](https://www.docker.com/products/docker-desktop/) (en Windows, con el backend WSL 2) o Docker Engine con Docker Compose. Hay que tener libres los puertos de la [tabla de componentes](#arquitectura).

```bash
git clone https://github.com/alejoalmiron/rentar-backend.git
cd rentar-backend
docker compose --env-file .env.example up --build -d
```

La primera vez tarda varios minutos porque construye las imágenes. El sistema está listo cuando `docker compose --env-file .env.example ps -a` muestra todos los servicios `Up`, las bases y RabbitMQ `healthy`, y `broker-init` como `Exited (0)`: ese contenedor declara la topología del broker y termina.

| Acceso | URL |
| --- | --- |
| Interfaz web | http://localhost:5173 |
| API REST | http://localhost:5000/api |
| GraphQL | http://localhost:5000/graphql |
| Swagger | http://localhost:5000/api-docs |
| Panel de RabbitMQ | http://localhost:15672 (usuario `rentar`, contraseña `rentar-dev-pass`) |

Customer Service crea estas cuentas en el primer arranque:

| Rol | Usuario | Contraseña |
| --- | --- | --- |
| Administrador | `admin` | `AdminRentar2026!` |
| Cliente | `cliente` | `ClienteRentar2026!` |

Para detener el sistema: `docker compose --env-file .env.example down`. Los datos persisten en volúmenes de Docker; agregá `-v` para borrarlos.

`.env.example` trae valores de desarrollo listos para usar. Para personalizarlos, copialo como `.env` (está ignorado por Git), editalo y levantá con `docker compose up --build -d`. Las credenciales de ejemplo son solo para uso local; fuera de desarrollo configurá un `JWT_SECRET` aleatorio de al menos 32 caracteres. Las cuentas se configuran con `SEED_ADMIN_USERNAME`, `SEED_ADMIN_PASSWORD`, `SEED_CLIENT_USERNAME`, `SEED_CLIENT_PASSWORD` y `SEED_CLIENT_DNI`; el seed no reemplaza contraseñas de cuentas que ya existen.

### Si algo no arranca

| Síntoma | Causa y solución |
| --- | --- |
| `Set MYSQL_ROOT_PASSWORD in .env` | Falta el archivo de variables. Usá `--env-file .env.example` o creá el `.env`. |
| `port is already allocated` | Otro programa usa ese puerto (por ejemplo un MySQL local). Detenelo o cambiá el puerto publicado en `docker-compose.yml`. |
| `Unknown column` en Rental Service, o un error de migración en Vehicle Service | Quedaron volúmenes de una versión anterior. Borralos con `docker compose --env-file .env.example down -v` y volvé a levantar. |
| La interfaz abre pero muestra errores de conexión | El Gateway todavía arranca. Esperá unos segundos y revisá `docker compose --env-file .env.example logs api-gateway`. |

### Cómo probar los flujos asíncronos

Los registros simulados tienen datos fijos para poder reproducir cada caso:

| Patente | Registro policial | Titular en el registro | Vehículo propio (admin) | Incorporación externa (usuario `cliente`) |
| --- | --- | --- | --- | --- |
| `DEF456`, `AA123BB`, `ABC123` | Sin denuncia | `40999000` y `30123456` | `VALIDADO` | `DISPONIBLE` |
| `XYZ999` | Denunciada | `40999000` | `ROBADO` | `RECHAZADO` por patente |
| `XYZ111`, `XYZ123`, `ROBADA123` | Denunciada | Sin titular | `ROBADO` | `RECHAZADO` por ambas validaciones |
| Cualquier otra | Sin denuncia | Sin titular | `VALIDADO` | `RECHAZADO` por titularidad |

1. **Verificación:** como `admin`, en *Vehículos (ABM)*, registrá un vehículo con patente `XYZ999`. El alta responde enseguida con verificación `PENDIENTE`. Recargá el listado unos segundos después: figura `ROBADO`, y si intentás reservarlo la operación se rechaza.
2. **Vehículos externos:** como `cliente`, en *Mis vehículos*, registrá `DEF456`. El estado pasa a `DISPONIBLE` y el vehículo ya se puede reservar. Probá también con `XYZ999` y con una patente cualquiera para ver los rechazos.
3. **Mantenimiento:** creá una reserva y abrí *Mis Reservas*. Aparece `CONFIRMADA` con mantenimiento `PENDIENTE`; a los pocos segundos pasa a `REALIZADO`. Si la reserva empieza en menos de 24 horas, el resultado es `NO_REALIZADO`.

En http://localhost:15672 se ve la actividad de cada cola. Para seguir un flujo por consola:

```bash
docker compose --env-file .env.example logs -f verificacion-worker validador-patente validador-titularidad correlador-externos mantenimiento-worker
```

## Arquitectura

```mermaid
flowchart TB
    UI["Interfaz web<br/>React 19 + Vite"]
    GW["API Gateway<br/>Node.js · Express 5 · Apollo Server 5"]
    VS["Vehicle Service<br/>Python · gRPC"]
    CS["Customer Service<br/>Python · gRPC"]
    RS["Rental Service<br/>Python · gRPC"]
    VDB[("vehicle_db<br/>MySQL")]
    CDB[("customer_db<br/>MySQL")]
    RDB[("rental_db<br/>MySQL")]
    MQ{{"RabbitMQ<br/>exchange rentar.events"}}
    VW["verificacion-worker"]
    VP["validador-patente"]
    VT["validador-titularidad"]
    CE["correlador-externos"]
    MW["mantenimiento-worker"]

    UI -- "REST / GraphQL + JWT" --> GW
    GW -- gRPC --> VS
    GW -- gRPC --> CS
    GW -- gRPC --> RS
    RS -- "gRPC: operatividad" --> VS
    VS --- VDB
    CS --- CDB
    RS --- RDB
    VS <-- eventos --> MQ
    RS <-- eventos --> MQ
    MQ <-- eventos --> VW
    MQ <-- eventos --> VP
    MQ <-- eventos --> VT
    MQ <-- eventos --> CE
    MQ <-- eventos --> MW
    CE --- VDB
    MW --- RDB
```

- **La interfaz web solo habla con el API Gateway.** El Gateway valida el JWT y los permisos por rol, decide qué servicios intervienen y arma la respuesta. Nunca accede a las bases de datos de los servicios.
- **Cada servicio es dueño de su dominio y de su base de datos.** Las reglas de negocio viven en el servicio responsable. Rental Service guarda los IDs de cliente y vehículo sin claves foráneas entre servicios.
- **Las operaciones que necesitan varios servicios las coordina el Gateway.** Por ejemplo, para crear una reserva verifica en paralelo que el cliente exista y esté activo (Customer), que el vehículo esté activo y operativo (Vehicle) y que el período esté libre (Rental). Recién entonces pide a Rental Service que la cree; Rental vuelve a controlar la operatividad y el solapamiento, con un bloqueo por vehículo para cubrir solicitudes concurrentes.
- **Lo síncrono va por gRPC y lo asíncrono por eventos.** Usamos gRPC cuando el usuario necesita la respuesta para continuar (consultar, validar, reservar). Usamos eventos cuando el proceso puede completarse después sin bloquear al usuario (verificar una patente, validar un vehículo externo, procesar un mantenimiento).

| Componente | Tecnología | Puerto local |
| --- | --- | --- |
| Interfaz web | React 19, React Router 7, Vite 8 | `5173` |
| API Gateway | Node.js 22, Express 5, Apollo Server 5, `@grpc/grpc-js` | `5000` |
| Vehicle Service | Python 3.10, gRPC, SQLAlchemy, Alembic, pika | `50051` |
| Customer Service | Python 3.10, gRPC, SQLAlchemy, bcrypt | `50052` |
| Rental Service | Python 3.10, gRPC, SQLAlchemy, pika | `50053` |
| Workers | Python 3.10, pika | Sin puerto |
| Bases de datos | MySQL 8 (una por servicio) | Vehicle `3308`, Customer `3310`, Rental `3309` |
| Broker | RabbitMQ 3.13 (AMQP + panel de administración) | `5672` / `15672` |

## Funcionalidades

| # | Funcionalidad | Rol | Interfaz | Operación en el Gateway | Servicios |
| --- | --- | --- | --- | --- | --- |
| 1 | Gestión de vehículos (alta, modificación, baja lógica, consulta) | Administrador | REST | `GET/POST /api/vehiculos`, `GET/PUT/DELETE /api/vehiculos/{id}` | Vehicle |
| 2 | Consulta de disponibilidad por período y filtros | Cliente | GraphQL | `vehiculosDisponibles` | Vehicle + Rental |
| 3 | Gestión de clientes (alta, modificación, baja lógica, consulta) | Administrador | REST | `GET/POST /api/clientes`, `GET/PUT/DELETE /api/clientes/{id}` | Customer |
| 4 | Alta de reserva | Cliente | REST | `POST /api/reservas` | Customer + Vehicle + Rental |
| 5 | Consulta de reservas | Cliente / Administrador | GraphQL | `reservasPorCliente` | Rental + Customer + Vehicle |
| 6 | Cancelación de reserva | Cliente | REST | `PATCH /api/reservas/{id}/cancelar` | Rental |
| 7 | Historial de alquileres | Cliente | GraphQL | `historialReservas` | Rental + Vehicle |
| 8 | Incorporación de vehículos propios | Cliente | REST | `GET/POST /api/vehiculos-externos` | Customer + Vehicle + workers |

Reglas de negocio principales:

- Todo vehículo nuevo queda `DISPONIBLE`. La patente es única y no se puede modificar. Los estados del vehículo son `DISPONIBLE` y `EN_ALQUILER`.
- Vehículos y clientes se dan de baja de forma lógica: los inactivos no pueden participar de nuevos alquileres.
- Un vehículo denunciado como robado queda con `operativo = false`: no aparece disponible, no se puede reservar y no se puede volver a habilitar.
- Una reserva exige un cliente y un vehículo activos, una fecha de inicio futura, una fecha de fin posterior al inicio y un período sin otra reserva confirmada.
- El importe total es la cantidad de días de alquiler (redondeada hacia arriba) por el precio diario. La reserva se crea `CONFIRMADA`.
- Solo se puede cancelar una reserva que todavía no comenzó. Queda `CANCELADA` sin borrarse y libera el período.

## Eventos asíncronos

Todos los eventos circulan por el exchange `rentar.events` (tipo `topic`). Cada consumidor tiene su propia cola durable y los mensajes son persistentes: si un consumidor está detenido, los eventos lo esperan en la cola. Un mensaje que falla al procesarse va a la dead-letter queue `rentar.dlq`. El servicio `broker-init` declara toda la topología al levantar el stack, para que ningún evento se pierda si un consumidor todavía no arrancó.

| Proceso | Eventos | Resultado |
| --- | --- | --- |
| **Verificación de vehículos:** al registrar un vehículo, `verificacion-worker` consulta un registro policial simulado. | `vehiculos.verificacion.solicitada` → `vehiculos.verificacion.resultado` | `VALIDADO` o `ROBADO`. Vehicle Service guarda el resultado en `estado_verificacion` y, si es robado, pone `operativo = false`. No se agrega ningún estado operativo. |
| **Incorporación de vehículos externos:** un cliente registra un vehículo propio, que queda `PENDIENTE`. `validador-patente` y `validador-titularidad` trabajan de forma independiente y `correlador-externos` combina sus resultados por `vehiculoExternoId`. | `vehiculos.externos.registrados` → `...validacion.patente` + `...validacion.titularidad` → `...validacion.completada` | Con ambas validaciones aprobadas, Vehicle Service lo incorpora a la flota como `DISPONIBLE`. Con alguna rechazada, queda `RECHAZADO` y no se incorpora. |
| **Mantenimiento preventivo:** al confirmarse una reserva, `mantenimiento-worker` registra una solicitud en su propia tabla y simula el trabajo. | `reserva.confirmada` → `mantenimiento.resultado` | `REALIZADO` o `NO_REALIZADO`. Rental Service lo asocia a la reserva. La confirmación nunca espera este proceso. |

La estructura de cada evento está documentada en [docs/eventos/README.md](docs/eventos/README.md) y tipada en [docs/eventos/contratos.schema.json](docs/eventos/contratos.schema.json).

## Autenticación y permisos

`POST /api/auth/login` devuelve un JWT que la interfaz envía como `Authorization: Bearer <token>`. `POST /api/auth/logout` lo revoca en el Gateway. Los permisos se controlan en el backend, no solo en la interfaz:

- **`ADMIN`:** gestiona vehículos y clientes, consulta las reservas de cualquier cliente y el historial completo, y puede cancelar cualquier reserva.
- **`CLIENTE`:** consulta disponibilidad, crea reservas a su nombre, consulta y cancela solo las propias, e incorpora vehículos propios. Su identidad sale del token, no de datos enviados en la solicitud.
- Sin token válido, REST responde `401`; con un rol sin permiso, `403`. GraphQL informa los mismos códigos en `errors[].extensions`.

## Contratos gRPC

Los contratos están en `services/<servicio>/proto/<dominio>/v1/*.proto`. El Gateway los carga en tiempo de ejecución y cada servicio genera sus stubs Python al construir su imagen. Tienen comentarios en cada servicio, método, mensaje, campo y valor de enum, y cumplen las reglas `STANDARD` y `COMMENTS` de Buf Lint ([buf.yaml](buf.yaml)):

```bash
npx @bufbuild/buf lint
```

- **Mensajes exclusivos:** cada RPC tiene su propio `<Metodo>Request` y `<Metodo>Response` (regla `RPC_REQUEST_RESPONSE_UNIQUE`). Las entidades (`Vehiculo`, `Cliente`, `Renta`) van dentro de la respuesta.
- **Nomenclatura:** los servicios mantienen el nombre del enunciado (`VehicleService`, `CustomerService`, `RentalService`). Métodos, mensajes, campos y enums usan el vocabulario del dominio en español, con campos en `lower_snake_case`.
- **Fechas:** `google.protobuf.Timestamp` (instante UTC). Rental Service las guarda como ISO-8601 UTC con milisegundos, así la comparación de solapamiento respeta el orden cronológico.
- **Enums:** `TipoVehiculo`, `EstadoVehiculo`, `EstadoRenta`, `EstadoIncorporacion` y `Rol`. El valor `0` es `*_UNSPECIFIED` y los servicios lo rechazan con `INVALID_ARGUMENT`. El Gateway traduce entre `TIPO_VEHICULO_SEDAN` y el valor de dominio `SEDAN` ([src/grpc/enums.js](src/grpc/enums.js)).
- **Reglas en el contrato:** `CrearVehiculoRequest` no tiene `estado` (todo vehículo nuevo queda `DISPONIBLE`) y `ActualizarVehiculoRequest` no tiene `patente` (no es modificable).

## Pruebas

Sin levantar el stack (requiere Node.js y `npm install`):

```bash
npm test                              # sintaxis del Gateway + pruebas unitarias de JWT
npx @bufbuild/buf lint                # contratos gRPC
npm --prefix front/mi-app run lint
npm --prefix front/mi-app run build
```

Con el stack levantado. Las pruebas de Customer y Rental incluyen integración contra el servidor gRPC y su base:

```bash
docker compose --env-file .env.example exec vehicle-service python -m unittest discover -s /app/tests
docker compose --env-file .env.example exec customer-service python -m pytest /app/tests/test_customer_service.py
docker compose --env-file .env.example exec rental-service python -m pytest /app/tests
```

Broker de eventos:

```bash
docker compose --env-file .env.example run --rm --entrypoint python broker-init smoke_test.py
docker compose --env-file .env.example exec vehicle-service python -m app.smoke_broker
```

En el panel de RabbitMQ tienen que verse el exchange `rentar.events`, el DLX `rentar.dlx`, la cola `rentar.dlq` y las 9 colas de consumidores.

## Estructura del repositorio

```text
front/mi-app/                 Interfaz web React + Vite
src/                          API Gateway
  routes/ controllers/          Endpoints REST
  graphql/                      Schema y resolvers GraphQL
  grpc/                         Clientes gRPC de los tres servicios
  orchestrators/                Coordinación de operaciones entre servicios (alta de reserva)
  auth/                         JWT y control de roles
  messaging/                    Helper de RabbitMQ para Node.js
services/
  vehicle-service/              Vehículos e incorporaciones: gRPC + vehicle_db + Alembic + eventos
  customer-service/             Clientes y cuentas: gRPC + customer_db + autenticación
  rental-service/               Reservas: gRPC + rental_db + eventos + worker de mantenimiento
workers/
  common/                       Topología del broker, helpers y registro policial simulado
  verificacion_worker.py        Verificación de patentes de vehículos propios
  validador_patente_worker.py   Validación de patente de vehículos externos
  validador_titularidad_worker.py  Validación de titularidad contra el registro simulado
  correlador_externos_worker.py Correlación de resultados de la incorporación
docs/
  GRAPHQL.md                    Tipos, operaciones, permisos y errores de GraphQL
  eventos/                      Contratos de los eventos del Hito 3
buf.yaml                      Configuración de Buf Lint para los contratos gRPC
docker-compose.yml            Stack completo: bases, broker, servicios, workers, Gateway e interfaz
prisma/schema.prisma          Modelo de datos del Hito 1 (referencia histórica, sin uso actual)
```

## Documentación

- **REST:** Swagger en http://localhost:5000/api-docs ([src/config/swagger.js](src/config/swagger.js)).
- **GraphQL:** [docs/GRAPHQL.md](docs/GRAPHQL.md) y la introspección del endpoint `/graphql`.
- **gRPC:** comentarios en los `.proto` de cada servicio.
- **Eventos:** [docs/eventos/README.md](docs/eventos/README.md).

## Equipo

| Integrante | GitHub |
| --- | --- |
| Alejo Daniel Almirón | [@alejoalmiron](https://github.com/alejoalmiron) |
| Gabriel Omar Romero | [@GabrielOmarRomero](https://github.com/GabrielOmarRomero) |
| Juan Cruz Lendoiro Quiroga | [@JuanCruzLendoiro](https://github.com/JuanCruzLendoiro) |
| Brian Avila | [@BrianAvila-UNLA](https://github.com/BrianAvila-UNLA) |
| Tomás Palma | [@ttomi03](https://github.com/ttomi03) |
