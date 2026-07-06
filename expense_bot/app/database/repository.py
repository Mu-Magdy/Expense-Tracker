"""Data access layer for transactions."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import delete, func, or_, select
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

    async def list_for_user_in_range(
        self,
        telegram_user_id: int,
        start: date,
        end: date,
    ) -> list[Transaction]:
        """Return transactions for a user within an inclusive date range."""
        stmt = (
            select(Transaction)
            .where(
                Transaction.telegram_user_id == telegram_user_id,
                Transaction.transaction_date >= start,
                Transaction.transaction_date <= end,
            )
            .order_by(
                Transaction.transaction_date.desc(),
                Transaction.created_at.desc(),
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def sum_by_type_and_currency(
        self,
        telegram_user_id: int,
        start: date,
        end: date,
    ) -> list[tuple[str, str, Decimal]]:
        """Return totals grouped by transaction type and currency."""
        stmt = (
            select(
                Transaction.type,
                Transaction.currency,
                func.sum(Transaction.amount),
            )
            .where(
                Transaction.telegram_user_id == telegram_user_id,
                Transaction.transaction_date >= start,
                Transaction.transaction_date <= end,
            )
            .group_by(Transaction.type, Transaction.currency)
            .order_by(Transaction.type, Transaction.currency)
        )
        result = await self._session.execute(stmt)
        return [
            (type_, currency, total or Decimal("0"))
            for type_, currency, total in result.all()
        ]

    async def sum_expenses_by_category(
        self,
        telegram_user_id: int,
        start: date,
        end: date,
    ) -> list[tuple[str, str, Decimal]]:
        """Return expense totals grouped by category and currency."""
        stmt = (
            select(
                Transaction.category,
                Transaction.currency,
                func.sum(Transaction.amount),
            )
            .where(
                Transaction.telegram_user_id == telegram_user_id,
                Transaction.type == "expense",
                Transaction.category.is_not(None),
                Transaction.transaction_date >= start,
                Transaction.transaction_date <= end,
            )
            .group_by(Transaction.category, Transaction.currency)
            .order_by(func.sum(Transaction.amount).desc())
        )
        result = await self._session.execute(stmt)
        return [
            (category, currency, total or Decimal("0"))
            for category, currency, total in result.all()
            if category is not None
        ]

    async def search(
        self,
        telegram_user_id: int,
        query: str,
        *,
        limit: int = 20,
    ) -> list[Transaction]:
        """Search transactions by merchant, category, or notes."""
        pattern = f"%{query}%"
        stmt = (
            select(Transaction)
            .where(
                Transaction.telegram_user_id == telegram_user_id,
                or_(
                    Transaction.merchant.ilike(pattern),
                    Transaction.category.ilike(pattern),
                    Transaction.notes.ilike(pattern),
                ),
            )
            .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_for_user(
        self,
        telegram_user_id: int,
    ) -> Transaction | None:
        """Return the most recently created transaction for a user."""
        stmt = (
            select(Transaction)
            .where(Transaction.telegram_user_id == telegram_user_id)
            .order_by(Transaction.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_by_id(self, transaction_id: int) -> bool:
        """Delete a transaction by id. Returns True if a row was deleted."""
        stmt = delete(Transaction).where(Transaction.id == transaction_id)
        result = await self._session.execute(stmt)
        return result.rowcount > 0
