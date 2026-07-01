"""Application entry point."""

from __future__ import annotations

import logging
import sys

from expense_bot.app.config import get_settings
from expense_bot.app.telegram.bot import create_application

LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configure_logging(level: str) -> None:
    """Configure root logging for the application."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=LOG_FORMAT,
        stream=sys.stdout,
    )


def run() -> None:
    """Start the Telegram bot using long polling."""
    settings = get_settings()
    configure_logging(settings.log_level)

    logger = logging.getLogger(__name__)
    logger.info("Starting expense tracker bot")

    application = create_application(settings)
    application.run_polling()


if __name__ == "__main__":
    run()
