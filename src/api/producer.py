import json
from typing import Optional

import aio_pika
from aio_pika import ExchangeType

from src.logger import logger
from src.storage.rabbit import channel_pool


async def send_profile_request(
    user_id: int,
    action: str = 'search',
    target_user_id: Optional[int] = None
) -> None:
    """
    Send a profile request to the common queue.
    
    Args:
        user_id: The ID of the user requesting profiles
        action: The action to perform ('search', 'like', 'dislike')
        target_user_id: The ID of the target user (for like/dislike actions)
    """
    try:
        async with channel_pool.acquire() as channel:
            # Declare exchange
            exchange = await channel.declare_exchange(
                'user_messages',  # Use the common queue
                ExchangeType.TOPIC,
                durable=True
            )
            
            # Prepare message data
            message_data = {
                'user_id': user_id,
                'action': 'update_profile_redis',
                'request_type': action
            }
            
            if target_user_id:
                message_data['target_user_id'] = target_user_id
            
            # Publish message
            await exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message_data).encode(),
                    content_type='application/json'
                ),
                routing_key='profile.update_redis'
            )
            
            logger.info(
                'Sent profile request for user %s, action: %s%s',
                user_id,
                action,
                f', target: {target_user_id}' if target_user_id else ''
            )
            
    except Exception as e:
        logger.error('Error sending profile request: %s', e)
        raise


async def send_profile_update(profile_data: dict) -> None:
    """
    Send a profile update to the common queue.
    
    Args:
        profile_data: The profile data to update
    """
    try:
        async with channel_pool.acquire() as channel:
            # Declare exchange
            exchange = await channel.declare_exchange(
                'user_messages',  # Use the common queue
                ExchangeType.TOPIC,
                durable=True
            )
            
            # Publish message
            await exchange.publish(
                aio_pika.Message(
                    body=json.dumps({
                        'user_id': profile_data.get('user_id'),
                        'action': 'profile_update',
                        'field': 'profile_data',
                        'value': profile_data
                    }).encode(),
                    content_type='application/json'
                ),
                routing_key='profile.update'
            )
            
            logger.info(
                'Sent profile update for user %s',
                profile_data.get('user_id')
            )
            
    except Exception as e:
        logger.error('Error sending profile update: %s', e)
        raise


async def send_interaction_event(user_id: int, target_user_id: int, action: str) -> None:
    """
    Send a like/dislike event to the common queue.
    
    Args:
        user_id: The ID of the user who performed the action
        target_user_id: The ID of the target user
        action: The action performed ('like' or 'dislike')
    """
    try:
        logger.info(
            'Preparing to send %s event: user_id=%s, target_user_id=%s',
            action,
            user_id,
            target_user_id
        )
        
        async with channel_pool.acquire() as channel:
            # Declare exchange
            exchange = await channel.declare_exchange(
                'user_messages',  # Use the common queue
                ExchangeType.TOPIC,
                durable=True
            )
            
            # Prepare message data
            message_data = {
                'user_id': user_id,
                'target_user_id': target_user_id,
                'action': action
            }
            
            logger.info(
                'Sending %s event to queue with data: %s',
                action,
                message_data
            )
            
            # Publish message
            await exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message_data).encode(),
                    content_type='application/json'
                ),
                routing_key='profile.interaction'
            )
            
            logger.info(
                'Successfully sent %s event from user %s to user %s',
                action,
                user_id,
                target_user_id
            )
            
    except Exception as e:
        logger.error(
            'Error sending %s event from user %s to user %s: %s',
            action,
            user_id,
            target_user_id,
            str(e)
        )
        raise 