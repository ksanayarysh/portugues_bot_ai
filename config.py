"""
Configuration for AI-Powered Portuguese Learning Bot
"""
import os
from pathlib import Path


class Config:
    """Конфигурация бота."""
    
    # === Telegram ===
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # === Anthropic API ===
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    MAX_TOKENS: int = 2000
    
    # === PostgreSQL (Railway автоматически предоставляет DATABASE_URL) ===
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # === Настройки рассылки ===
    DEFAULT_LESSON_HOUR: int = int(os.getenv("DEFAULT_LESSON_HOUR", "9"))
    DEFAULT_LESSON_MINUTE: int = int(os.getenv("DEFAULT_LESSON_MINUTE", "0"))
    
    # Частоты рассылки (в днях)
    FREQUENCIES = {
        "twice_daily": 0.5,
        "daily": 1,
        "every_2_days": 2,
        "twice_week": 3.5,
        "weekly": 7,
    }
    
    FREQUENCY_LABELS = {
        "twice_daily": "2 раза в день",
        "daily": "Каждый день",
        "every_2_days": "Раз в 2 дня",
        "twice_week": "2 раза в неделю",
        "weekly": "Раз в неделю",
    }
    
    # === Темы уроков (для AI генерации) ===
    LESSON_TOPICS = [
        "subjuntivo_presente_vs_imperfeito",
        "por_vs_para",
        "ser_vs_estar",
        "que_vs_o_que",
        "diminutivos",
        "false_cognates",
        "brazilian_slang",
        "pronunciation_r",
        "pronunciation_nasal",
        "verb_conjugation",
        "prepositions",
        "brazilian_vs_european",
        "contractions",
        "indirect_speech",
        "phrasal_verbs",
        "idiomatic_expressions",
        "formal_vs_informal",
        "gerundio_usage",
        "imperative_mood",
        "conditional_tenses",
    ]
    
    # === Уровни сложности ===
    DIFFICULTY_LEVELS = ["beginner", "intermediate", "advanced"]
    
    def __init__(self):
        """Проверка конфигурации."""
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN not set")
        
        if not self.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL not set (Railway should provide this)")
