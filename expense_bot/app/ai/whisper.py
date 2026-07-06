"""Speech-to-text transcription for voice messages."""

from __future__ import annotations

import logging
from io import BytesIO
from typing import Protocol

from openai import AsyncOpenAI, OpenAIError

from expense_bot.app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    """Raised when speech transcription fails."""


class SpeechTranscriber(Protocol):
    """Interface for transcribing audio to text."""

    async def transcribe(self, audio: bytes, filename: str) -> str:
        """Transcribe audio bytes into plain text."""
        ...


class OpenAIWhisperTranscriber:
    """Transcribe audio using the OpenAI Whisper API."""

    def __init__(
        self,
        api_key: str,
        whisper_model: str,
        client: AsyncOpenAI | None = None,
    ) -> None:
        if not api_key:
            raise TranscriptionError("OPENAI_API_KEY is not configured.")

        self._whisper_model = whisper_model
        self._client = client or AsyncOpenAI(api_key=api_key)

    async def transcribe(self, audio: bytes, filename: str) -> str:
        """Transcribe audio bytes into plain text using Whisper.

        Args:
            audio: Raw audio file bytes.
            filename: Filename hint for the audio format (e.g. voice.ogg).

        Returns:
            Transcribed text.

        Raises:
            TranscriptionError: If audio is empty or the API call fails.
        """
        if not audio:
            raise TranscriptionError("Audio data is empty.")

        audio_file = BytesIO(audio)
        audio_file.name = filename

        try:
            response = await self._client.audio.transcriptions.create(
                model=self._whisper_model,
                file=audio_file,
            )
        except OpenAIError as exc:
            logger.exception("OpenAI Whisper API call failed")
            raise TranscriptionError("Failed to transcribe voice message.") from exc

        text = response.text.strip()
        if not text:
            raise TranscriptionError("Transcription returned empty text.")

        return text


def create_openai_transcriber(
    settings: Settings | None = None,
) -> OpenAIWhisperTranscriber:
    """Create an OpenAI-backed speech transcriber from application settings.

    Args:
        settings: Optional settings override. Uses cached settings when omitted.

    Returns:
        Configured OpenAIWhisperTranscriber instance.
    """
    resolved_settings = settings or get_settings()
    return OpenAIWhisperTranscriber(
        api_key=resolved_settings.openai_api_key,
        whisper_model=resolved_settings.whisper_model,
    )
