# API GraphQL de Rentar

## Acceso y autenticación

El endpoint es `POST http://localhost:5000/graphql`. Primero se inicia sesión en `POST /api/auth/login` con `username` y `password`. La respuesta contiene un JWT. En cada petición GraphQL protegida se envía:

```http
Authorization: Bearer <token>
Content-Type: application/json
```

Los roles reconocidos son `ADMIN` y `CLIENTE`. El Gateway valida la firma y vencimiento del JWT. El administrador consulta el historial completo y puede cancelar cualquier reserva. El cliente solo consulta/cancela las propias; el servicio deriva su identidad del token, no de un DNI enviado por el usuario.

## Tipos

### `Vehiculo`

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `id` | `ID!` | Identificador asignado por Vehicle Service. |
| `patente` | `String!` | Patente única. |
| `marca` | `String!` | Marca. |
| `modelo` | `String!` | Modelo. |
| `anio` | `Int!` | Año de fabricación. |
| `color` | `String` | Color opcional. |
| `tipo` | `TipoVehiculo!` | Categoría. |
| `precioDiario` | `Float!` | Precio diario. |
| `estado` | `EstadoVehiculo!` | Estado registrado. |
| `activo` | `Boolean!` | Estado lógico del registro. |

### `Cliente`

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `id` | `ID!` | Identificador en Customer Service. |
| `dni` | `String!` | Documento nacional. |
| `nombre` | `String!` | Nombre. |
| `apellido` | `String!` | Apellido. |
| `email` | `String!` | Correo. |
| `telefono` | `String` | Teléfono opcional. |

### `Reserva`

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `id` | `ID!` | Identificador de la reserva. |
| `fechaInicio`, `fechaFin` | `String!` | Fechas ISO-8601. |
| `estado` | `EstadoReserva!` | Estado de la reserva. |
| `montoTotal` | `Float!` | Importe calculado por Rental Service. |
| `cliente` | `Cliente` | Cliente asociado; `null` si el registro ya no existe en Customer Service. |
| `vehiculo` | `Vehiculo` | Vehículo asociado; `null` si el registro ya no existe en Vehicle Service. |

### Enums

- `TipoVehiculo`: `SEDAN`, `SUV`, `PICKUP`, `COUPE`, `HATCHBACK`.
- `EstadoVehiculo`: `DISPONIBLE`, `EN_ALQUILER`.
- `EstadoReserva`: `CONFIRMADA`, `CANCELADA`, `FINALIZADA`.

No hay tipos `input` GraphQL: las operaciones reciben argumentos escalares. Las fechas se envían como `String` ISO-8601 y los importes como `Float`.

## Queries

### `vehiculosDisponibles`

Busca vehículos activos y operativos, y comprueba que no tengan reservas superpuestas para el período. Disponible para ambos roles autenticados.

| Argumento | Tipo | Requerido | Validación |
| --- | --- | --- | --- |
| `fechaInicio` | `String!` | Sí | Fecha ISO-8601 válida y futura. |
| `fechaFin` | `String!` | Sí | ISO-8601 válida, posterior al inicio. |
| `tipo` | `String` | No | Valor admitido por el servicio de vehículos. |
| `marca` | `String` | No | Filtro exacto en la implementación actual. |
| `modelo` | `String` | No | Filtro exacto en la implementación actual. |
| `precioMin` | `Float` | No | Límite inferior inclusivo. |
| `precioMax` | `Float` | No | Límite superior inclusivo. |

Request:

```json
{
  "query": "query Disponibles($inicio: String!, $fin: String!) { vehiculosDisponibles(fechaInicio: $inicio, fechaFin: $fin) { id patente marca modelo anio precioDiario estado } }",
  "variables": { "inicio": "2030-01-10T00:00:00Z", "fin": "2030-01-13T00:00:00Z" }
}
```

Response:

```json
{
  "data": {
    "vehiculosDisponibles": [
      { "id": "1", "patente": "AA123BC", "marca": "Toyota", "modelo": "Corolla", "anio": 2024, "precioDiario": 45000, "estado": "DISPONIBLE" }
    ]
  }
}
```

### `reservasPorCliente`

Devuelve reservas del cliente indicado. El rol `ADMIN` debe proporcionar `dni`; para `CLIENTE`, `dni` es opcional y el Gateway fuerza la identidad del token. Si el cliente envía un DNI distinto del propio, la operación se rechaza.

| Argumento | Tipo | Requerido | Validación |
| --- | --- | --- | --- |
| `dni` | `String` | Admin: sí; Cliente: no | Debe existir y pertenecer al usuario autorizado. |

Request de cliente:

```json
{
  "query": "query MisReservas { reservasPorCliente { id fechaInicio fechaFin estado montoTotal vehiculo { patente marca modelo } } }"
}
```

Response:

```json
{
  "data": {
    "reservasPorCliente": [
      { "id": "r-123", "fechaInicio": "2030-01-10T00:00:00Z", "fechaFin": "2030-01-13T00:00:00Z", "estado": "CONFIRMADA", "montoTotal": 135000, "vehiculo": { "patente": "AA123BC", "marca": "Toyota", "modelo": "Corolla" } }
    ]
  }
}
```

### `historialReservas`

Devuelve el historial completo para `ADMIN`; para `CLIENTE`, el Gateway fuerza el filtro al cliente autenticado. `estado` y `patente` se pueden combinar.

| Argumento | Tipo | Requerido | Validación |
| --- | --- | --- | --- |
| `estado` | `String` | No | Se compara con el estado de la reserva. |
| `patente` | `String` | No | Se compara con la patente del vehículo. |

Request:

```json
{
  "query": "query Historial($estado: String, $patente: String) { historialReservas(estado: $estado, patente: $patente) { id estado montoTotal cliente { dni nombre apellido } vehiculo { patente marca modelo } } }",
  "variables": { "estado": "FINALIZADA", "patente": "AA123BC" }
}
```

Response: `data.historialReservas` es una lista de objetos `Reserva` con los campos seleccionados. Si no hay coincidencias, devuelve una lista vacía.

## Mutation

### `cancelarReserva`

Cancela una reserva. `ADMIN` puede cancelar cualquier reserva; `CLIENTE` solo una propia. Rental Service rechaza reservas ya canceladas o cuyo período ya comenzó.

| Argumento | Tipo | Requerido | Validación |
| --- | --- | --- | --- |
| `id` | `ID!` | Sí | Debe identificar una reserva existente y cancelable. |

Request:

```json
{
  "query": "mutation Cancelar($id: ID!) { cancelarReserva(id: $id) { id estado montoTotal } }",
  "variables": { "id": "r-123" }
}
```

Response:

```json
{ "data": { "cancelarReserva": { "id": "r-123", "estado": "CANCELADA", "montoTotal": 135000 } } }
```

## Errores y validaciones

GraphQL puede devolver HTTP 200 con un arreglo `errors`; los errores incluyen `message` y `extensions.code`. Para errores de autenticación/autorización, Apollo además usa el status HTTP correspondiente (401/403). El frontend debe comprobar `errors`, no solo el estado HTTP.

| Código | HTTP | Causa |
| --- | ---: | --- |
| `UNAUTHENTICATED` | 401 | Falta token, es inválido, venció o fue revocado. |
| `PERMISSION_DENIED` | 403 | El rol/usuario no puede acceder a ese recurso. |
| `INVALID_ARGUMENT` | 400 | Fechas, filtros o argumentos inválidos. |
| `NOT_FOUND` | 404 | Cliente, vehículo o reserva inexistente. |
| `ALREADY_EXISTS` | 409 | Solapamiento o dato duplicado. |
| `FAILED_PRECONDITION` | 409 | Reserva ya iniciada o cancelada. |
| `UNAVAILABLE` | 503 | Servicio gRPC no disponible o no se cargó su contrato. |
| `DEADLINE_EXCEEDED` | 504 | El servicio interno superó el timeout del Gateway. |

Validaciones adicionales: Customer Service exige cliente activo; Vehicle Service exige vehículo activo y operativo; Rental Service valida período, controla solapamientos al confirmar y calcula el importe. Una respuesta de error se representa así:

```json
{
  "errors": [
    {
      "message": "Solo podés consultar tus propias reservas",
      "extensions": { "code": "PERMISSION_DENIED" }
    }
  ],
  "data": null
}
```