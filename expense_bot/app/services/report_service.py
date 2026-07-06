"""Spending report business logic."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from expense_bot.app.database.models import Transaction
from expense_bot.app.database.repository import TransactionRepository


class ReportService:
    """Generates spending reports from database queries."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._session_factory = session_factory

    async def today_report(self, telegram_user_id: int) -> str:
        """Return a report for today's transactions."""
        today = date.today()
        return await self._period_report(telegram_user_id, "Today", today, today)

    async def week_report(self, telegram_user_id: int) -> str:
        """Return a report for the current calendar week."""
        today = date.today()
        start = today - timedelta(days=today.weekday())
        return await self._period_report(telegram_user_id, "This week", start, today)

    async def month_report(self, telegram_user_id: int) -> str:
        """Return a report for the current calendar month."""
        today = date.today()
        start = today.replace(day=1)
        return await self._period_report(telegram_user_id, "This month", start, today)

    async def categories_report(self, telegram_user_id: int) -> str:
        """Return expense totals grouped by category for the current month."""
        today = date.today()
        start = today.replace(day=1)

        async with self._session_factory() as session:
            repository = TransactionRepository(session)
            totals = await repository.sum_expenses_by_category(
                telegram_user_id, start, today
            )

        if not totals:
            return "No categorized expenses this month."

        lines = ["Categories (this month)", ""]
        for category, currency, amount in totals:
            lines.append(f"{category}: {_format_amount(amount, currency)}")
        return "\n".join(lines)

    async def search_report(self, telegram_user_id: int, query: str) -> str:
        """Search transactions and return matching results."""
        stripped_query = query.strip()
        if not stripped_query:
            return "Usage: /search <term>"

        async with self._session_factory() as session:
            repository = TransactionRepository(session)
            transactions = await repository.search(telegram_user_id, stripped_query)

        if not transactions:
            return f'No transactions found for "{stripped_query}".'

        lines = [f'Search: "{stripped_query}"', ""]
        for transaction in transactions:
            lines.append(_format_transaction_line(transaction))
        return "\n".join(lines)

    async def undo_last(self, telegram_user_id: int) -> str:
        """Delete the user's most recently created transaction."""
        async with self._session_factory() as session:
            repository = TransactionRepository(session)
            transaction = await repository.get_latest_for_user(telegram_user_id)
            if transaction is None:
                return "No transactions to undo."

            summary = _format_transaction_line(transaction)
            await repository.delete_by_id(transaction.id)
            await session.commit()

        return f"Undone\n\n{summary}"

    async def _period_report(
        self,
        telegram_user_id: int,
        title: str,
        start: date,
        end: date,
    ) -> str:
        """Build a summary report for a date range."""
        async with self._session_factory() as session:
            repository = TransactionRepository(session)
            transactions = await repository.list_for_user_in_range(
                telegram_user_id, start, end
            )
            totals = await repository.sum_by_type_and_currency(
                telegram_user_id, start, end
            )

        if not transactions:
            return f"{title}\n\nNo transactions."

        lines = [title, ""]
        for type_, currency, amount in totals:
            lines.append(f"{type_.capitalize()}: {_format_amount(amount, currency)}")

        lines.extend(["", f"{len(transactions)} transaction(s)"])
        return "\n".join(lines)


def _format_amount(amount: Decimal, currency: str) -> str:
    """Format a decimal amount with currency."""
    normalized = amount.normalize()
    if normalized == normalized.to_integral_value():
        return f"{int(normalized)} {currency}"
    return f"{normalized} {currency}"


def _format_transaction_line(transaction: Transaction) -> str:
    """Format a single transaction as a one-line summary."""
    parts = [
        transaction.transaction_date.isoformat(),
        transaction.type,
        _format_amount(transaction.amount, transaction.currency),
    ]
    if transaction.merchant:
        parts.append(transaction.merchant)
    if transaction.category:
        parts.append(f"({transaction.category})")
    return " · ".join(parts)
