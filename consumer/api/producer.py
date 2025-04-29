import json
import aio_pika
from typing import Dict, Any
import os

# RabbitMQ configuration
RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@rabbitmq:5672/')
PROFILE_REQUEST_QUEUE = 'profile_requests'

async def send_profile_request(user_id: int, request_data: Dict[str, Any]) -> None:
    """
    Send a profile request to the profile service via RabbitMQ.
    
    Args:
        user_id (int): The ID of the user making the request
        request_data (Dict[str, Any]): Additional data for the profile request
    """
    try:
        # Connect to RabbitMQ
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        
        async with connection:
            # Create a channel
            channel = await connection.channel()
            
            # Declare the queue
            queue = await channel.declare_queue(
                PROFILE_REQUEST_QUEUE,
                durable=True
            )
            
            # Prepare the message
            message_data = {
                'user_id': user_id,
                **request_data
            }
            
            # Create the message
            message = aio_pika.Message(
                body=json.dumps(message_data).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            
            # Send the message
            await channel.default_exchange.publish(
                message,
                routing_key=PROFILE_REQUEST_QUEUE
            )
            
    except Exception as e:
        print(f"Error sending profile request: {e}")
        raise 