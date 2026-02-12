"""
AI-Powered Portuguese Learning Bot
Генерирует уроки через Claude API
"""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import Config
from bot.database.db import Database
from bot.ai.generator import LessonGenerator
from bot.handlers import start, settings, feedback
from bot.jobs.daily_lesson import add_lesson_jobs

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


async def main():
    """Запуск бота."""
    try:
        # Загружаем конфигурацию
        config = Config()
        logger.info("Configuration loaded")
        
        # Инициализируем бота
        bot = Bot(
            token=config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        logger.info("Bot initialized")
        
        # Инициализируем БД
        db = Database(config.DATABASE_URL)
        await db.init_db()
        logger.info("Database connected")
        
        # Инициализируем AI генератор уроков
        lesson_generator = LessonGenerator(
            api_key=config.ANTHROPIC_API_KEY,
            model=config.ANTHROPIC_MODEL
        )
        logger.info(f"AI Generator initialized with model {config.ANTHROPIC_MODEL}")
        
        # Создаём dispatcher
        dp = Dispatcher()
        
        # Регистрируем роутеры
        dp.include_router(start.router)
        dp.include_router(settings.router)
        dp.include_router(feedback.router)
        
        # Инициализируем scheduler для рассылки
        scheduler = AsyncIOScheduler(timezone="UTC")
        add_lesson_jobs(
            scheduler,
            bot=bot,
            db=db,
            config=config,
            lesson_generator=lesson_generator
        )
        scheduler.start()
        
        logger.info("Bot started successfully!")
        logger.info(f"Scheduler running with {len(scheduler.get_jobs())} jobs")
        
        # Запускаем polling
        await dp.start_polling(
            bot,
            db=db,
            config=config,
            lesson_generator=lesson_generator,
            allowed_updates=dp.resolve_used_update_types()
        )
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    
    finally:
        # Cleanup
        if 'db' in locals():
            await db.close()
        if 'bot' in locals():
            await bot.session.close()
        if 'scheduler' in locals():
            scheduler.shutdown()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        sys.exit(1)
