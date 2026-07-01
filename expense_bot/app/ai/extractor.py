"""Transaction extraction from natural language text."""

from __future__ import annotations

import json
import logging
import re
from datetime import date
from typing import Protocol

from openai import AsyncOpenAI, OpenAIError
from pydantic import ValidationError

from expense_bot.app.ai.prompts import EXTRACTION_SYSTEM_PROMPT, build_user_prompt
from expense_bot.app.config import Settings, get_settings
from expense_bot.app.schemas.transaction import ExtractedTransaction

logger = logging.getLogger(__name__)

_JSON_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


class ExtractionError(Exception):
    """Raised when extraction or validation fails."""


class TransactionExtractor(Protocol):
    """Interface for extracting structured transactions from text."""

    async def extract(self, text: str) -> ExtractedTransaction:
        """Extract a transaction from free-form text."""
        ...


class OpenAITransactionExtractor:
    """Extract transactions using the OpenAI Chat Completions API."""

    def __init__(
        self,
        api_key: str,
        model_name: str,
        client: AsyncOpenAI | None = None,
    ) -> None:
        if not api_key:
            raise ExtractionError("OPENAI_API_KEY is not configured.")

        self._model_name = model_name
        self._client = client or AsyncOpenAI(api_key=api_key)

    async def extract(self, text: str) -> ExtractedTransaction:
        """Extract a transaction from free-form text using an LLM.

        Args:
            text: Natural language description of a financial transaction.

        Returns:
            Validated extracted transaction.

        Raises:
            ExtractionError: If input is empty, the API fails, or validation fails.
        """
        stripped_text = text.strip()
        if not stripped_text:
            raise ExtractionError("Message text is empty.")

        try:
            response = await self._client.chat.completions.create(
                model=self._model_name,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": build_user_prompt(stripped_text, date.today()),
                    },
                ],
            )
        except OpenAIError as exc:
            logger.exception("OpenAI API call failed")
            raise ExtractionError("Failed to extract transaction from message.") from exc

        raw_content = response.choices[0].message.content
        if not raw_content:
            raise ExtractionError("LLM returned an empty response.")

        return self._parse_and_validate(raw_content)

    def _parse_and_validate(self, raw_content: str) -> ExtractedTransaction:
        """Parse LLM JSON output and validate against the schema."""
        cleaned = _JSON_FENCE_PATTERN.sub("", raw_content.strip())

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.warning("LLM returned non-JSON response: %s", raw_content)
            raise ExtractionError("LLM response was not valid JSON.") from exc

        try:
            return ExtractedTransaction.model_validate(data)
        except ValidationError as exc:
            logger.warning("LLM response failed validation: %s", raw_content)
            raise ExtractionError("LLM response failed validation.") from exc


def create_openai_extractor(
    settings: Settings | None = None,
) -> OpenAITransactionExtractor:
    """Create an OpenAI-backed transaction extractor from application settings.

    Args:
        settings: Optional settings override. Uses cached settings when omitted.

    Returns:
        Configured OpenAITransactionExtractor instance.
    """
    resolved_settings = settings or get_settings()
    return OpenAITransactionExtractor(
        api_key=resolved_settings.openai_api_key,
        model_name=resolved_settings.model_name,
    )
