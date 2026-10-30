import pika
import json
import os
import time

try:
    from common import topology
    from common.registro_policial import PATENTES_DENUNCIADAS
except ImportError:
    from workers.common import topology
    from workers.common.registro_policial import PATENTES_DENUNCIADAS

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
QUEUE_NAME = "verificador_patentes.solicitudes"

def procesar_verificacion(ch, method, properties, body):
    data = json.loads(body)
    vehiculo_id = data.get("vehiculoId")
    patente = data.get("patente")
    
    print(f"Worker procesando verificación para patente: {patente}")
    time.sleep(2)  # Simular latencia de red externa
    
    # 4. Se consulte un registro propio que simule la información policial.
    
    resultado = "ROBADO" if patente in PATENTES_DENUNCIADAS else "VALIDADO"
    
    # 5. Se genere un nuevo evento informando el resultado de la verificación.
    respuesta = {
        "vehiculoId": vehiculo_id,
        "patente": patente,
        "resultado": resultado
    }
    
    # Publicar el resultado de vuelta al mismo Exchange
    ch.basic_publish(
        exchange=topology.EXCHANGE,
        routing_key=topology.EVENTOS["VEHICULO_VERIFICACION_RESULTADO"],
        body=json.dumps(respuesta),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    print(f"Evento vehiculos.verificacion.resultado publicado: {respuesta}")
    
    # Acknowledge manual del mensaje procesado
    ch.basic_ack(delivery_tag=method.delivery_tag)

def start_worker():
    print("Iniciando Worker de Verificación Policial...")
    connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    channel = connection.channel()
    
    # Usar el exchange correcto de la topología
    channel.exchange_declare(
        exchange=topology.EXCHANGE,
        exchange_type='topic',
        durable=True,
    )
    
    # Declarar la cola de solicitudes y vincularla al exchange
    queue = channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True,
        arguments={"x-dead-letter-exchange": topology.DLX_EXCHANGE},
    )
    channel.queue_bind(
        exchange=topology.EXCHANGE,
        queue=queue.method.queue,
        routing_key=topology.COLAS[QUEUE_NAME],
    )
    
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue.method.queue, on_message_callback=procesar_verificacion)
    
    print("Worker listo. Esperando eventos vehiculos.verificacion.solicitada...")
    channel.start_consuming()

if __name__ == '__main__':
    while True:
        try:
            start_worker()
        except pika.exceptions.AMQPConnectionError:
            print("RabbitMQ no está listo, reintentando en 5 segundos...")
            time.sleep(5)
        except Exception as e:
            print(f"Error inesperado: {e}")
            time.sleep(5)