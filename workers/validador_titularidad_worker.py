from common.messaging import RabbitMQ
from common import topology


REGISTRO_TITULARIDAD = {
    ("30123456", "DEF456"),
    ("30123456", "AA123BB"),
    ("30123456", "ABC123"),
    ("40999000", "DEF456"),
    ("40999000", "AA123BB"),
    ("40999000", "ABC123"),
    ("40999000", "XYZ999"),
}


def procesar_validacion_titularidad(evento):
    vehiculo_externo_id = evento.get("vehiculoExternoId") or evento.get("vehiculo_externo_id")
    documento = str(evento.get("documento") or "").strip()
    patente = (evento.get("patente") or "").strip().upper()
    resultado = "VALIDADO" if (documento, patente) in REGISTRO_TITULARIDAD else "RECHAZADO"
    payload = {
        "vehiculoExternoId": vehiculo_externo_id,
        "clienteId": evento.get("clienteId"),
        "documento": documento,
        "patente": patente,
        "resultado": resultado,
    }
    RabbitMQ().publish(
        topology.EVENTOS["VEHICULO_EXTERNO_VALIDACION_TITULARIDAD"],
        payload,
    )


def main():
    RabbitMQ().consume("validador_titularidad.registros", procesar_validacion_titularidad)


if __name__ == "__main__":
    main()
