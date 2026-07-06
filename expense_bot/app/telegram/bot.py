"""Telegram bot application factory."""

from __future__ import annotations

from telegram.ext import Application, ApplicationBuilder, CommandHandler, MessageHandler, filters

from expense_bot.app.ai.extractor import create_openai_extractor
from expense_bot.app.ai.whisper import create_openai_transcriber
from expense_bot.app.config import Settings
from expense_bot.app.database.session import create_engine, create_session_factory
from expense_bot.app.services.report_service import ReportService
from expense_bot.app.services.transaction_service import TransactionService
from expense_bot.app.telegram.handlers import TelegramHandlers


def create_application(settings: Settings) -> Application:
    """Build and configure the Telegram bot application.

    Args:
        settings: Application settings containing the bot token.

    Returns:
        Configured python-telegram-bot Application instance.
    """
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    extractor = create_openai_extractor(settings)
    transcriber = create_openai_transcriber(settings)
    transaction_service = TransactionService(extractor, session_factory, transcriber)
    report_service = ReportService(session_factory)
    handlers = TelegramHandlers(transaction_service, report_service)

    application = (
        ApplicationBuilder()
        .token(settings.telegram_token)
        .build()
    )

    application.bot_data["engine"] = engine

    application.add_handler(CommandHandler("today", handlers.today_command))
    application.add_handler(CommandHandler("week", handlers.week_command))
    application.add_handler(CommandHandler("month", handlers.month_command))
    application.add_handler(CommandHandler("categories", handlers.categories_command))
    application.add_handler(CommandHandler("search", handlers.search_command))
    application.add_handler(CommandHandler("undo", handlers.undo_command))

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.text_message_handler)
    )
    application.add_handler(
        MessageHandler(filters.VOICE, handlers.voice_message_handler)
    )

    return application
