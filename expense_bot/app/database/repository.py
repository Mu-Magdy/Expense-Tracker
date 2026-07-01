"""Data access layer for transactions."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from expense_bot.app.database.models import Transaction


class TransactionRepository:
    """Repository for transaction persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        telegram_user_id: int,
        type: str,
        amount: Decimal,
        currency: str,
        merchant: str | None,
        category: str | None,
        notes: str | None,
        transaction_date: date,
    ) -> Transaction:
        """Persist a new transaction and return the created row."""
        transaction = Transaction(
            telegram_user_id=telegram_user_id,
            type=type,
            amount=amount,
            currency=currency,
            merchant=merchant,
            category=category,
            notes=notes,
            transaction_date=transaction_date,
        )
        self._session.add(transaction)
        await self._session.flush()
        await self._session.refresh(transaction)
        return transaction

    async def get_by_id(self, transaction_id: int) -> Transaction | None:
        """Return a transaction by primary key, or None if not found."""
        return await self._session.get(Transaction, transaction_id)
