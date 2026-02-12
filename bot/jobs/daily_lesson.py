"""
Daily AI Lesson Job - рассылка AI-сгенерированных уроков
"""
import logging
from datetime import datetime
from typing import Dict, Any

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)


def format_ai_lesson(lesson_content: Dict[str, Any], lesson_id: int) -> tuple[str, InlineKeyboardMarkup]:
    """
    Отформатировать AI-сгенерированный урок.
    
    Args:
        lesson_content: Dict с содержимым урока от Claude
        lesson_id: ID урока в БД
        
    Returns:
        (formatted_text, keyboard)
    """
    # Заголовок
    text = f"{lesson_content.get('title', '🇧🇷 Урок португальского')}\n\n"
    
    # Объяснение
    text += f"{lesson_content.get('explanation', '')}\n\n"
    
    # Примеры
    if 'examples' in lesson_content:
        text += "📝 <b>Примеры:</b>\n\n"
        for i, example in enumerate(lesson_content['examples'], 1):
            text += f"<b>{i}.</b>\n"
            text += f"🇧🇷 <i>{example.get('portuguese', '')}</i>\n"
            text += f"🇷🇺 {example.get('russian', '')}\n"
            text += f"💡 {example.get('note', '')}\n\n"
    
    # Совет
    if 'tip' in lesson_content and lesson_content['tip']:
        text += f"💡 <b>Совет:</b> {lesson_content['tip']}\n\n"
    
    # Культурная заметка
    if 'cultural_note' in lesson_content and lesson_content['cultural_note']:
        text += f"🌎 <i>{lesson_content['cultural_note']}</i>\n\n"
    
    # Практика
    if 'practice' in lesson_content and lesson_content['practice']:
        text += f"✏️ <b>Попробуй сам:</b>\n{lesson_content['practice']}"
    
    # Клавиатура
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="👍 Понятно",
                callback_data=f"feedback:{lesson_id}:clear"
            ),
            InlineKeyboardButton(
                text="❓ Сложно",
                callback_data=f"feedback:{lesson_id}:hard"
            )
        ],
        [
            InlineKeyboardButton(
                text="📚 Ещё урок",
                callback_data="get_lesson"
            )
        ]
    ])
    
    return text, keyboard


async def send_lesson_to_user(
    bot: Bot,
    user_id: int,
    lesson_content: Dict[str, Any],
    lesson_id: int,
    db
) -> bool:
    """Отправить урок пользователю."""
    try:
        lesson_text, keyboard = format_ai_lesson(lesson_content, lesson_id)
        
        await bot.send_message(
            chat_id=user_id,
            text=lesson_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        await db.update_last_lesson_time(user_id)
        
        logger.info(f"Sent AI lesson {lesson_id} to user {user_id}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send lesson to user {user_id}: {e}")
        return False


async def send_daily_lessons(bot: Bot, db, config, lesson_generator) -> None:
    """
    Отправить AI-сгенерированные уроки активным пользователям.
    
    Эта функция:
    1. Получает активных пользователей
    2. Для каждого генерирует персонализированный урок через Claude
    3. Сохраняет в БД
    4. Отправляет пользователю
    """
    try:
        users = await db.get_active_users()
        
        if not users:
            logger.debug("No active users")
            return
        
        now = datetime.utcnow()
        current_hour = now.hour
        
        sent_count = 0
        
        for user in users:
            try:
                user_id = user['user_id']
                user_hour = user.get('lesson_hour', config.DEFAULT_LESSON_HOUR)
                frequency = user.get('frequency', 'daily')
                last_lesson_at = user.get('last_lesson_at')
                
                # Проверяем, нужно ли отправлять урок
                should_send = False
                
                if current_hour == user_hour:
                    if not last_lesson_at:
                        should_send = True
                    else:
                        time_since_last = (now - last_lesson_at).total_seconds() / 3600
                        frequency_hours = config.FREQUENCIES.get(frequency, 1) * 24
                        
                        if time_since_last >= frequency_hours:
                            should_send = True
                
                if not should_send:
                    continue
                
                # Получаем контекст пользователя
                completed_topics = await db.get_completed_topics(user_id)
                difficult_topics = await db.get_difficult_topics(user_id)
                user_level = user.get('level', 'intermediate')
                
                user_stats = {
                    'level': user_level,
                    'difficult_topics': difficult_topics
                }
                
                logger.info(f"Generating lesson for user {user_id} (level: {user_level})")
                
                # Генерируем персонализированный урок через Claude API
                lesson_data = lesson_generator.generate_personalized_lesson(
                    user_stats=user_stats,
                    previous_lessons=completed_topics
                )
                
                # Извлекаем тему из lesson_data (генератор возвращает её)
                topic = lesson_data.get('_topic', 'general')  # добавим в генератор
                
                # Сохраняем урок в БД
                lesson_id = await db.save_lesson(
                    user_id=user_id,
                    topic=topic,
                    level=user_level,
                    content=lesson_data
                )
                
                # Отправляем пользователю
                success = await send_lesson_to_user(
                    bot, user_id, lesson_data, lesson_id, db
                )
                
                if success:
                    sent_count += 1
                    logger.info(f"✅ Sent AI lesson to user {user_id}")
            
            except Exception as e:
                logger.error(f"Failed to process user {user.get('user_id')}: {e}")
                continue
        
        if sent_count > 0:
            logger.info(f"📚 Sent {sent_count} AI-generated lessons")
    
    except Exception as e:
        logger.error(f"Failed in send_daily_lessons: {e}")


def add_lesson_jobs(
    scheduler: AsyncIOScheduler,
    *,
    bot: Bot,
    db,
    config,
    lesson_generator
) -> None:
    """Добавить задачи рассылки в scheduler."""
    
    # Рассылка каждый час (проверяем кому пора)
    scheduler.add_job(
        send_daily_lessons,
        trigger="cron",
        hour="*",
        minute=0,
        args=[bot, db, config, lesson_generator],
        id="send_ai_lessons",
        replace_existing=True,
    )
    
    logger.info("✅ Scheduled AI lesson job (runs every hour)")
