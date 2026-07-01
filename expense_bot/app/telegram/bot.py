"""Telegram bot application factory."""

from __future__ import annotations

from telegram.ext import Application, ApplicationBuilder, MessageHandler, filters

from expense_bot.app.ai.extractor import create_openai_extractor
from expense_bot.app.config import Settings
from expense_bot.app.database.session import create_engine, create_session_factory
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
    transaction_service = TransactionService(extractor, session_factory)
    handlers = TelegramHandlers(transaction_service)

    application = (
        ApplicationBuilder()
        .token(settings.telegram_token)
        .build()
    )

    application.bot_data["engine"] = engine

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.text_message_handler)
    )

    return application
