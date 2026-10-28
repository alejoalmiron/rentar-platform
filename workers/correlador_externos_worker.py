import threading

from common import topology
from common.messaging import RabbitMQ
from app import external_repository
from app.db import SessionLocal


def resultado_valido(evento):
    return evento.get("resultado") == "VALIDADO" or evento.get("valida") is True


def obtener_id(evento):
    return evento.get("vehiculoExternoId") or evento.get("vehiculo_externo_id")


def procesar_resultado(db, evento, campo_validacion):
    vehiculo_externo_id = obtener_id(evento)
    if not vehiculo_externo_id:
        raise ValueError("Falta vehiculoExternoId en el resultado de validación")

    vehiculo = external_repository.get_by_correlation_id(db, vehiculo_externo_id)
    if not vehiculo:
        raise ValueError(f"Vehículo externo no encontrado: {vehiculo_externo_id}")

    if not resultado_valido(evento):
        external_repository.update_estado_by_correlation(
            db,
            vehiculo_externo_id,
            "RECHAZADO",
        )
        return

    vehiculo = external_repository.update_validacion(
        db,
        vehiculo_externo_id,
        campo_validacion,
        True,
    )
    if vehiculo.patente_validada and vehiculo.titularidad_validada:
        external_repository.update_estado_by_correlation(
            db,
            vehiculo_externo_id,
            "DISPONIBLE",
        )
        RabbitMQ().publish(
            topology.EVENTOS["VEHICULO_EXTERNO_VALIDACION_COMPLETADA"],
            {
                "vehiculoExternoId": vehiculo_externo_id,
                "clienteId": vehiculo.cliente_id,
            },
        )


def procesar_resultado_patente(evento):
    db = SessionLocal()
    try:
        procesar_resultado(db, evento, "patente_validada")
    finally:
        db.close()


def procesar_resultado_titularidad(evento):
    db = SessionLocal()
    try:
        procesar_resultado(db, evento, "titularidad_validada")
    finally:
        db.close()


def ejecutar_consumidor(queue_name, callback):
    RabbitMQ().consume(queue_name, callback)


def main():
    consumidores = (
        ("correlador_externos.resultados_patente", procesar_resultado_patente),
        ("correlador_externos.resultados_titularidad", procesar_resultado_titularidad),
    )
    for queue_name, callback in consumidores:
        threading.Thread(
            target=ejecutar_consumidor,
            args=(queue_name, callback),
            daemon=True,
        ).start()
    threading.Event().wait()


if __name__ == "__main__":
    main()
