"""Topologia de mensajeria del sistema Rentar (Hito 3).

Fuente unica de verdad para exchange, colas y routing keys.
Todos los productores y consumidores deben usar estas constantes.
"""

EXCHANGE = "rentar.events"
DLX_EXCHANGE = "rentar.dlx"
DLQ = "rentar.dlq"

# Routing keys de los eventos definidos por el enunciado del Hito 3.
EVENTOS = {
    "VEHICULO_VERIFICACION_SOLICITADA": "vehiculos.verificacion.solicitada",
    "VEHICULO_VERIFICACION_RESULTADO": "vehiculos.verificacion.resultado",
    "VEHICULO_EXTERNO_REGISTRADO": "vehiculos.externos.registrados",
    "VEHICULO_EXTERNO_VALIDACION_PATENTE": "vehiculos.externos.validacion.patente",
    "VEHICULO_EXTERNO_VALIDACION_TITULARIDAD": "vehiculos.externos.validacion.titularidad",
    "VEHICULO_EXTERNO_VALIDACION_COMPLETADA": "vehiculos.externos.validacion.completada",
    "RESERVA_CONFIRMADA": "reserva.confirmada",
    "MANTENIMIENTO_RESULTADO": "mantenimiento.resultado",
}

# Colas: una por componente consumidor. Dos workers que consumen el mismo
# evento (validadores de externos) tienen colas separadas.
COLAS = {
    # Integrante 2: verificador de patentes consume solicitudes; Vehicle consume resultados.
    "verificador_patentes.solicitudes": EVENTOS["VEHICULO_VERIFICACION_SOLICITADA"],
    "vehicle_service.verificacion_resultados": EVENTOS["VEHICULO_VERIFICACION_RESULTADO"],
    # Integrante 3: ambos validadores escuchan el mismo registro; el correlador escucha ambos resultados.
    "validador_patente.registros": EVENTOS["VEHICULO_EXTERNO_REGISTRADO"],
    "validador_titularidad.registros": EVENTOS["VEHICULO_EXTERNO_REGISTRADO"],
    "correlador_externos.resultados_patente": EVENTOS["VEHICULO_EXTERNO_VALIDACION_PATENTE"],
    "correlador_externos.resultados_titularidad": EVENTOS["VEHICULO_EXTERNO_VALIDACION_TITULARIDAD"],
    "vehicle_service.incorporaciones_completadas": EVENTOS["VEHICULO_EXTERNO_VALIDACION_COMPLETADA"],
    # Integrante 4: worker de mantenimiento consume confirmaciones; Rental consume resultados.
    "mantenimiento.reservas_confirmadas": EVENTOS["RESERVA_CONFIRMADA"],
    "rental_service.mantenimiento_resultados": EVENTOS["MANTENIMIENTO_RESULTADO"],
}
