"""Expense tracker entry point."""

from expense_bot.app.main import run


def main() -> None:
    """Delegate to the application runner."""
    run()


if __name__ == "__main__":
    main()
