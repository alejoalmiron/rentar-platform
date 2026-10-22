"""Smoke test del broker desde Vehicle Service.

Verifica conexion a RabbitMQ, declara la infraestructura y prueba el ciclo
publish/consume con una cola temporal. No toca datos del dominio.

Uso: docker compose exec vehicle-service python -m app.smoke_broker
"""

from app.messaging import EventBus, EXCHANGE


def main():
    bus = EventBus()
    bus._connect()
    queue = "vehicle_service.smoke"
    routing_key = "smoke.ping"

    bus._channel.queue_declare(queue=queue, durable=False, auto_delete=True)
    bus._channel.queue_bind(exchange=EXCHANGE, queue=queue, routing_key=routing_key)
    bus.publish(routing_key, {"prueba": True})

    method, _props, body = bus._channel.basic_get(queue=queue, auto_ack=True)
    assert method is not None, "El evento de prueba no llego a la cola"
    bus._channel.queue_delete(queue=queue)
    bus.close()
    print("OK: Vehicle Service publica y recibe eventos via RabbitMQ.")


if __name__ == "__main__":
    main()
