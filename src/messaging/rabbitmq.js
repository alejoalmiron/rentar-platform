import amqp from 'amqplib';

// Topologia compartida con workers/common/topology.py (fuente de verdad).
export const EXCHANGE = 'rentar.events';
export const DLX_EXCHANGE = 'rentar.dlx';
export const DLQ = 'rentar.dlq';
export const EVENTOS = {
  VEHICULO_VERIFICACION_SOLICITADA: 'vehiculos.verificacion.solicitada',
  VEHICULO_VERIFICACION_RESULTADO: 'vehiculos.verificacion.resultado',
  VEHICULO_EXTERNO_REGISTRADO: 'vehiculos.externos.registrados',
  VEHICULO_EXTERNO_VALIDACION_PATENTE: 'vehiculos.externos.validacion.patente',
  VEHICULO_EXTERNO_VALIDACION_TITULARIDAD: 'vehiculos.externos.validacion.titularidad',
  VEHICULO_EXTERNO_VALIDACION_COMPLETADA: 'vehiculos.externos.validacion.completada',
  RESERVA_CONFIRMADA: 'reserva.confirmada',
  MANTENIMIENTO_RESULTADO: 'mantenimiento.resultado',
};
export const COLAS = {
  'verificador_patentes.solicitudes': EVENTOS.VEHICULO_VERIFICACION_SOLICITADA,
  'vehicle_service.verificacion_resultados': EVENTOS.VEHICULO_VERIFICACION_RESULTADO,
  'validador_patente.registros': EVENTOS.VEHICULO_EXTERNO_REGISTRADO,
  'validador_titularidad.registros': EVENTOS.VEHICULO_EXTERNO_REGISTRADO,
  'correlador_externos.resultados_patente': EVENTOS.VEHICULO_EXTERNO_VALIDACION_PATENTE,
  'correlador_externos.resultados_titularidad': EVENTOS.VEHICULO_EXTERNO_VALIDACION_TITULARIDAD,
  'vehicle_service.incorporaciones_completadas': EVENTOS.VEHICULO_EXTERNO_VALIDACION_COMPLETADA,
  'mantenimiento.reservas_confirmadas': EVENTOS.RESERVA_CONFIRMADA,
  'rental_service.mantenimiento_resultados': EVENTOS.MANTENIMIENTO_RESULTADO,
};

let connection = null;
let channel = null;

async function connect({ maxRetries = 20, retryDelayMs = 3000 } = {}) {
  if (connection && channel) return channel;
  const url = process.env.RABBITMQ_URL || 'amqp://guest:guest@localhost:5672';
  let lastError;
  for (let attempt = 1; attempt <= maxRetries; attempt += 1) {
    try {
      connection = await amqp.connect(url);
      connection.on('close', () => { connection = null; channel = null; });
      connection.on('error', () => { connection = null; channel = null; });
      channel = await connection.createChannel();
      await channel.assertExchange(EXCHANGE, 'topic', { durable: true });
      await channel.assertExchange(DLX_EXCHANGE, 'fanout', { durable: true });
      await channel.assertQueue(DLQ, { durable: true });
      await channel.bindQueue(DLQ, DLX_EXCHANGE, '');
      return channel;
    } catch (error) {
      lastError = error;
      await new Promise((resolve) => setTimeout(resolve, retryDelayMs));
    }
  }
  throw new Error(`No se pudo conectar a RabbitMQ: ${lastError?.message}`);
}

export async function declareQueue(queueName) {
  const routingKey = COLAS[queueName];
  if (!routingKey) {
    throw new Error(`Cola desconocida: ${queueName}`);
  }
  const ch = await connect();
  await ch.assertQueue(queueName, {
    durable: true,
    arguments: { 'x-dead-letter-exchange': DLX_EXCHANGE },
  });
  await ch.bindQueue(queueName, EXCHANGE, routingKey);
}

export async function declareAllQueues() {
  await connect();
  await Promise.all(Object.keys(COLAS).map((queueName) => declareQueue(queueName)));
}

/** Publica un evento JSON persistente en el exchange de Rentar. */
export async function publishEvent(routingKey, payload) {
  const ch = await connect();
  ch.publish(EXCHANGE, routingKey, Buffer.from(JSON.stringify(payload)), {
    contentType: 'application/json',
    persistent: true,
  });
}

/** Consume una cola. Si onEvent lanza, el mensaje va a la DLQ (nack sin requeue). */
export async function consumeEvent(queueName, onEvent) {
  await declareQueue(queueName);
  const ch = await connect();
  await ch.prefetch(1);
  await ch.consume(queueName, async (message) => {
    if (!message) return;
    try {
      await onEvent(JSON.parse(message.content.toString()));
      ch.ack(message);
    } catch (error) {
      console.error(`Error procesando evento de ${queueName}:`, error);
      ch.nack(message, false, false);
    }
  });
  console.log(`Escuchando eventos en la cola ${queueName}...`);
}

export async function closeEventBus() {
  await channel?.close().catch(() => {});
  await connection?.close().catch(() => {});
  channel = null;
  connection = null;
}
