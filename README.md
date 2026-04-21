Telegram-бот для анкет. ИИ-модерация

Микросервис: анкеты игроков, модерация через AI, система лайков.

**Стек:** FastAPI + aiogram 3 + PostgreSQL + OpenAI GPT-4o-mini + Docker

---

## Быстрый старт

### 1. Переменные окружения

Создай `.env` в корне проекта:

```env
BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=sk-...

DB_HOST=db
DB_PORT=5432
DB_USER=admin
DB_PASSWORD=your_password
DB_NAME=telegram_bot_service
```

### 2. Запуск через Docker Compose

```bash
docker-compose up --build
```

Сервисы:
- **bot** — FastAPI + aiogram polling, порт `8003`
- **db** — PostgreSQL 15, порт `5435` (внешний)

### 3. Запуск для разработки (без Docker)

```bash
pip install -r requirements.txt
python main.py
```

Требует локальный PostgreSQL и все переменные из `.env`.

---

## Структура проекта

```
game-agent/
├── main.py                  # Точка входа: FastAPI + bot polling
├── migrations.py            # Инициализация схемы БД
├── docker-compose.yml
├── Dockerfile.dev
├── requirements.txt
│
├── config/
│   ├── bot.py               # Bot & Dispatcher (aiogram)
│   ├── database.py          # SQLAlchemy async engine
│   ├── access.py            # ID админов
│   └── form.py              # Данные игры: ранги, тиры, типы поиска
│
├── handlers/
│   ├── commands.py          # Общие команды (/start, /watch, /likes)
│   ├── form/fsm.py          # FSM создания анкеты
│   └── admin/               # Админские команды и FSM
│
├── services/
│   ├── moderation.py        # AI-модерация фото и текста
│   ├── form.py              # Бизнес-логика анкет
│   ├── scheduler.py         # Фоновые задачи (APScheduler)
│   └── telegram.py          # Отправка сообщений
│
├── models/                  # SQLAlchemy ORM модели
├── keyboards/               # Inline и reply-клавиатуры
├── routes/routes.py         # FastAPI endpoints
│
├── tests/
│   └── test_moderation_rules.py
│
└── src/media/               # Медиафайлы бота (mp4, png)
```

---

## Тесты

### Запуск

```bash
pip install pytest
pytest tests/ -v
```

### Структура тестов

Файл: `tests/test_moderation_rules.py`

Тестирует **алгоритмическую часть модерации** — без вызовов OpenAI, без сети, без бота.
Покрывает функцию `_check_text_rules()` и регулярные выражения `_TEXT_BAN_RE`, `_FLOOD_RE`.

| Класс | Что тестирует |
|-------|---------------|
| `TestLinks` | Блокировка URL, t.me, @username |
| `TestPhones` | Блокировка номеров RU в разных форматах |
| `TestFlood` | Флуд: одинаковые символы 6+ раз подряд |
| `TestLength` | Лимит 500 символов |
| `TestEdgeCases` | Граничные случаи, unicode-флуд, обфускация |

**34 теста, время выполнения < 1 сек.**

Пример:
```bash
pytest tests/test_moderation_rules.py -v
# ✓ TestLinks::test_http_url
# ✓ TestPhones::test_ru_mobile_dashes
# ✓ TestFlood::test_repeated_char_6
# ...
```

---

## Модерация: архитектура и затраты OpenAI

### Как работает модерация

При создании анкеты вызывается `moderate_form(photo_file_id, description)`:

```
Входящая анкета
       │
       ▼
_check_text_rules()   ← regex: ссылки, телефоны, флуд, длина
       │ ОК
       ▼
asyncio.gather(
  moderate_photo(),   ← GPT-4o-mini + vision (фото профиля)
  moderate_text(),    ← GPT-4o-mini (описание)
)
```

- Если regex отклоняет текст — AI вообще не вызывается
- Фото и текст проверяются **параллельно**
- При ошибке OpenAI — анкета **пропускается** (fail-open)

### Оптимизации

- Фото ресайзится до **384×384 px**, JPEG 60% — ~15–25 КБ вместо 200–500 КБ
- `detail: "low"` для vision — фиксированная стоимость вне зависимости от размера
- Текст обрезается до **300 символов** перед отправкой в AI
- `max_tokens: 60` — ответ только JSON `{"ok":bool,"reason":""}`

### Затраты GPT-4o-mini (актуальные цены)

| Операция | Модель | Токены (вход) | Токены (выход) | Стоимость |
|----------|--------|--------------|----------------|-----------|
| Модерация фото | gpt-4o-mini | ~300 (prompt) + 85 (image low) | ~20 | ~$0.00007 |
| Модерация текста | gpt-4o-mini | ~120 (system) + ~60 (text) | ~20 | ~$0.000027 |
| **Итого за анкету** | | ~565 | ~40 | **~$0.0001** |

> Цены gpt-4o-mini: $0.15 / 1M input tokens, $0.60 / 1M output tokens

### Месячный расчёт

| Анкет/день | Анкет/месяц | Затраты/месяц |
|------------|-------------|---------------|
| 100 | 3 000 | ~$0.30 |
| 500 | 15 000 | ~$1.50 |
| 2 000 | 60 000 | ~$6.00 |

**Экономия за счёт regex pre-check:** если ~30% анкет отклоняется на этапе regex (ссылки, телефоны), то реальные затраты на AI ниже примерно на треть.

---

## API

`GET /health` — проверка состояния сервиса
