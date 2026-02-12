"""
Feedback handler - обратная связь по урокам
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.startswith("feedback:"))
async def callback_feedback(callback_query: CallbackQuery, db):
    """
    Обработать обратную связь по уроку.
    
    Формат: feedback:lesson_id:rating
    rating: clear (понятно) или hard (сложно)
    """
    try:
        _, lesson_id, rating = callback_query.data.split(":")
        lesson_id = int(lesson_id)
        user_id = callback_query.from_user.id
        
        # Сохраняем feedback
        await db.save_feedback(user_id, lesson_id, rating)
        
        # Помечаем урок как пройденный
        await db.mark_lesson_completed(user_id, lesson_id, feedback=rating)
        
        # Отправляем подтверждение
        if rating == "clear":
            response_text = "👍 Отлично! Рад, что было понятно."
            emoji = "✨"
        else:  # hard
            response_text = "❓ Понял, этот урок показался сложным. Мы учтём это!"
            emoji = "💪"
        
        # Обновляем сообщение, убирая кнопки feedback
        try:
            await callback_query.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass  # Сообщение может быть уже изменено
        
        await callback_query.answer(f"{emoji} {response_text}", show_alert=False)
        
        logger.info(f"User {user_id} gave feedback '{rating}' for lesson {lesson_id}")
    
    except Exception as e:
        logger.error(f"Failed to process feedback: {e}")
        await callback_query.answer("Произошла ошибка. Попробуй позже.", show_alert=True)
