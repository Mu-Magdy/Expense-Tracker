"""Transaction processing business logic."""

from __future__ import annotations

import logging
from decimal import Decimal

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from expense_bot.app.ai.extractor import ExtractionError, TransactionExtractor
from expense_bot.app.ai.whisper import SpeechTranscriber, TranscriptionError
from expense_bot.app.database.repository import TransactionRepository
from expense_bot.app.schemas.transaction import ExtractedTransaction

logger = logging.getLogger(__name__)


class TransactionService:
    """Orchestrates extraction, validation, and persistence of transactions."""

    def __init__(
        self,
        extractor: TransactionExtractor,
        session_factory: async_sessionmaker[AsyncSession],
        transcriber: SpeechTranscriber,
    ) -> None:
        self._extractor = extractor
        self._session_factory = session_factory
        self._transcriber = transcriber

    async def process_text(self, telegram_user_id: int, text: str) -> str:
        """Extract a transaction from text, save it, and return a confirmation.

        Args:
            telegram_user_id: Telegram user ID of the sender.
            text: Natural language description of a financial transaction.

        Returns:
            Formatted confirmation message, or an error message on failure.
        """
        try:
            extracted = await self._extractor.extract(text)
        except ExtractionError as exc:
            logger.warning(
                "Extraction failed for user_id=%s: %s",
                telegram_user_id,
                exc,
            )
            return f"Could not record transaction: {exc}"

        async with self._session_factory() as session:
            repository = TransactionRepository(session)
            transaction = await repository.create(
                telegram_user_id=telegram_user_id,
                type=extracted.type,
                amount=extracted.amount,
                currency=extracted.currency,
                merchant=extracted.merchant,
                category=extracted.category,
                notes=extracted.notes,
                transaction_date=extracted.transaction_date,
            )
            await session.commit()

        logger.info(
            "Saved transaction id=%s for user_id=%s",
            transaction.id,
            telegram_user_id,
        )
        return format_confirmation(extracted)

    async def process_voice(
        self,
        telegram_user_id: int,
        audio: bytes,
        filename: str = "voice.ogg",
    ) -> str:
        """Transcribe a voice message, then extract, save, and confirm.

        Args:
            telegram_user_id: Telegram user ID of the sender.
            audio: Raw voice message audio bytes.
            filename: Filename hint for the audio format.

        Returns:
            Formatted confirmation message, or an error message on failure.
        """
        try:
            text = await self._transcriber.transcribe(audio, filename)
        except TranscriptionError as exc:
            logger.warning(
                "Transcription failed for user_id=%s: %s",
                telegram_user_id,
                exc,
            )
            return f"Could not transcribe voice message: {exc}"

        logger.info("Transcribed voice for user_id=%s: %s", telegram_user_id, text)
        return await self.process_text(telegram_user_id, text)


def format_confirmation(extracted: ExtractedTransaction) -> str:
    """Format a saved transaction as a Telegram confirmation message."""
    lines = [
        "Recorded",
        "",
        extracted.type.capitalize(),
        _format_amount_line(extracted.amount, extracted.currency),
    ]

    if extracted.merchant:
        lines.extend(["", "Merchant", extracted.merchant])

    if extracted.category:
        lines.extend(["", "Category", extracted.category])

    return "\n".join(lines)


def _format_amount_line(amount: Decimal, currency: str) -> str:
    """Format amount and currency for display."""
    normalized = amount.normalize()
    if normalized == normalized.to_integral_value():
        return f"{int(normalized)} {currency}"
    return f"{normalized} {currency}"
