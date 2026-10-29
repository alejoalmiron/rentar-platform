import sqlite3
import threading

from common import topology
from common.messaging import RabbitMQ

DB_PATH = "correlador_externos.db"
DB_LOCK = threading.Lock()


def inicializar_estado():
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS validaciones (
                vehiculo_externo_id INTEGER PRIMARY KEY,
                patente_validada INTEGER NOT NULL DEFAULT 0,
                titularidad_validada INTEGER NOT NULL DEFAULT 0,
                rechazada INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        db.commit()


def resultado_valido(evento):
    return evento.get("resultado") == "VALIDADO"


def obtener_id(evento):
    return evento.get("vehiculoExternoId")


def procesar_resultado(evento, campo_validacion):
    vehiculo_externo_id = obtener_id(evento)
    if not isinstance(vehiculo_externo_id, int) or vehiculo_externo_id < 1:
        raise ValueError("Falta vehiculoExternoId válido en el resultado de validación")

    with DB_LOCK, sqlite3.connect(DB_PATH) as db:
        db.execute(
            "INSERT OR IGNORE INTO validaciones (vehiculo_externo_id) VALUES (?)",
            (vehiculo_externo_id,),
        )
        if not resultado_valido(evento):
            db.execute(
                "UPDATE validaciones SET rechazada = 1 WHERE vehiculo_externo_id = ?",
                (vehiculo_externo_id,),
            )
        else:
            db.execute(
                f"UPDATE validaciones SET {campo_validacion} = 1 WHERE vehiculo_externo_id = ?",
                (vehiculo_externo_id,),
            )
        row = db.execute(
            """
            SELECT patente_validada, titularidad_validada, rechazada
            FROM validaciones WHERE vehiculo_externo_id = ?
            """,
            (vehiculo_externo_id,),
        ).fetchone()
        db.commit()

    if row == (1, 1, 0):
        RabbitMQ().publish(
            topology.EVENTOS["VEHICULO_EXTERNO_VALIDACION_COMPLETADA"],
            {"vehiculoExternoId": vehiculo_externo_id},
        )


def procesar_resultado_patente(evento):
    procesar_resultado(evento, "patente_validada")


def procesar_resultado_titularidad(evento):
    procesar_resultado(evento, "titularidad_validada")


def main():
    inicializar_estado()
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
