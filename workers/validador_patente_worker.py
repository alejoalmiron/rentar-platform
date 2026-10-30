from common.messaging import RabbitMQ
from common import topology
from common.registro_policial import PATENTES_DENUNCIADAS


def procesar_validacion_patente(evento):
    vehiculo_externo_id = evento.get("vehiculoExternoId") or evento.get("vehiculo_externo_id")
    patente = (evento.get("patente") or "").strip().upper()
    resultado = "RECHAZADO" if patente in PATENTES_DENUNCIADAS else "VALIDADO"
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
