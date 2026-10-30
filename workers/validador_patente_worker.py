from common.messaging import RabbitMQ
from common import topology


REGISTRO_PATENTES = {
    "DEF456",
    "AA123BB",
    "ABC123",
}


def procesar_validacion_patente(evento):
    vehiculo_externo_id = evento.get("vehiculoExternoId") or evento.get("vehiculo_externo_id")
    patente = (evento.get("patente") or "").strip().upper()
    resultado = "VALIDADO" if patente in REGISTRO_PATENTES else "RECHAZADO"
    payload = {
        "vehiculoExternoId": vehiculo_externo_id,
        "patente": patente,
        "resultado": resultado,
    }
    RabbitMQ().publish(
        topology.EVENTOS["VEHICULO_EXTERNO_VALIDACION_PATENTE"],
        payload,
    )


def main():
    RabbitMQ().consume("validador_patente.registros", procesar_validacion_patente)


if __name__ == "__main__":
    main()
