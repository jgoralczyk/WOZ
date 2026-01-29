import aio_pika
from aio_pika import DeliveryMode
import json

async def send_to_worker(connection: aio_pika.RobustConnection, data: dict):
    async with connection.channel() as channel:

        await channel.declare_queue("wnioski_queue", durable=True)

        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(data).encode(),
                delivery_mode=DeliveryMode.PERSISTENT
            ),
            routing_key="wnioski_queue"
        )
        print(f"[X] Wysłano do RabbitMQ: {data}")