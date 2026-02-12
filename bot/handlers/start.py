"""
Start handler - приветствие и регистрация пользователя
"""
import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db, config):
    """Обработка команды /start."""
    user = message.from_user
    
    # Регистрируем пользователя
    await db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        language_code=user.language_code
    )
    
    welcome_text = (
        f"Olá, {user.first_name}! 🇧🇷\n\n"
        "Добро пожаловать в бота для изучения португальского!\n\n"
        "📚 Я буду присылать тебе короткие уроки каждый день.\n"
        "Уроки практичные и в доступной форме — "
        "грамматика, сленг, произношение, культура.\n\n"
        "🎯 Что ты получишь:\n"
        "• Ежедневная порция знаний (5-10 минут)\n"
        "• Примеры из жизни\n"
        "• Упражнения для практики\n"
        "• Прогресс обучения\n\n"
        "⚙️ Настрой частоту уроков командой /settings\n"
        "📊 Смотри свой прогресс — /stats\n"
        "❓ Помощь — /help"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⚙️ Настройки",
                callback_data="open_settings"
            )
        ],
        [
            InlineKeyboardButton(
                text="📚 Получить первый урок",
                callback_data="get_lesson"
            )
        ]
    ])
    
    await message.answer(welcome_text, reply_markup=keyboard)
    logger.info(f"User {user.id} started the bot")


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Помощь по использованию бота."""
    help_text = (
        "🇧🇷 <b>Помощь по использованию бота</b>\n\n"
        "<b>Команды:</b>\n"
        "/start — Начать работу с ботом\n"
        "/settings — Настройки (частота, время)\n"
        "/stats — Твоя статистика\n"
        "/pause — Приостановить уроки\n"
        "/resume — Возобновить уроки\n"
        "/help — Эта справка\n\n"
        "<b>Как это работает:</b>\n\n"
        "1️⃣ Бот присылает уроки по расписанию\n"
        "2️⃣ Читаешь, изучаешь примеры\n"
        "3️⃣ Оставляешь отзыв (👍 понятно / ❓ сложно)\n"
        "4️⃣ Бот запоминает твой прогресс\n\n"
        "<b>Настройки:</b>\n\n"
        "В /settings ты можешь:\n"
        "• Выбрать частоту уроков (от 2 раз в день до раза в неделю)\n"
        "• Установить удобное время\n"
        "• Выбрать часовой пояс\n\n"
        "Есть вопросы? Пиши @your_support"
    )
    
    await message.answer(help_text, parse_mode="HTML")


@router.message(Command("stats"))
async def cmd_stats(message: Message, db):
    """Показать статистику пользователя."""
    user_id = message.from_user.id
    
    # Получаем статистику
    stats = await db.get_user_stats(user_id)
    user_data = await db.get_user(user_id)
    
    if not stats.get('total_lessons'):
        await message.answer(
            "📊 У тебя пока нет статистики.\n\n"
            "Получи первый урок с помощью кнопки ниже! 👇",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📚 Получить урок", callback_data="get_lesson")]
            ])
        )
        return
    
    from datetime import datetime
    
    first_lesson = datetime.fromisoformat(stats['first_lesson'])
    last_lesson = datetime.fromisoformat(stats['last_lesson'])
    days_learning = (datetime.now() - first_lesson).days + 1
    
    stats_text = (
        f"📊 <b>Твоя статистика</b>\n\n"
        f"🎯 Уроков пройдено: <b>{stats['total_lessons']}</b>\n"
        f"📅 Учишься: <b>{days_learning} дней</b>\n"
        f"📚 Первый урок: {first_lesson.strftime('%d.%m.%Y')}\n"
        f"🕐 Последний урок: {last_lesson.strftime('%d.%m.%Y')}\n\n"
        f"⚙️ Частота: <b>{user_data.get('frequency', 'daily')}</b>\n"
        f"✅ Статус: <b>{'Активен' if user_data.get('is_active') else 'На паузе'}</b>\n\n"
        f"Так держать! 🚀"
    )
    
    await message.answer(stats_text, parse_mode="HTML")


@router.message(Command("pause"))
async def cmd_pause(message: Message, db):
    """Приостановить рассылку уроков."""
    user_id = message.from_user.id
    await db.set_user_active(user_id, False)
    
    await message.answer(
        "⏸ Рассылка уроков приостановлена.\n\n"
        "Чтобы возобновить, используй команду /resume"
    )
    logger.info(f"User {user_id} paused lessons")


@router.message(Command("resume"))
async def cmd_resume(message: Message, db):
    """Возобновить рассылку уроков."""
    user_id = message.from_user.id
    await db.set_user_active(user_id, True)
    
    await message.answer(
        "▶️ Рассылка уроков возобновлена!\n\n"
        "Следующий урок придёт по расписанию. 📚"
    )
    logger.info(f"User {user_id} resumed lessons")


@router.callback_query(F.data == "get_lesson")
async def callback_get_lesson(callback_query, db, config):
    """Получить случайный урок прямо сейчас."""
    from bot.lessons.loader import LessonLoader
    from bot.lessons.formatter import format_lesson
    
    user_id = callback_query.from_user.id
    
    # Загружаем уроки
    loader = LessonLoader(config.LESSONS_PATH)
    lessons = loader.get_all_lessons()
    
    # Получаем пройденные уроки
    completed = await db.get_completed_lessons(user_id)
    
    # Находим непройденный урок
    available = [l for l in lessons if l['id'] not in completed]
    
    if not available:
        # Все уроки пройдены - начинаем сначала
        available = lessons
    
    # Берём первый доступный
    lesson = available[0]
    
    # Форматируем и отправляем
    lesson_text, keyboard = format_lesson(lesson)
    
    await callback_query.message.answer(lesson_text, reply_markup=keyboard, parse_mode="HTML")
    await callback_query.answer()
    
    logger.info(f"User {user_id} requested lesson {lesson['id']}")
