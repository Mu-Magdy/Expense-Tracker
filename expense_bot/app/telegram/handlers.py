"""Telegram update handlers."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from expense_bot.app.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


class TelegramHandlers:
    """Thin handlers that delegate business logic to services."""

    def __init__(self, transaction_service: TransactionService) -> None:
        self._transaction_service = transaction_service

    async def text_message_handler(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle incoming text messages."""
        message = update.effective_message
        if message is None or message.text is None:
            return

        user_id = update.effective_user.id if update.effective_user else 0
        logger.info("Received text from user_id=%s: %s", user_id, message.text)

        reply = await self._transaction_service.process_text(user_id, message.text)
        await message.reply_text(reply)
