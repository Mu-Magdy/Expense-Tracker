"""Telegram update handlers."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from expense_bot.app.services.report_service import ReportService
from expense_bot.app.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


class TelegramHandlers:
    """Thin handlers that delegate business logic to services."""

    def __init__(
        self,
        transaction_service: TransactionService,
        report_service: ReportService,
    ) -> None:
        self._transaction_service = transaction_service
        self._report_service = report_service

    def _user_id(self, update: Update) -> int:
        """Return the Telegram user id from an update."""
        return update.effective_user.id if update.effective_user else 0

    async def text_message_handler(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle incoming text messages."""
        message = update.effective_message
        if message is None or message.text is None:
            return

        user_id = self._user_id(update)
        logger.info("Received text from user_id=%s: %s", user_id, message.text)

        reply = await self._transaction_service.process_text(user_id, message.text)
        await message.reply_text(reply)

    async def voice_message_handler(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle incoming voice messages."""
        message = update.effective_message
        if message is None or message.voice is None:
            return

        user_id = self._user_id(update)
        logger.info("Received voice from user_id=%s", user_id)

        tg_file = await message.voice.get_file()
        audio = bytes(await tg_file.download_as_bytearray())

        reply = await self._transaction_service.process_voice(user_id, audio)
        await message.reply_text(reply)

    async def today_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle the /today command."""
        message = update.effective_message
        if message is None:
            return
        reply = await self._report_service.today_report(self._user_id(update))
        await message.reply_text(reply)

    async def week_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle the /week command."""
        message = update.effective_message
        if message is None:
            return
        reply = await self._report_service.week_report(self._user_id(update))
        await message.reply_text(reply)

    async def month_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle the /month command."""
        message = update.effective_message
        if message is None:
            return
        reply = await self._report_service.month_report(self._user_id(update))
        await message.reply_text(reply)

    async def categories_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle the /categories command."""
        message = update.effective_message
        if message is None:
            return
        reply = await self._report_service.categories_report(self._user_id(update))
        await message.reply_text(reply)

    async def search_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle the /search command."""
        message = update.effective_message
        if message is None:
            return
        query = " ".join(context.args) if context.args else ""
        reply = await self._report_service.search_report(self._user_id(update), query)
        await message.reply_text(reply)

    async def undo_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle the /undo command."""
        message = update.effective_message
        if message is None:
            return
        reply = await self._report_service.undo_last(self._user_id(update))
        await message.reply_text(reply)
