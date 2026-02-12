"""
Settings handler - настройки частоты и времени уроков
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

logger = logging.getLogger(__name__)
router = Router()


class SettingsStates(StatesGroup):
    """Состояния для настройки."""
    choosing_frequency = State()
    choosing_time = State()


@router.message(Command("settings"))
@router.callback_query(F.data == "open_settings")
async def cmd_settings(event: Message | CallbackQuery, db, config):
    """Открыть меню настроек."""
    user_id = event.from_user.id
    user_data = await db.get_user(user_id)
    
    if not user_data:
        text = "Сначала начни работу с ботом — /start"
        if isinstance(event, Message):
            await event.answer(text)
        else:
            await event.answer(text, show_alert=True)
        return
    
    current_frequency = user_data.get('frequency', 'daily')
    current_hour = user_data.get('lesson_hour', 9)
    current_minute = user_data.get('lesson_minute', 0)
    is_active = user_data.get('is_active', True)
    
    settings_text = (
        "⚙️ <b>Настройки уроков</b>\n\n"
        f"📅 Частота: <b>{config.FREQUENCY_LABELS.get(current_frequency, current_frequency)}</b>\n"
        f"🕐 Время: <b>{current_hour:02d}:{current_minute:02d}</b> UTC\n"
        f"✅ Статус: <b>{'Включено' if is_active else 'Выключено'}</b>\n\n"
        "Что хочешь изменить?"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📅 Изменить частоту",
                callback_data="change_frequency"
            )
        ],
        [
            InlineKeyboardButton(
                text="🕐 Изменить время",
                callback_data="change_time"
            )
        ],
        [
            InlineKeyboardButton(
                text="⏸ Приостановить" if is_active else "▶️ Возобновить",
                callback_data="toggle_active"
            )
        ]
    ])
    
    if isinstance(event, Message):
        await event.answer(settings_text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await event.message.edit_text(settings_text, reply_markup=keyboard, parse_mode="HTML")
        await event.answer()


@router.callback_query(F.data == "change_frequency")
async def callback_change_frequency(callback_query: CallbackQuery, config):
    """Выбор частоты уроков."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"2 раза в день",
                callback_data="freq:twice_daily"
            )
        ],
        [
            InlineKeyboardButton(
                text="Каждый день ⭐",
                callback_data="freq:daily"
            )
        ],
        [
            InlineKeyboardButton(
                text="Раз в 2 дня",
                callback_data="freq:every_2_days"
            )
        ],
        [
            InlineKeyboardButton(
                text="2 раза в неделю",
                callback_data="freq:twice_week"
            )
        ],
        [
            InlineKeyboardButton(
                text="Раз в неделю",
                callback_data="freq:weekly"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="open_settings"
            )
        ]
    ])
    
    await callback_query.message.edit_text(
        "📅 <b>Выбери частоту уроков:</b>\n\n"
        "Рекомендуется начинать с ежедневных уроков для лучшего результата!",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback_query.answer()


@router.callback_query(F.data.startswith("freq:"))
async def callback_set_frequency(callback_query: CallbackQuery, db, config):
    """Сохранить выбранную частоту."""
    frequency = callback_query.data.split(":")[1]
    user_id = callback_query.from_user.id
    
    await db.update_user_settings(user_id, frequency=frequency)
    
    await callback_query.answer(
        f"✅ Частота изменена: {config.FREQUENCY_LABELS[frequency]}",
        show_alert=True
    )
    
    # Возвращаемся в меню настроек
    await cmd_settings(callback_query, db, config)
    
    logger.info(f"User {user_id} changed frequency to {frequency}")


@router.callback_query(F.data == "change_time")
async def callback_change_time(callback_query: CallbackQuery):
    """Изменить время уроков."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌅 6:00", callback_data="time:6:0"),
            InlineKeyboardButton(text="🌄 7:00", callback_data="time:7:0")
        ],
        [
            InlineKeyboardButton(text="☀️ 8:00", callback_data="time:8:0"),
            InlineKeyboardButton(text="☀️ 9:00", callback_data="time:9:0")
        ],
        [
            InlineKeyboardButton(text="☀️ 10:00", callback_data="time:10:0"),
            InlineKeyboardButton(text="🌤 12:00", callback_data="time:12:0")
        ],
        [
            InlineKeyboardButton(text="🌤 14:00", callback_data="time:14:0"),
            InlineKeyboardButton(text="🌤 16:00", callback_data="time:16:0")
        ],
        [
            InlineKeyboardButton(text="🌆 18:00", callback_data="time:18:0"),
            InlineKeyboardButton(text="🌃 20:00", callback_data="time:20:0")
        ],
        [
            InlineKeyboardButton(text="🌙 22:00", callback_data="time:22:0"),
            InlineKeyboardButton(text="🌙 23:00", callback_data="time:23:0")
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="open_settings")
        ]
    ])
    
    await callback_query.message.edit_text(
        "🕐 <b>Выбери время получения уроков</b>\n\n"
        "⏰ Указано время по UTC (всемирное координированное время)\n\n"
        "Для Бразилии (Сан-Паулу): UTC-3\n"
        "Например, 12:00 UTC = 09:00 по Бразилии",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback_query.answer()


@router.callback_query(F.data.startswith("time:"))
async def callback_set_time(callback_query: CallbackQuery, db):
    """Сохранить выбранное время."""
    _, hour, minute = callback_query.data.split(":")
    hour = int(hour)
    minute = int(minute)
    user_id = callback_query.from_user.id
    
    await db.update_user_settings(
        user_id,
        lesson_hour=hour,
        lesson_minute=minute
    )
    
    await callback_query.answer(
        f"✅ Время изменено: {hour:02d}:{minute:02d} UTC",
        show_alert=True
    )
    
    # Возвращаемся в меню настроек
    from bot.handlers.start import cmd_settings as settings_func
    await settings_func(callback_query, db, callback_query.bot.get("config"))
    
    logger.info(f"User {user_id} changed time to {hour}:{minute}")


@router.callback_query(F.data == "toggle_active")
async def callback_toggle_active(callback_query: CallbackQuery, db, config):
    """Включить/выключить рассылку."""
    user_id = callback_query.from_user.id
    user_data = await db.get_user(user_id)
    
    new_status = not user_data.get('is_active', True)
    await db.set_user_active(user_id, new_status)
    
    status_text = "включена" if new_status else "приостановлена"
    await callback_query.answer(
        f"✅ Рассылка {status_text}",
        show_alert=True
    )
    
    # Обновляем меню настроек
    await cmd_settings(callback_query, db, config)
    
    logger.info(f"User {user_id} toggled active to {new_status}")
