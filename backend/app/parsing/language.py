"""Language detection + translation for multi-language resume support.

Both langdetect and deep-translator can fail (short/ambiguous text, no network
access for the translator, etc). Every call here is wrapped so a failure
degrades gracefully instead of crashing the upload/parsing request.
"""
import logging

logger = logging.getLogger(__name__)


def detect_language(text: str) -> str:
    """Return an ISO-639-1 language code, defaulting to 'en' on any failure."""
    if not text or not text.strip():
        return "en"
    try:
        from langdetect import DetectorFactory, detect

        DetectorFactory.seed = 0  # deterministic results
        return detect(text)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Language detection failed, defaulting to 'en': %s", exc)
        return "en"


def translate_to_english(text: str, source_language: str) -> str | None:
    """Translate text to English using GoogleTranslator (deep-translator).

    Returns None (rather than raising) if translation is unavailable -- e.g. no
    network access in this environment -- so callers can fall back to the
    original text.
    """
    if not text or not text.strip():
        return None
    if source_language == "en":
        return None
    try:
        from deep_translator import GoogleTranslator

        # deep-translator has a per-request character limit; chunk long resumes.
        chunk_size = 4000
        chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
        translated_chunks = []
        translator = GoogleTranslator(source="auto", target="en")
        for chunk in chunks:
            translated_chunks.append(translator.translate(chunk) or "")
        return "\n".join(translated_chunks)
    except Exception as exc:  # pragma: no cover - defensive (no network, API changes, etc.)
        logger.warning("Translation to English failed, using original text: %s", exc)
        return None
