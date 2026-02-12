"""
AI Lesson Generator - генерация уроков через Anthropic Claude API
"""
import logging
from typing import Dict, Any, Optional
import anthropic
import json

logger = logging.getLogger(__name__)


class LessonGenerator:
    """Генератор уроков через Claude API."""
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        Инициализация генератора.
        
        Args:
            api_key: Anthropic API key
            model: Модель Claude
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
    
    def generate_lesson(
        self,
        topic: str,
        level: str = "intermediate",
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Сгенерировать урок по теме.
        
        Args:
            topic: Тема урока (например, "subjuntivo_presente_vs_imperfeito")
            level: Уровень сложности (beginner, intermediate, advanced)
            user_context: Дополнительный контекст о пользователе (пройденные уроки, сложности)
            
        Returns:
            Dict с уроком в структурированном формате
        """
        prompt = self._build_prompt(topic, level, user_context)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Извлекаем текст ответа
            lesson_json = response.content[0].text
            
            # Парсим JSON (Claude должен вернуть валидный JSON)
            lesson = json.loads(lesson_json)
            
            logger.info(f"Generated lesson for topic '{topic}', level '{level}'")
            return lesson
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse lesson JSON: {e}")
            logger.error(f"Raw response: {response.content[0].text}")
            raise ValueError("Claude returned invalid JSON")
        
        except Exception as e:
            logger.error(f"Failed to generate lesson: {e}")
            raise
    
    def _build_prompt(
        self,
        topic: str,
        level: str,
        user_context: Optional[Dict[str, Any]]
    ) -> str:
        """Построить промпт для генерации урока."""
        
        # Маппинг тем на описания
        topic_descriptions = {
            "subjuntivo_presente_vs_imperfeito": "Когда использовать Presente do Subjuntivo vs Imperfeito do Subjuntivo",
            "por_vs_para": "Разница между предлогами POR и PARA",
            "ser_vs_estar": "Разница между глаголами SER и ESTAR",
            "que_vs_o_que": "Когда использовать QUE vs O QUE",
            "diminutivos": "Уменьшительные суффиксы -inho/-inha и их культурное значение",
            "false_cognates": "Ложные друзья переводчика (слова похожие на русские/английские, но с другим значением)",
            "brazilian_slang": "Бразильский сленг и разговорные выражения",
            "pronunciation_r": "Произношение буквы R в разных позициях",
            "pronunciation_nasal": "Носовые звуки в португальском",
            "verb_conjugation": "Спряжение глаголов",
            "prepositions": "Предлоги и их использование",
            "brazilian_vs_european": "Различия между бразильским и европейским португальским",
            "contractions": "Контракции (ao, do, pelo и т.д.)",
            "indirect_speech": "Косвенная речь",
            "phrasal_verbs": "Фразовые глаголы",
            "idiomatic_expressions": "Идиоматические выражения",
            "formal_vs_informal": "Формальная и неформальная речь",
            "gerundio_usage": "Использование герундия",
            "imperative_mood": "Повелительное наклонение",
            "conditional_tenses": "Условные времена",
        }
        
        topic_description = topic_descriptions.get(topic, topic.replace("_", " "))
        
        # Контекст о пользователе
        context_info = ""
        if user_context:
            if user_context.get("completed_topics"):
                context_info += f"\nПользователь уже изучил: {', '.join(user_context['completed_topics'])}"
            if user_context.get("difficult_topics"):
                context_info += f"\nПользователю были сложны: {', '.join(user_context['difficult_topics'])}"
        
        prompt = f"""Ты — преподаватель португальского языка (бразильский вариант).

Создай короткий практический урок на тему: "{topic_description}"

Уровень: {level}
{context_info}

КРИТИЧЕСКИ ВАЖНО: Верни ТОЛЬКО валидный JSON без пояснений, без markdown-блоков, без текста до или после.

Формат урока:

{{
  "title": "🇧🇷 Заголовок урока (эмодзи + короткое название)",
  "explanation": "Простое объяснение темы 2-3 предложения. Используй аналогии и простой язык.",
  "examples": [
    {{
      "portuguese": "Пример на португальском",
      "russian": "Перевод на русский",
      "note": "Краткое пояснение (почему именно так)"
    }},
    {{
      "portuguese": "Второй пример (контрастный или дополнительный)",
      "russian": "Перевод",
      "note": "Пояснение"
    }}
  ],
  "tip": "Полезный совет или мнемоническое правило (опционально)",
  "cultural_note": "Культурный контекст или особенность использования (опционально)",
  "practice": "Упражнение для самопроверки с ответом. Формат: 'Вопрос... Ответ: правильный_ответ'"
}}

ТРЕБОВАНИЯ:
1. Примеры должны быть из реальной жизни, не учебные
2. Используй современный разговорный бразильский португальский
3. Объяснения короткие и понятные
4. 2-3 примера максимум (урок должен занимать 3-5 минут чтения)
5. Если есть распространённые ошибки — укажи их
6. ТОЛЬКО JSON, никакого другого текста

Пример качественного урока:

{{
  "title": "🇧🇷 Subjuntivo: когда nasçam, а когда nascessem?",
  "explanation": "Главное правило: смотрим на время главного глагола! Если главный глагол в настоящем/будущем → Presente do Subjuntivo. Если в прошедшем → Imperfeito do Subjuntivo.",
  "examples": [
    {{
      "portuguese": "Eles procuram um homem diferente para que as crianças nasçam saudáveis.",
      "russian": "Они ищут другого мужчину, чтобы дети родились здоровыми.",
      "note": "procuram (настоящее) → nasçam (Presente do Subjuntivo)"
    }},
    {{
      "portuguese": "Eles procuravam um homem diferente para que as crianças nascessem saudáveis.",
      "russian": "Они искали другого мужчину, чтобы дети родились здоровыми.",
      "note": "procuravam (прошедшее) → nascessem (Imperfeito do Subjuntivo)"
    }}
  ],
  "tip": "Согласование времён работает механически: настоящее → настоящее subjuntivo, прошедшее → прошедшее subjuntivo.",
  "practice": "Eu quero que você ___ (falar) português! Ответ: fale (quero в настоящем времени)"
}}

Теперь создай урок на тему "{topic_description}" уровня {level}.
"""
        
        return prompt
    
    def generate_personalized_lesson(
        self,
        user_stats: Dict[str, Any],
        previous_lessons: list[str]
    ) -> Dict[str, Any]:
        """
        Сгенерировать персонализированный урок на основе прогресса пользователя.
        
        Args:
            user_stats: Статистика пользователя (сложные темы, уровень и т.д.)
            previous_lessons: Список тем предыдущих уроков
            
        Returns:
            Dict с уроком
        """
        # Определяем следующую тему
        from config import Config
        config = Config()
        
        # Исключаем уже пройденные темы
        available_topics = [t for t in config.LESSON_TOPICS if t not in previous_lessons]
        
        if not available_topics:
            # Все темы пройдены - начинаем заново с более сложного уровня
            available_topics = config.LESSON_TOPICS
            next_level = self._get_next_level(user_stats.get('level', 'beginner'))
        else:
            next_level = user_stats.get('level', 'intermediate')
        
        # Берём первую доступную тему
        next_topic = available_topics[0]
        
        # Генерируем урок
        user_context = {
            "completed_topics": previous_lessons[-5:] if len(previous_lessons) > 5 else previous_lessons,
            "difficult_topics": user_stats.get('difficult_topics', [])
        }
        
        lesson = self.generate_lesson(next_topic, next_level, user_context)
        
        # Добавляем тему в результат для сохранения в БД
        lesson['_topic'] = next_topic
        lesson['_level'] = next_level
        
        return lesson
    
    def _get_next_level(self, current_level: str) -> str:
        """Определить следующий уровень сложности."""
        level_progression = {
            "beginner": "intermediate",
            "intermediate": "advanced",
            "advanced": "advanced"  # остаёмся на продвинутом
        }
        return level_progression.get(current_level, "intermediate")
