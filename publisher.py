import aio_pika
import json

async def send_to_worker(connection: aio_pika.RobustConnection, data: dict):
    async with connection.channel() as channel:

        await channel.declare_queue("wnioski_queue", durable=True)

        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(data).encode(),
                delivery_mode=aio_pika.DeliveryMode.Persistent
            ),
            routing_key="wnioski_queue"
        )
        print(f"[X] Wysłano do RabbitMQ: {data}")