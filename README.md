# 🚀 Деплой AI Portuguese Bot на Railway

## Что это?

Telegram-бот с **AI-генерацией уроков** через Claude API.
- ✅ Каждый урок уникален и персонализирован
- ✅ Claude адаптирует сложность под пользователя
- ✅ PostgreSQL для хранения прогресса
- ✅ Автодеплой на Railway

## Почему Railway?

- 🆓 Бесплатный тир ($5 кредитов в месяц)
- 🗄️ Встроенный PostgreSQL
- 🔄 Автодеплой из GitHub
- 🌍 Глобальная доступность

## Шаг 1: Подготовка

### 1.1 Создай Telegram бота

1. Открой [@BotFather](https://t.me/BotFather)
2. `/newbot`
3. Выбери имя: `Portuguese AI Tutor`
4. Username: `portuguese_ai_bot`
5. **Скопируй токен**: `1234567890:ABCdefGHI...`

### 1.2 Получи Anthropic API Key

1. Иди на https://console.anthropic.com
2. Войди или зарегистрируйся
3. API Keys → Create Key
4. **Скопируй ключ**: `sk-ant-api03-xxx...`

> 💰 **Цена:** ~$0.003 за урок (Sonnet 4). $5 = ~1600 уроков.

### 1.3 Создай GitHub репозиторий

```bash
# Распакуй бота
tar -xzf portuguese_ai_bot.tar.gz
cd portuguese_ai_bot

# Инициализируй git
git init
git add .
git commit -m "Initial commit"

# Создай репозиторий на GitHub
# Затем:
git remote add origin https://github.com/YOUR_USERNAME/portuguese-ai-bot.git
git branch -M main
git push -u origin main
```

## Шаг 2: Railway Setup

### 2.1 Создай проект

1. Иди на https://railway.app
2. Войди через GitHub
3. `New Project` → `Deploy from GitHub repo`
4. Выбери свой репозиторий

### 2.2 Добавь PostgreSQL

1. В проекте: `New` → `Database` → `Add PostgreSQL`
2. Railway автоматически создаст переменную `DATABASE_URL`

### 2.3 Установи переменные окружения

В Railway:
1. Выбери свой сервис (бот)
2. `Variables` → `Raw Editor`
3. Вставь:

```bash
BOT_TOKEN=1234567890:ABCdefGHI...
ANTHROPIC_API_KEY=sk-ant-api03-xxx...
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

> ⚠️ `DATABASE_URL` уже установлена Railway автоматически!

### 2.4 Задеплой

1. `Deploy` → Дождись окончания билда
2. Логи покажут:
```
Configuration loaded
Bot initialized  
Database connected
AI Generator initialized with model claude-sonnet-4-20250514
Bot started successfully!
```

3. ✅ Готово! Найди бота в Telegram и нажми `/start`

## Шаг 3: Проверка

### Проверь логи

В Railway → `Deployments` → `View Logs`

Должно быть:
```
INFO - Database connected
INFO - AI Generator initialized
INFO - Bot started successfully!
INFO - Scheduler running with 1 jobs
```

### Протестируй бота

1. Найди бота в Telegram
2. `/start` — должно показать приветствие
3. `📚 Получить урок` — должен прийти AI-сгенерированный урок

### Проверь PostgreSQL

В Railway → PostgreSQL → `Data`

Должны быть таблицы:
- `users`
- `lessons`

## Как это работает?

```
User нажимает кнопку
       ↓
Bot вызывает Claude API
       ↓
Claude генерирует урок
  (персонализированный!)
       ↓
Урок сохраняется в PostgreSQL
       ↓
Отправляется пользователю
       ↓
User оставляет feedback
       ↓
Следующий урок учтёт это
```

## Автоматическая рассылка

Scheduler запускается **каждый час** и:
1. Проверяет, каким пользователям пора отправить урок
2. Для каждого генерирует **персонализированный** урок через Claude
3. Учитывает:
   - Уровень пользователя
   - Пройденные темы
   - Сложные темы (по feedback)
4. Сохраняет в БД
5. Отправляет

## Мониторинг

### Просмотр логов

```bash
# В Railway
Deployments → View Logs
```

Фильтруй по:
- `✅ Sent AI lesson` — успешные отправки
- `ERROR` — ошибки
- `Generated lesson` — генерация уроков

### Проверка БД

В Railway → PostgreSQL → Query:

```sql
-- Активные пользователи
SELECT COUNT(*) FROM users WHERE is_active = true;

-- Всего уроков сгенерировано
SELECT COUNT(*) FROM lessons;

-- Последние уроки
SELECT user_id, topic, level, created_at 
FROM lessons 
ORDER BY created_at DESC 
LIMIT 10;

-- Статистика по feedback
SELECT 
  feedback,
  COUNT(*) as count
FROM lessons
WHERE feedback IS NOT NULL
GROUP BY feedback;
```

## Стоимость

### Railway
- 🆓 $5/месяц бесплатно
- Бот использует ~500MB RAM → вписывается в free tier
- PostgreSQL ~100MB → тоже бесплатно

### Anthropic API
- **Sonnet 4**: $3 / 1M input tokens, $15 / 1M output
- Один урок ≈ 1000 tokens ≈ **$0.003**
- 100 пользователей × 1 урок/день × 30 дней = 3000 уроков = **$9/месяц**

**Итого:** ~$9-14/месяц для 100 активных пользователей.

## Масштабирование

### Больше пользователей?

Railway автоскейлинг:
```
Settings → Resources → Auto-scaling
```

### Оптимизация стоимости

**1. Используй Haiku для простых тем:**
```python
# В config.py
ANTHROPIC_MODEL = "claude-haiku-4-20250514"  # $0.25 / 1M → $0.0003 за урок
```

**2. Кэшируй похожие уроки:**
```python
# Если тема уже генерировалась — используй из БД
cached = await db.get_cached_lesson(topic, level)
if cached:
    return cached
```

**3. Батч-генерация:**
Генерируй уроки пачками раз в день, а не по требованию.

## Troubleshooting

### Бот не запускается

**Ошибка: `BOT_TOKEN not set`**
→ Проверь переменные в Railway → Variables

**Ошибка: `DATABASE_URL not set`**  
→ Убедись, что PostgreSQL добавлен в проект

**Ошибка: `Failed to connect to database`**
→ Railway может перезапускать БД. Подожди 1-2 минуты.

### Уроки не генерируются

**В логах: `Failed to generate lesson`**
→ Проверь ANTHROPIC_API_KEY
→ Проверь баланс на Anthropic Console

**В логах: `Claude returned invalid JSON`**
→ Это редко, но случается. Бот retry автоматически.

### Уроки не отправляются

**Нет логов `Sent AI lesson`**
→ Проверь, что у пользователя `is_active = true` в БД
→ Проверь настройки времени (`/settings`)

## Обновление кода

```bash
# Локально
git add .
git commit -m "Updated feature X"
git push

# Railway автоматически задеплоит!
```

Логи покажут:
```
Building...
Deploying...
✓ Deployed successfully
```

## Бэкап БД

### Автобэкап в Railway

Railway автоматически делает snapshot каждый день.

### Ручной экспорт

```bash
# Скачай credentials
Railway → PostgreSQL → Connect → Connection String

# Экспорт
pg_dump $DATABASE_URL > backup.sql

# Восстановление
psql $DATABASE_URL < backup.sql
```

## Добавление фич

### Аудио произношение

```python
# Используй elevenlabs API
from elevenlabs import generate

audio = generate(
    text="Olá, tudo bem?",
    voice="Portuguese (BR)",
    model="eleven_multilingual_v2"
)
```

### Квизы после урока

```python
# Добавь в промпт генератора:
"quiz": [
  {
    "question": "Что правильно: procuram или procuravam?",
    "options": ["procuram", "procuravam"],
    "correct": 0,
    "explanation": "..."
  }
]
```

### Статистика в Telegram

```python
@router.message(Command("analytics"))
async def analytics(message: Message, db):
    stats = await db.get_global_stats()
    
    text = f"""
    📊 Глобальная статистика
    
    👥 Всего пользователей: {stats['total_users']}
    ✅ Активных: {stats['active_users']}
    📚 Уроков сгенерировано: {stats['total_lessons']}
    💰 Стоимость API: ${stats['api_cost']:.2f}
    """
    
    await message.answer(text)
```

## Поддержка

**Логи не помогли?**
1. Railway Discord: https://discord.gg/railway
2. Anthropic Support: support@anthropic.com
3. GitHub Issues в твоём репозитории

---

**Готово! Твой AI бот работает 24/7 на Railway** 🚀🇧🇷
