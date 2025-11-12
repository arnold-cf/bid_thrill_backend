import pika

def connect_to_rabbitmq():
    """Establish a connection to RabbitMQ."""
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        return connection, channel
    except Exception as e:
        print(f"RabbitMQ connection error: {e}")
        raise
