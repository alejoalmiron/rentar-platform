"""Helper de mensajeria RabbitMQ para los servicios Python de Rentar (Hito 3).

Uso:
    from workers.common.messaging import RabbitMQ
    from workers.common import topology

    bus = RabbitMQ()
    bus.declare_infrastructure()
    bus.publish(topology.EVENTOS["RESERVA_CONFIRMADA"], {"reservaId": 1, ...})
    bus.consume("mantenimiento.reservas_confirmadas", on_event)
"""

import json
import os
import time

import pika
from pika.exchange_type import ExchangeType

try:
    from . import topology
except ImportError:
    import topology


class RabbitMQ:
    def __init__(self, url=None, max_retries=20, retry_delay=3):
        self.url = url or os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672")
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._connection = None
        self._channel = None

    def _connect(self):
        if self._connection and not self._connection.is_closed:
            return
        params = pika.URLParameters(self.url)
        params.heartbeat = 600
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                self._connection = pika.BlockingConnection(params)
                self._channel = self._connection.channel()
                return
            except Exception as error:  # AMQPConnectionError y variantes
                last_error = error
                print(f"RabbitMQ no disponible (intento {attempt}/{self.max_retries}). Reintentando en {self.retry_delay}s...")
                time.sleep(self.retry_delay)
        raise RuntimeError(f"No se pudo conectar a RabbitMQ: {last_error}")

    @property
    def channel(self):
        self._connect()
        return self._channel

    def declare_infrastructure(self):
        """Declara exchange principal, DLX y DLQ. Idempotente."""
        channel = self.channel
        channel.exchange_declare(exchange=topology.EXCHANGE, exchange_type=ExchangeType.topic, durable=True)
        channel.exchange_declare(exchange=topology.DLX_EXCHANGE, exchange_type=ExchangeType.fanout, durable=True)
        channel.queue_declare(queue=topology.DLQ, durable=True)
        channel.queue_bind(exchange=topology.DLX_EXCHANGE, queue=topology.DLQ)

    def declare_queue(self, queue_name):
        """Declara la cola del consumidor y la bindea a su routing key. Idempotente."""
        routing_key = topology.COLAS[queue_name]
        channel = self.channel
        channel.queue_declare(
            queue=queue_name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": topology.DLX_EXCHANGE,
            },
        )
        channel.queue_bind(exchange=topology.EXCHANGE, queue=queue_name, routing_key=routing_key)

    def declare_all_queues(self):
        """Declara exchange, DLQ y todas las colas de consumidores. Idempotente."""
        self.declare_infrastructure()
        for queue_name in topology.COLAS:
            self.declare_queue(queue_name)

    def publish(self, routing_key, payload):
        """Publica un evento JSON persistente."""
        self.channel.basic_publish(
            exchange=topology.EXCHANGE,
            routing_key=routing_key,
            body=json.dumps(payload),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=pika.DeliveryMode.Persistent,
            ),
        )
        print(f"Evento publicado [{routing_key}]: {payload}")

    def consume(self, queue_name, on_event):
        """Consume eventos de una cola. on_event recibe el payload ya parseado.

        Si on_event termina sin excepcion se hace ack; si lanza, el mensaje va
        a la DLQ (nack sin requeue) para no bloquear la cola.
        """
        while True:
            try:
                self._connect()
                channel = self.channel
                self.declare_infrastructure()
                self.declare_queue(queue_name)
                channel.basic_qos(prefetch_count=1)

                def _callback(ch, method, _properties, body):
                    try:
                        on_event(json.loads(body))
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception as error:
                        print(f"Error procesando evento de {queue_name}: {error}")
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

                channel.basic_consume(queue=queue_name, on_message_callback=_callback)
                print(f"Escuchando eventos en la cola {queue_name}...")
                channel.start_consuming()
            except Exception as error:
                print(f"Consumidor {queue_name} caido ({error}). Reintentando en 5s...")
                self._connection = None
                self._channel = None
                time.sleep(5)

    def close(self):
        if self._connection and not self._connection.is_closed:
            self._connection.close()
