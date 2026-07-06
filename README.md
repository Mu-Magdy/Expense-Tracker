# AI Telegram Expense Tracker

A production-oriented Telegram bot that records expenses and income from **text** or **voice** messages. It uses OpenAI to extract structured transaction data, stores everything in a relational database, and provides spending reports via bot commands.

## Features

- **Text messages** — send natural language like `Paid 120 EGP for Uber` and the bot extracts amount, currency, merchant, category, and date
- **Voice messages** — transcribed with OpenAI Whisper, then processed through the same extraction pipeline
- **Reports** — query spending from the database (no LLM for reports)
- **Clean architecture** — Telegram handlers stay thin; business logic lives in services; AI modules have no Telegram dependencies

## Tech stack

- Python 3.13+
- [FastAPI-ready structure](expense_bot/) — bot runs via long polling today
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) v21+
- SQLAlchemy 2.0 (async) + Alembic migrations
- SQLite (development) or PostgreSQL (production)
- OpenAI — GPT for extraction, Whisper for voice
- Pydantic v2 for validation
- [uv](https://github.com/astral-sh/uv) for dependency management

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- A [Telegram bot token](https://t.me/BotFather)
- An [OpenAI API key](https://platform.openai.com/api-keys)

## Quick start

### 1. Clone and install

```bash
git clone <repository-url>
cd "Expense Tracker"
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

| Variable | Description |
|----------|-------------|
| `TELEGRAM_TOKEN` | Bot token from @BotFather |
| `OPENAI_API_KEY` | OpenAI API key |
| `DATABASE_URL` | Default: `sqlite+aiosqlite:///./expense.db` |
| `MODEL_NAME` | LLM for extraction (default: `gpt-4o-mini`) |
| `WHISPER_MODEL` | Speech model (default: `whisper-1`) |
| `LOG_LEVEL` | `INFO`, `DEBUG`, etc. |

### 3. Run migrations

```bash
uv run alembic upgrade head
```

### 4. Start the bot

```bash
uv run expense-bot
```

Send the bot a text or voice message describing a transaction.

## Bot commands

| Command | Description |
|---------|-------------|
| `/today` | Spending summary for today |
| `/week` | Summary for the current calendar week |
| `/month` | Summary for the current calendar month |
| `/categories` | Expense breakdown by category (this month) |
| `/search <term>` | Search merchant, category, or notes |
| `/undo` | Remove the most recently recorded transaction |

## Example

**You send:**
```
Paid 120 EGP for Uber ride today
```

**Bot replies:**
```
Recorded

Expense
120 EGP

Merchant
Uber

Category
Transport
```

## Project structure

```
expense_bot/
  app/
    main.py              # Entry point, logging, polling
    config.py            # Environment-based settings
    ai/
      extractor.py       # LLM transaction extraction
      whisper.py         # Speech-to-text (swappable protocol)
      prompts.py
    database/
      models.py          # SQLAlchemy ORM
      repository.py      # Data access
      session.py         # Async engine / sessions
    schemas/
      transaction.py     # Pydantic extraction schema
    services/
      transaction_service.py
      report_service.py
    telegram/
      bot.py             # Application factory
      handlers.py        # Thin update handlers
migrations/              # Alembic migrations
```

## Architecture

```
Telegram handlers  →  Services  →  Repository  →  Database
                         ↓
                    AI (extract / transcribe)
```

Handlers only orchestrate Telegram I/O. Services own business logic. The AI layer is Telegram-agnostic and uses protocols so providers can be swapped.

## Database

**Development (SQLite):**

```
DATABASE_URL=sqlite+aiosqlite:///./expense.db
```

**Production (PostgreSQL):**

```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/expense_tracker
```

Apply migrations after changing `DATABASE_URL`:

```bash
uv run alembic upgrade head
```

## Development

```bash
# Install dependencies
uv sync

# Run bot
uv run expense-bot

# Create a new migration (after model changes)
uv run alembic revision --autogenerate -m "description"

# Roll back one migration
uv run alembic downgrade -1
```

