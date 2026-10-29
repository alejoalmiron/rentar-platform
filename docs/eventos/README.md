# Contratos de eventos — Rentar (Hito 3)

Documentación de los eventos que circulan por el broker **RabbitMQ**. Este archivo es la fuente de verdad: productores y consumidores deben respetar estos nombres y estructuras.

## Infraestructura

| Elemento | Valor |
| --- | --- |
| Broker | RabbitMQ 3.13 (imagen `rabbitmq:3.13-management`) |
| Exchange principal | `rentar.events` (tipo `topic`, durable) |
| Dead-letter exchange | `rentar.dlx` (tipo `fanout`, durable) |
| Dead-letter queue | `rentar.dlq` (recibe mensajes rechazados) |
| Panel de administración | `http://localhost:15672` (usuario/clave de `RABBITMQ_USER` / `RABBITMQ_PASS`) |
| Puerto AMQP | `5672` |
| Conexión servicios | variable de entorno `RABBITMQ_URL` |

Las colas son durables y los mensajes persistentes. Cada componente consumidor tiene **su propia cola** bindeada al exchange con la routing key del evento; si dos workers necesitan el mismo evento, cada uno declara una cola distinta. Un mensaje cuyo procesamiento lanza excepción se rechaza sin requeue y cae en `rentar.dlq`.

Los nombres de routing key y de colas están centralizados en `workers/common/topology.py`. Al levantar el stack, el servicio `broker-init` declara exchange, DLQ y todas las colas para que los mensajes no se pierdan si un worker todavía no arrancó.

Los tipos y campos requeridos de cada payload están en [contratos.schema.json](contratos.schema.json).

## Eventos

### 1. `vehiculos.verificacion.solicitada`

Solicita verificar una patente contra el registro de vehículos denunciados.

| | |
| --- | --- |
| **Productor** | Vehicle Service (al registrar un vehículo) |
| **Consumidor** | Worker verificador de patentes (cola `verificador_patentes.solicitudes`) |

```json
{
  "vehiculoId": 15,
  "patente": "ABC123"
}
```

### 2. `vehiculos.verificacion.resultado`

Informa el resultado de la verificación de patente.

| | |
| --- | --- |
| **Productor** | Worker verificador de patentes |
| **Consumidor** | Vehicle Service (cola `vehicle_service.verificacion_resultados`) |

```json
{
  "vehiculoId": 15,
  "patente": "ABC123",
  "resultado": "VALIDADO"
}
```

`resultado`: `VALIDADO` | `ROBADO`. Si es `ROBADO`, el vehículo queda inhabilitado para nuevas operaciones (sin crear un estado operativo nuevo).

### 3. `vehiculos.externos.registrados`

Un cliente registró un vehículo propio para incorporarlo al sistema (comienza en `PENDIENTE`).

| | |
| --- | --- |
| **Productor** | Vehicle Service |
| **Consumidores** | Worker validador de patente (cola `validador_patente.registros`) y worker validador de titularidad (cola `validador_titularidad.registros`), de forma independiente |

```json
{
  "vehiculoExternoId": 50,
  "clienteId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "patente": "DEF456"
}
```

### 4. `vehiculos.externos.validacion.patente`

Resultado de la validación de patente del vehículo externo.

| | |
| --- | --- |
| **Productor** | Worker validador de patente |
| **Consumidor** | Correlador de incorporaciones (cola `correlador_externos.resultados_patente`) |

```json
{
  "vehiculoExternoId": 50,
  "patente": "DEF456",
  "resultado": "VALIDADO"
}
```

### 5. `vehiculos.externos.validacion.titularidad`

Resultado de la validación de titularidad (el cliente es titular del vehículo).

| | |
| --- | --- |
| **Productor** | Worker validador de titularidad |
| **Consumidor** | Correlador de incorporaciones (cola `correlador_externos.resultados_titularidad`) |

```json
{
  "vehiculoExternoId": 50,
  "clienteId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "documento": "30123456",
  "patente": "DEF456",
  "resultado": "VALIDADO"
}
```

### 6. `vehiculos.externos.validacion.completada`

Todas las validaciones de la incorporación resultaron `VALIDADO`.

| | |
| --- | --- |
| **Productor** | Correlador de incorporaciones |
| **Consumidor** | Vehicle Service (cola `vehicle_service.incorporaciones_completadas`): pasa el vehículo a `DISPONIBLE` |

```json
{
  "vehiculoExternoId": 50
}
```

Si alguna validación es `RECHAZADO`, este evento **no se emite** y el vehículo no se incorpora.

### 7. `reserva.confirmada`

Una reserva quedó confirmada. La confirmación **no espera** al mantenimiento (fire-and-forget).

| | |
| --- | --- |
| **Productor** | Rental Service (al confirmar la reserva) |
| **Consumidor** | Worker de mantenimiento preventivo (cola `mantenimiento.reservas_confirmadas`) |

```json
{
  "reservaId": 150,
  "vehiculoId": 15,
  "fechaInicio": "2026-10-10T10:00:00",
  "fechaFin": "2026-10-15T10:00:00"
}
```

### 8. `mantenimiento.resultado`

Resultado del mantenimiento preventivo asociado a la reserva.

| | |
| --- | --- |
| **Productor** | Worker de mantenimiento preventivo |
| **Consumidor** | Rental Service (cola `rental_service.mantenimiento_resultados`): registra el resultado asociado a la reserva |

```json
{
  "reservaId": 150,
  "vehiculoId": 15,
  "resultado": "REALIZADO"
}
```

`resultado`: `REALIZADO` | `NO_REALIZADO`.

## Convenciones

- **Formato:** JSON UTF-8, `content-type: application/json`, entrega persistente.
- **Fechas:** ISO-8601 (`YYYY-MM-DDTHH:mm:ss`).
- **Correlación:** los eventos de un mismo proceso comparten el identificador del agregado (`vehiculoId`, `vehiculoExternoId` o `reservaId`).
- **Identificadores:** numéricos para entidades del dominio interno (`vehiculoId`, `reservaId`); `clienteId` conserva el UUID/string del Customer Service.
- **Helpers:** Python → `workers/common/messaging.py` (workers) y `app/messaging.py` dentro de cada servicio; Node → `src/messaging/rabbitmq.js`. Todos implementan conexión con reintentos, publicación y consumo con ack/nack a DLQ.
- **Declaración de topología:** `python workers/common/declare_topology.py` o `docker compose run --rm broker-init`.
- **Schemas:** [contratos.schema.json](contratos.schema.json). Productores deben respetar `required` y los `enum` de `resultado`.

## Cómo usan esto los demás integrantes

Los flujos de negocio (verificación de patentes, saga de vehículos externos, mantenimiento) **no** se implementan acá. Cada integrante escribe productores/consumidores contra estos contratos:

| Integrante | Publica | Consume |
| --- | --- | --- |
| 2 — Verificación de patentes | `vehiculos.verificacion.solicitada`, `vehiculos.verificacion.resultado` | Vehicle: resultados; worker verificador: solicitudes |
| 3 — Incorporación externa | `vehiculos.externos.registrados`, validaciones parciales, `...completada` | validadores + correlador + Vehicle |
| 4 — Mantenimiento | `reserva.confirmada`, `mantenimiento.resultado` | worker mantenimiento + Rental |

Pruebas E2E de cada flujo (cuando existan los workers):

1. Verificar en `http://localhost:15672` que existen `rentar.events`, `rentar.dlx`, `rentar.dlq` y las 9 colas de consumidores.
2. Disparar el caso de negocio y confirmar que el mensaje llega a la cola correcta (Ready/Unacked).
3. Caso feliz y caso de rechazo/DLQ (handler que lanza excepción → mensaje en `rentar.dlq`).
4. En mantenimiento: la confirmación de reserva responde sin esperar `mantenimiento.resultado`.
