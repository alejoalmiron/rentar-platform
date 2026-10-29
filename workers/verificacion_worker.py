import pika
import json
import os
import time

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
EXCHANGE = "rentar.events"

def procesar_verificacion(ch, method, properties, body):
    data = json.loads(body)
    vehiculo_id = data.get("vehiculoId")
    patente = data.get("patente")
    
    print(f"Worker procesando verificación para patente: {patente}")
    time.sleep(2)  # Simular latencia de red externa
    
    # 4. Se consulte un registro propio que simule la información policial.
    patentes_robadas = ["ROBADA123", "XYZ999"]
    
    resultado = "ROBADO" if patente in patentes_robadas else "VALIDADO"
    
    # 5. Se genere un nuevo evento informando el resultado de la verificación.
    respuesta = {
        "vehiculoId": vehiculo_id,
        "patente": patente,
        "resultado": resultado
    }
    
    # Publicar el resultado de vuelta al mismo Exchange
    ch.basic_publish(
        exchange=EXCHANGE,
        routing_key='vehiculos.verificacion.resultado',
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
    channel.exchange_declare(exchange=EXCHANGE, exchange_type='topic', durable=True)
    
    # Declarar la cola de solicitudes y vincularla al exchange
    queue = channel.queue_declare(queue='verificacion.solicitada.queue', durable=True)
    channel.queue_bind(exchange=EXCHANGE, queue=queue.method.queue, routing_key='vehiculos.verificacion.solicitada')
    
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