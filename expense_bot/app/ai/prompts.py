"""LLM prompts for transaction extraction."""

from __future__ import annotations

from datetime import date

EXTRACTION_SYSTEM_PROMPT = """You are a financial transaction extraction assistant.

Extract structured transaction data from the user's message. The message may be in any language.

Return ONLY a valid JSON object with these exact keys:
- type: "expense" or "income" (default to "expense" when ambiguous)
- amount: positive number (no currency symbols)
- currency: ISO 4217 currency code (e.g. EGP, USD, EUR)
- merchant: string or null if unknown
- category: string or null if unknown (e.g. Transport, Groceries, Food)
- transaction_date: ISO date string YYYY-MM-DD
- notes: string or null for extra context not captured elsewhere
- confidence: float between 0.0 and 1.0 reflecting extraction certainty

Rules:
- Return ONLY the JSON object. No markdown, no code fences, no explanation.
- Use null for unknown optional fields.
- If no date is mentioned, use the reference date provided in the user message.
- Infer reasonable categories from context when possible.
"""


def build_user_prompt(text: str, today: date) -> str:
    """Build the user prompt with the message text and reference date.

    Args:
        text: Raw user message describing a transaction.
        today: Reference date to use when no date is mentioned.

    Returns:
        Formatted user prompt for the LLM.
    """
    return (
        f"Reference date (use when no date is mentioned): {today.isoformat()}\n\n"
        f"Message:\n{text}"
    )
