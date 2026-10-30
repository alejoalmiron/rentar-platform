import threading

from app import external_repository
from app.db import SessionLocal
from common import topology
from common.messaging import RabbitMQ


def resultado_valido(evento):
    return evento.get("resultado") == "VALIDADO"


def obtener_id(evento):
    return evento.get("vehiculoExternoId")


def procesar_resultado(evento, campo_validacion):
    vehiculo_externo_id = obtener_id(evento)
    if not isinstance(vehiculo_externo_id, int) or vehiculo_externo_id < 1:
        raise ValueError("Falta vehiculoExternoId válido en el resultado de validación")

    correlacion = str(vehiculo_externo_id)
    db = SessionLocal()
    try:
        if not external_repository.get_by_correlation_id(db, correlacion):
            raise ValueError(f"Vehículo externo no encontrado: {vehiculo_externo_id}")
        if not resultado_valido(evento):
            external_repository.update_estado_by_correlation(db, correlacion, "RECHAZADO")
            return
        vehiculo = external_repository.update_validacion(db, correlacion, campo_validacion, True)
        completo = (
            vehiculo.estado == "PENDIENTE"
            and vehiculo.patente_validada
            and vehiculo.titularidad_validada
        )
    finally:
        db.close()

    if completo:
        bus = RabbitMQ()
        bus.publish(
            topology.EVENTOS["VEHICULO_EXTERNO_VALIDACION_COMPLETADA"],
            {"vehiculoExternoId": vehiculo_externo_id},
        )
        bus.close()


def procesar_resultado_patente(evento):
    procesar_resultado(evento, "patente_validada")


def procesar_resultado_titularidad(evento):
    procesar_resultado(evento, "titularidad_validada")


def main():
    for queue_name, callback in (
        ("correlador_externos.resultados_patente", procesar_resultado_patente),
        ("correlador_externos.resultados_titularidad", procesar_resultado_titularidad),
    ):
        threading.Thread(
            target=RabbitMQ().consume,
            args=(queue_name, callback),
            daemon=True,
        ).start()
    threading.Event().wait()


if __name__ == "__main__":
    main()
