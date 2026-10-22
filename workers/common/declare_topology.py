"""Declara la topologia completa de RabbitMQ (exchange, DLQ y colas).

Uso:
    python declare_topology.py
    docker compose run --rm broker-init
"""

try:
    from messaging import RabbitMQ
except ImportError:
    from workers.common.messaging import RabbitMQ


def main():
    bus = RabbitMQ()
    bus.declare_all_queues()
    bus.close()
    print("OK: topologia de Rentar declarada (exchange, DLQ y colas de consumidores).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
