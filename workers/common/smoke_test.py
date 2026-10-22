"""Smoke test del broker RabbitMQ (Hito 3).

Publica un evento de prueba en el exchange real y lo consume desde una cola
temporal, verificando la conexion, la topologia y el ciclo publish/consume.
No usa routing keys de dominio para no ensuciar las colas de los workers.

Uso (dentro de un contenedor o con RABBITMQ_URL apuntando al broker):
    python smoke_test.py
    docker compose run --rm --entrypoint python broker-init smoke_test.py
"""

try:
    from messaging import RabbitMQ
    import topology
except ImportError:
    from workers.common.messaging import RabbitMQ
    from workers.common import topology


def main():
    bus = RabbitMQ(max_retries=10, retry_delay=2)
    bus.declare_all_queues()

    queue = "smoke_test.queue"
    routing_key = "smoke.ping"
    bus.channel.queue_declare(queue=queue, durable=False, auto_delete=True)
    bus.channel.queue_bind(exchange=topology.EXCHANGE, queue=queue, routing_key=routing_key)

    payload = {"prueba": True, "origen": "workers.common.smoke_test"}
    bus.publish(routing_key, payload)

    method, _properties, body = bus.channel.basic_get(queue=queue, auto_ack=True)
    assert method is not None, "La cola de prueba quedo vacia: el evento no llego"
    assert b'"prueba": true' in body or b'"prueba":true' in body, f"Payload inesperado: {body}"

    bus.channel.queue_delete(queue=queue)
    bus.close()
    print("OK: RabbitMQ publica y entrega eventos con la topologia de Rentar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
