"""
PostgreSQL Database module for AI Portuguese Bot
"""
import asyncpg
import logging
from datetime import datetime, date
from typing import Optional, List, Dict, Any
import json

logger = logging.getLogger(__name__)


class Database:
    """PostgreSQL database для бота."""
    
    def __init__(self, database_url: str):
        """
        Инициализация БД.
        
        Args:
            database_url: PostgreSQL connection URL (Railway предоставляет автоматически)
        """
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
    
    async def init_db(self) -> None:
        """Создать connection pool и таблицы."""
        try:
            self.pool = await asyncpg.create_pool(
                dsn=self.database_url,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            
            async with self.pool.acquire() as conn:
                # Создаём таблицы
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        language_code TEXT,
                        frequency TEXT DEFAULT 'daily',
                        lesson_hour INTEGER DEFAULT 9,
                        lesson_minute INTEGER DEFAULT 0,
                        timezone TEXT DEFAULT 'UTC',
                        level TEXT DEFAULT 'intermediate',
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        last_lesson_at TIMESTAMPTZ,
                        total_lessons INTEGER DEFAULT 0
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS lessons (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                        topic TEXT NOT NULL,
                        level TEXT NOT NULL,
                        content JSONB NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        feedback TEXT,
                        completed_at TIMESTAMPTZ
                    )
                """)
                
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_lessons_user_id ON lessons(user_id)
                """)
                
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_lessons_topic ON lessons(topic)
                """)
                
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)
                """)
            
            logger.info("Database initialized successfully")
        
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def close(self) -> None:
        """Закрыть pool."""
        if self.pool:
            await self.pool.close()
    
    # ==================== Users ====================
    
    async def add_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        language_code: Optional[str] = None
    ) -> None:
        """Добавить или обновить пользователя."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users (user_id, username, first_name, language_code)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    language_code = EXCLUDED.language_code
                """,
                user_id, username, first_name, language_code
            )
        logger.info(f"User {user_id} added/updated")
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить пользователя."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE user_id = $1",
                user_id
            )
            return dict(row) if row else None
    
    async def update_user_settings(
        self,
        user_id: int,
        frequency: Optional[str] = None,
        lesson_hour: Optional[int] = None,
        lesson_minute: Optional[int] = None,
        timezone: Optional[str] = None,
        level: Optional[str] = None
    ) -> None:
        """Обновить настройки пользователя."""
        updates = []
        params = []
        param_count = 1
        
        if frequency is not None:
            updates.append(f"frequency = ${param_count}")
            params.append(frequency)
            param_count += 1
        
        if lesson_hour is not None:
            updates.append(f"lesson_hour = ${param_count}")
            params.append(lesson_hour)
            param_count += 1
        
        if lesson_minute is not None:
            updates.append(f"lesson_minute = ${param_count}")
            params.append(lesson_minute)
            param_count += 1
        
        if timezone is not None:
            updates.append(f"timezone = ${param_count}")
            params.append(timezone)
            param_count += 1
        
        if level is not None:
            updates.append(f"level = ${param_count}")
            params.append(level)
            param_count += 1
        
        if updates:
            params.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ${param_count}"
            
            async with self.pool.acquire() as conn:
                await conn.execute(query, *params)
            
            logger.info(f"Updated settings for user {user_id}")
    
    async def set_user_active(self, user_id: int, is_active: bool) -> None:
        """Включить/выключить рассылку."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET is_active = $1 WHERE user_id = $2",
                is_active, user_id
            )
    
    async def get_active_users(self) -> List[Dict[str, Any]]:
        """Получить активных пользователей."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM users WHERE is_active = TRUE"
            )
            return [dict(row) for row in rows]
    
    async def update_last_lesson_time(self, user_id: int) -> None:
        """Обновить время последнего урока."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE users 
                SET last_lesson_at = NOW(), total_lessons = total_lessons + 1
                WHERE user_id = $1
                """,
                user_id
            )
    
    # ==================== Lessons ====================
    
    async def save_lesson(
        self,
        user_id: int,
        topic: str,
        level: str,
        content: Dict[str, Any]
    ) -> int:
        """
        Сохранить сгенерированный урок.
        
        Args:
            user_id: User ID
            topic: Тема урока
            level: Уровень
            content: JSON с содержимым урока
            
        Returns:
            Lesson ID
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO lessons (user_id, topic, level, content)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                user_id, topic, level, asyncpg.types.Json(content)
            )
            lesson_id = row['id']
            logger.info(f"Saved lesson {lesson_id} for user {user_id}, topic: {topic}")
            return lesson_id
    
    async def mark_lesson_completed(
        self,
        lesson_id: int,
        feedback: Optional[str] = None
    ) -> None:
        """Пометить урок как завершённый."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE lessons
                SET completed_at = NOW(), feedback = $2
                WHERE id = $1
                """,
                lesson_id, feedback
            )
    
    async def get_user_lessons(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить уроки пользователя."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, topic, level, content, created_at, feedback, completed_at
                FROM lessons
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                user_id, limit
            )
            return [dict(row) for row in rows]
    
    async def get_completed_topics(self, user_id: int) -> List[str]:
        """Получить список пройденных тем."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT DISTINCT topic
                FROM lessons
                WHERE user_id = $1 AND completed_at IS NOT NULL
                ORDER BY topic
                """,
                user_id
            )
            return [row['topic'] for row in rows]
    
    async def get_difficult_topics(self, user_id: int) -> List[str]:
        """Получить темы, которые были сложны (feedback = 'hard')."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT DISTINCT topic
                FROM lessons
                WHERE user_id = $1 AND feedback = 'hard'
                """,
                user_id
            )
            return [row['topic'] for row in rows]
    
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Получить статистику пользователя."""
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE user_id = $1",
                user_id
            )
            
            lessons_stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total_lessons,
                    COUNT(CASE WHEN completed_at IS NOT NULL THEN 1 END) as completed,
                    COUNT(CASE WHEN feedback = 'clear' THEN 1 END) as clear_count,
                    COUNT(CASE WHEN feedback = 'hard' THEN 1 END) as hard_count
                FROM lessons
                WHERE user_id = $1
                """,
                user_id
            )

            result = {}
            if user:
                result.update(dict(user))
            if lessons_stats:
                result.update(dict(lessons_stats))
            return result

    async def get_today_topics(self, user_id: int, day: str | None = None) -> List[str]:
        """
        Темы, которые уже выдавались пользователю СЕГОДНЯ (по UTC-датe, если не указано иначе).
        day: 'YYYY-MM-DD' (опционально)
        """
        if day is None:
            day = date.today().isoformat()

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT DISTINCT topic
                FROM lessons
                WHERE user_id = $1
                  AND created_at::date = $2::date
                ORDER BY topic
                """,
                user_id, day
            )
            return [r["topic"] for r in rows]

    async def get_recent_lesson_topics(self, user_id: int, limit: int = 500) -> List[str]:
        """
        Темы, которые уже выдавались пользователю (самые свежие сверху).
        Это лучше, чем completed_topics, потому что у тебя feedback/completed может быть не всегда.
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT topic
                FROM lessons
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                user_id, limit
            )
            return [r["topic"] for r in rows]

    async def save_today_topic(self, user_id: int, day: str, topic: str) -> None:
        """
        Ничего отдельного не сохраняем: сам факт "тема выдана сегодня" фиксируется строкой lessons.
        Этот метод оставлен, потому что твой start.py его зовёт.
        Здесь можно просто no-op или проверку, но лучше вообще не использовать его отдельно.
        """
        # Ничего не делаем: это уже фиксируется в lessons при save_lesson()
        return