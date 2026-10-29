"""Mensajeria RabbitMQ de Vehicle Service (Hito 3).

Modulo autocontenido: cada microservicio es desplegable de forma independiente.
Las constantes deben coincidir con workers/common/topology.py (fuente de verdad).
"""

import json
import os
import threading
import time

import pika
from pika.exchange_type import ExchangeType

EXCHANGE = "rentar.events"
DLX_EXCHANGE = "rentar.dlx"
DLQ = "rentar.dlq"

# Eventos que publica o consume este servicio.
EVENTO_VERIFICACION_SOLICITADA = "vehiculos.verificacion.solicitada"
EVENTO_VERIFICACION_RESULTADO = "vehiculos.verificacion.resultado"
EVENTO_EXTERNO_REGISTRADO = "vehiculos.externos.registrados"
EVENTO_EXTERNO_COMPLETADO = "vehiculos.externos.validacion.completada"
COLA_RESULTADOS_VERIFICACION = "vehicle_service.verificacion_resultados"
COLA_INCORPORACIONES_COMPLETADAS = "vehicle_service.incorporaciones_completadas"


class EventBus:
    """Conexion perezosa a RabbitMQ con reintentos, para publicar y consumir."""

    def __init__(self):
        self.url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672")
        self._connection = None
        self._channel = None

    def _connect(self, max_retries=20, retry_delay=3):
        if self._connection and not self._connection.is_closed:
            return
        params = pika.URLParameters(self.url)
        params.heartbeat = 600
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                self._connection = pika.BlockingConnection(params)
                self._channel = self._connection.channel()
                self._declare()
                return
            except Exception as error:
                last_error = error
                print(f"RabbitMQ no disponible (intento {attempt}/{max_retries}). Reintentando...")
                time.sleep(retry_delay)
        raise RuntimeError(f"No se pudo conectar a RabbitMQ: {last_error}")

    def _declare(self):
        self._channel.exchange_declare(exchange=EXCHANGE, exchange_type=ExchangeType.topic, durable=True)
        self._channel.exchange_declare(exchange=DLX_EXCHANGE, exchange_type=ExchangeType.fanout, durable=True)
        self._channel.queue_declare(queue=DLQ, durable=True)
        self._channel.queue_bind(exchange=DLX_EXCHANGE, queue=DLQ)

    def publish(self, routing_key, payload):
        self._connect()
        self._channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=routing_key,
            body=json.dumps(payload),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=pika.DeliveryMode.Persistent,
            ),
        )
        print(f"Evento publicado [{routing_key}]: {payload}")

    def start_consumer(self, queue_name, routing_key, on_event):
        """Lanza un hilo daemon que consume la cola indicada. No bloquea al gRPC."""
        thread = threading.Thread(
            target=self._consume_loop,
            args=(queue_name, routing_key, on_event),
            daemon=True,
            name=f"consumer-{queue_name}",
        )
        thread.start()
        return thread

    def _consume_loop(self, queue_name, routing_key, on_event):
        while True:
            try:
                # 1. Crear una conexión TOTALMENTE AISLADA para este hilo consumidor
                params = pika.URLParameters(self.url)
                params.heartbeat = 600
                consumer_connection = pika.BlockingConnection(params)
                channel = consumer_connection.channel()

                # 2. Declarar la infraestructura en este canal independiente
                channel.exchange_declare(exchange=EXCHANGE, exchange_type=ExchangeType.topic, durable=True)
                channel.exchange_declare(exchange=DLX_EXCHANGE, exchange_type=ExchangeType.fanout, durable=True)
                
                channel.queue_declare(
                    queue=queue_name,
                    durable=True,
                    arguments={"x-dead-letter-exchange": DLX_EXCHANGE},
                )
                channel.queue_bind(exchange=EXCHANGE, queue=queue_name, routing_key=routing_key)
                channel.basic_qos(prefetch_count=1)

                def _callback(ch, method, _properties, body):
                    try:
                        on_event(json.loads(body))
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception as error:
                        print(f"Error procesando evento de {queue_name}: {error}")
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

                channel.basic_consume(queue=queue_name, on_message_callback=_callback)
                print(f"Escuchando eventos en la cola {queue_name} (conexión aislada)...")
                channel.start_consuming()
            except Exception as error:
                print(f"Consumidor {queue_name} caido ({error}). Reintentando en 5s...")
                time.sleep(5)

    def close(self):
        if self._connection and not self._connection.is_closed:
            self._connection.close()

# Instancia global para ser usada por todo el microservicio
event_bus = EventBus()