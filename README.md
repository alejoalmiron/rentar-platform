# 🚗 Rentar - Sistema de Alquiler de Vehículos (API Gateway, REST, GraphQL & gRPC)

Proyecto desarrollado para el **Hito 2** de la materia **Desarrollo de Software en Sistemas Distribuidos (UNLa)**. A partir del sistema desarrollado en el Hito 1, se incorpora una arquitectura basada en servicios independientes y comunicación mediante **gRPC**, manteniendo las funcionalidades desarrolladas anteriormente.

La interfaz web desarrollada en el Hito 1 se mantiene como medio de acceso al sistema. El **API Gateway**, desarrollado en Node.js, funciona como punto de entrada y se comunica mediante gRPC con los servicios internos de Vehículos, Clientes y Alquileres.

---

## 🛠️ Requisitos Previos

Antes de comenzar, asegurate de tener instalado en tu equipo:

* **Node.js** (Versión LTS v18 o superior)
* **Python** (v3.10 o superior)
* **MySQL Server** (v8.0+) o gestor local como MySQL Workbench / XAMPP
* **Git** y **Visual Studio Code**
* **Docker** y **Docker Compose**

---

## 🚀 Guía de Instalación y Configuración Local

El proyecto está compuesto por el API Gateway en Node.js, tres servicios internos en Python y el frontend existente en React.

### 1. Clonar el repositorio e instalar dependencias

* git clone <LINK_DEL_REPOSITORIO>
* cd rentar-backend
* npm install

Para los servicios Python, instalar las dependencias correspondientes dentro de cada servicio:

* cd services/vehicle-service
* pip install -r requirements.txt

El mismo procedimiento se utiliza para `customer-service` y `rental-service`.

### 2. Configurar las variables de entorno

El API Gateway utiliza variables de entorno para conocer las direcciones de los servicios gRPC.

Ejemplo:

* PORT=5000
* VEHICLE_GRPC_URL=localhost:50051
* CUSTOMER_GRPC_URL=localhost:50052
* RENTAL_GRPC_URL=localhost:50053

Cada servicio Python tendrá su propio archivo `.env` con la configuración necesaria para conectarse a su base de datos.

### 3. Crear las bases de datos en MySQL

Cada servicio cuenta con una base de datos independiente:

* `vehicle_db`
* `customer_db`
* `rental_db`

Por ejemplo:

```sql
CREATE DATABASE vehicle_db;
CREATE DATABASE customer_db;
CREATE DATABASE rental_db;
```

Cada servicio es responsable de sus propias tablas y migraciones.

### 4. Ejecutar las migraciones

Las migraciones se encuentran dentro de cada servicio:

* `services/vehicle-service/migrations/`
* `services/customer-service/migrations/`
* `services/rental-service/migrations/`

Cada servicio debe ejecutar sus propias migraciones sobre su respectiva base de datos.

### 5. Iniciar el sistema

`docker-compose.yml` levanta las bases y servicios de Alquileres y Vehículos. Cada microservicio usa su propio contenedor MySQL: Alquileres publica MySQL en `localhost:3307` y Vehículos en `localhost:3308`. Para iniciar esos servicios:

```powershell
docker compose up --build -d db rental-service vehicle-db vehicle-service
```

Vehículos espera a que su base de datos esté lista y expone gRPC en `localhost:50051`. Para detener los contenedores:

```bash
docker compose down
```

El API Gateway se ejecuta desde otra terminal en la raíz del proyecto. Configurá en `.env` `VEHICLE_GRPC_ADDRESS=localhost:50051` y luego iniciá:

```powershell
npm.cmd run dev
```

El Gateway queda disponible en `http://localhost:5000` y reenvía las operaciones REST de vehículos a su servicio gRPC. El contrato que utiliza el Gateway es el de `services/vehicle-service/proto/vehicle/v1/vehicle.proto`; las propiedades disponibles son `id`, `marca`, `modelo`, `patente`, `operativo` y `activo`.

Para ejecutar el servicio de Vehículos directamente en Windows, primero configurá `DATABASE_URL` en `services/vehicle-service/.env` para apuntar a una instancia de MySQL disponible y luego, desde `services/vehicle-service`, ejecutá:

```powershell
.\venv\Scripts\python.exe -m app.server
```

---

## 📁 Arquitectura del Proyecto Backend

La estructura general del proyecto queda organizada de la siguiente manera:

```text
rentar-backend/
├── src/                              # API Gateway existente (Node.js)
│   ├── index.js
│   ├── routes/                       # Rutas REST que usa el frontend
│   ├── controllers/                  # Adaptados para utilizar gRPC
│   ├── graphql/                      # Resolvers adaptados para utilizar gRPC
│   ├── grpc/                         # Clientes gRPC
│   │   ├── vehicle.client.js
│   │   ├── customer.client.js
│   │   └── rental.client.js
│   ├── orchestrators/                # Coordinación de operaciones
│   │   └── reserva.orchestrator.js
│   └── config/
│       └── grpc.js                   # Direcciones de los servicios
│
├── proto/                            # Contratos compartidos
│   ├── vehicle/v1/vehicle.proto
│   ├── customer/v1/customer.proto
│   └── rental/v1/rental.proto
│
├── services/                         # Microservicios Python
│   ├── vehicle-service/
│   ├── customer-service/
│   └── rental-service/
│
├── front/
│   └── mi-app/                       # Frontend React existente
│
├── docker-compose.yml
├── .env.example
└── README.md
```

Cada servicio Python tendrá una estructura similar:

```text
services/vehicle-service/
├── app/
│   ├── server.py                     # Inicia el servidor gRPC
│   ├── service.py                    # Implementa operaciones del dominio
│   ├── repository.py                 # Acceso a su propia base MySQL
│   ├── db.py                         # Conexión y sesión de base de datos
│   └── generated/                    # Código generado desde vehicle.proto
├── migrations/                       # Migraciones Alembic
├── tests/
├── requirements.txt
├── Dockerfile
└── .env.example
```

Para `customer-service` y `rental-service` se replica la misma estructura, utilizando sus respectivos contratos `.proto`.

---

## 👥 Distribución y Módulos de Trabajo

### 📌 Integrante 1 — API Gateway en Node.js

**Modificar y crear dentro de `src`:**

* Modificar `vehiculo.controller.js`, `cliente.controller.js` y `reserva.controller.js` para que dejen de consultar Prisma y deleguen las operaciones al cliente gRPC correspondiente.
* Crear `src/grpc/vehicle.client.js`.
* Crear `src/grpc/customer.client.js`.
* Crear `src/grpc/rental.client.js`.
* Crear `src/config/grpc.js` para leer de variables de entorno las direcciones de los servicios.
* Crear `src/orchestrators/reserva.orchestrator.js` para coordinar las validaciones y el alta de reserva.
* Modificar `resolvers.js` para llamar a los servicios por gRPC, no directamente a Prisma.
* Mantener en `index.js` el montaje de REST/GraphQL como entrada para el frontend.

**Operaciones que debe coordinar al crear una reserva:**

* Consultar en paralelo si el cliente está activo.
* Consultar si el vehículo está operativo.
* Consultar si las fechas están libres.
* Si todas las validaciones son correctas, pedir la creación de la reserva al Rental Service.

**No debe hacer:**

* Acceder directamente a MySQL.
* Implementar reglas internas de clientes, vehículos o alquileres.

---

### 📌 Integrante 2 — Vehicle Service en Python

**Crear dentro de `services/vehicle-service/`:**

* `app/server.py`
* `app/service.py`
* `app/repository.py`
* `app/db.py`
* `requirements.txt`
* `Dockerfile`
* `.env.example`
* `migrations/`
* `tests/`
* `proto/vehicle/v1/vehicle.proto`

**El servicio debe incluir operaciones para:**

* Listar vehículos y consultar un vehículo por ID.
* Crear vehículos.
* Modificar vehículos.
* Dar de baja vehículos, para conservar la gestión del Hito 1.
* Consultar si un vehículo está operativo.
* Validar los datos propios del vehículo.

**Base de datos:**

El servicio utiliza una base MySQL propia:

```text
vehicle_db
```

El Vehicle Service administra sus propias tablas y migraciones.

---

### 📌 Integrante 3 — Customer Service en Python

**Crear dentro de `services/customer-service/`:**

* `app/server.py`
* `app/service.py`
* `app/repository.py`
* `app/db.py`
* `requirements.txt`
* `Dockerfile`
* `.env.example`
* `migrations/`
* `tests/`
* `proto/customer/v1/customer.proto`

**El servicio debe incluir operaciones para:**

* Listar clientes y consultar un cliente por ID.
* Crear clientes.
* Modificar clientes.
* Dar de baja clientes, para conservar la gestión del Hito 1.
* Verificar que un cliente exista y esté activo.
* Validar datos propios del cliente, como documento/DNI único y campos obligatorios.

**Base de datos:**

El servicio utiliza una base MySQL propia:

```text
customer_db
```

El Customer Service administra sus propias tablas y migraciones.

El Gateway debe poder invocar la validación de cliente activo antes de solicitar una reserva.

---

### 📌 Integrante 4 — Rental Service en Python

**Crear dentro de `services/rental-service/`:**

* `app/server.py`
* `app/service.py`
* `app/repository.py`
* `app/db.py`
* `requirements.txt`
* `Dockerfile`
* `.env.example`
* `migrations/`
* `tests/`
* `proto/rental/v1/rental.proto`

**El servicio debe incluir operaciones para:**

* Crear reservas.
* Consultar reservas.
* Listar reservas por cliente.
* Cancelar una reserva.
* Consultar el historial de alquileres.
* Verificar si existen reservas que se superponen con un vehículo y un período.

**Base de datos:**

El servicio utiliza una base MySQL propia:

```text
rental_db
```

El Rental Service administra sus propias tablas y migraciones.

El Rental Service debe volver a verificar los solapamientos al guardar la reserva, aunque el Gateway ya haya consultado la disponibilidad.

---

### 📌 Integrante 5 — Frontend, Integración y Documentación

**Modificar y crear:**

* Revisar `ConectarAlBackend.js` para que todas las llamadas utilicen el API Gateway.
* Revisar las páginas de `pages` y mantener los flujos existentes:

  * Vehículos.
  * Clientes.
  * Disponibilidad.
  * Alta de reservas.
  * Consulta de reservas.
  * Cancelación.
  * Historial de alquileres.
* Crear `docker-compose.yml` en la raíz para levantar el Gateway, los tres servicios y MySQL.
* Actualizar `README.md` con arquitectura, requisitos, variables y pasos para ejecutar el sistema.
* Preparar el documento de entrega con diagramas, integrantes, tareas, pruebas y capturas.

El integrante 5 coordina las pruebas integrales, pero cada responsable debe escribir y ejecutar las pruebas de su propio componente.

---

## 🔗 Contratos gRPC

Los contratos gRPC se encuentran únicamente dentro de `proto/`:

```text
proto/
├── vehicle/v1/vehicle.proto
├── customer/v1/customer.proto
└── rental/v1/rental.proto
```

Cada contrato define los servicios, métodos, mensajes de entrada y respuestas correspondientes.

Los servicios utilizan estos contratos para implementar la comunicación entre el API Gateway y los servicios internos.

El código necesario para ejecutar los contratos se genera dentro de cada servicio, en `app/generated/`.

---

## ⚡ Flujo de Alta de Reserva

La creación de una reserva requiere la participación del API Gateway, Customer Service, Vehicle Service y Rental Service.

```text
Frontend
   │
   │ Solicitud de reserva
   ▼
API Gateway
   │
   ├──────────────► Customer Service
   │                    │
   │                    └── Cliente activo
   │
   └──────────────► Vehicle Service
                        │
                        ├── Vehículo operativo
                        └── Fechas disponibles

              │
              │ Datos validados
              ▼
         API Gateway
              │
              │ Crear reserva
              ▼
        Rental Service
              │
              ▼
        Reserva guardada
```

El Gateway realiza las consultas al Customer Service y al Vehicle Service en paralelo.

Si alguna validación falla, la solicitud es rechazada.

Si todas las validaciones son correctas, el Gateway solicita al Rental Service la creación de la reserva.

El Rental Service vuelve a verificar los solapamientos antes de guardar la reserva.

---

## ⚛️ Guía para el Integrante 5 — Frontend (React + Vite)

El Frontend desarrollado en el Hito 1 se mantiene y continúa siendo el medio de acceso al sistema.

La diferencia es que ahora todas las solicitudes deben pasar por el API Gateway.

### 1. Conexión con el Backend

* Base URL de la API REST: `http://localhost:5000/api`
* Endpoint de GraphQL: `http://localhost:5000/graphql`

El frontend no debe comunicarse directamente con Vehicle Service, Customer Service ni Rental Service.

### 2. Tareas a desarrollar en React

* Mantener las vistas existentes de vehículos y clientes.
* Mantener el formulario de alta de reservas.
* Mantener la consulta de disponibilidad.
* Mantener la consulta de reservas.
* Mantener la cancelación de reservas.
* Mantener el historial de alquileres.
* Revisar `ConectarAlBackend.js` para garantizar que todas las llamadas utilicen el Gateway.

---

## 🗄️ Bases de Datos

A diferencia del Hito 1, las bases de datos se separan por servicio:

| Servicio         | Base de datos |
| ---------------- | ------------- |
| Vehicle Service  | `vehicle_db`  |
| Customer Service | `customer_db` |
| Rental Service   | `rental_db`   |

Cada servicio accede únicamente a su propia base de datos.

El API Gateway no accede directamente a MySQL.

El esquema Prisma utilizado en el Hito 1 puede conservarse como referencia durante la migración, pero no debe continuar funcionando como una base de datos compartida entre los servicios.

---

## 📋 Criterios Comunes

* **Lenguajes:** API Gateway en Node.js; los tres servicios internos en Python.
* **Bases de datos:** MySQL con `vehicle_db`, `customer_db` y `rental_db`.
* **Acceso a datos:** cada servicio accede únicamente a su propia base de datos.
* **Contratos:** los archivos `.proto` se guardan en `proto/`.
* **Código generado:** cada servicio genera o utiliza los archivos necesarios dentro de `app/generated/`.
* **Disponibilidad:** Vehicle Service informa si el vehículo está operativo y Rental Service informa si las fechas están libres.
* **Coordinación:** el Gateway combina las respuestas necesarias para completar una operación.
* **Fechas e identificadores:** conservar el tipo de ID utilizado actualmente y utilizar fechas en UTC en los contratos.
* **Estados:** revisar los enums actuales de `schema.prisma` antes de definirlos en los `.proto`, evitando crear estados incompatibles.
* **Pruebas finales:** demostrar desde la interfaz que las siete funciones del Hito 1 continúan funcionando a través del API Gateway.

---

## 🧪 Pruebas

Se deben comprobar las funcionalidades desarrolladas en el Hito 1 utilizando la nueva arquitectura:

* Gestión de vehículos.
* Consulta de disponibilidad.
* Gestión de clientes.
* Alta de reservas.
* Consulta de reservas.
* Cancelación de reservas.
* Historial de alquileres.

Además, se debe verificar la comunicación mediante gRPC entre el API Gateway y cada uno de los servicios internos.

Las pruebas realizadas y sus respectivas capturas forman parte de la entrega del trabajo práctico.
