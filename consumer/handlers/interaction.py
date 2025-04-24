from sqlalchemy.ext.asyncio import AsyncSession

from consumer.logger import logger
from consumer.services.interaction_service import process_like, process_dislike
from consumer.storage import get_db_session


async def handle_like(body: dict) -> None:
    """
    Обрабатывает сообщение о лайке.
    
    Args:
        body: Тело сообщения с данными о лайке
    """
    try:
        logger.info('Received like event with data: %s', body)
        
        user_id = body.get('user_id')
        target_user_id = body.get('target_user_id')
        
        if not user_id or not target_user_id:
            logger.error(
                'Missing required fields in like message. Received data: %s',
                body
            )
            return
            
        logger.info(
            'Processing like from user %s to user %s',
            user_id,
            target_user_id
        )
            
        async with get_db_session() as db:
            success = await process_like(db, user_id, target_user_id)
            if success:
                logger.info(
                    'Successfully processed like from user %s to user %s',
                    user_id,
                    target_user_id
                )
            else:
                logger.warning(
                    'Failed to process like from user %s to user %s',
                    user_id,
                    target_user_id
                )
                
    except Exception as e:
        logger.error(
            'Error handling like event with data %s: %s',
            body,
            str(e)
        )
        # Add traceback for better debugging
        import traceback
        logger.error('Traceback: %s', traceback.format_exc())


async def handle_dislike(body: dict) -> None:
    """
    Обрабатывает сообщение о дизлайке.
    
    Args:
        body: Тело сообщения с данными о дизлайке
    """
    try:
        logger.info('Received dislike event with data: %s', body)
        
        user_id = body.get('user_id')
        target_user_id = body.get('target_user_id')
        
        if not user_id or not target_user_id:
            logger.error(
                'Missing required fields in dislike message. Received data: %s',
                body
            )
            return
            
        logger.info(
            'Processing dislike from user %s to user %s',
            user_id,
            target_user_id
        )
            
        async with get_db_session() as db:
            success = await process_dislike(db, user_id, target_user_id)
            if success:
                logger.info(
                    'Successfully processed dislike from user %s to user %s',
                    user_id,
                    target_user_id
                )
            else:
                logger.warning(
                    'Failed to process dislike from user %s to user %s',
                    user_id,
                    target_user_id
                )
                
    except Exception as e:
        logger.error(
            'Error handling dislike event with data %s: %s',
            body,
            str(e)
        )
        # Add traceback for better debugging
        import traceback
        logger.error('Traceback: %s', traceback.format_exc()) 