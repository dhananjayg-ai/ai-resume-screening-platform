"""Extract raw text from uploaded resume files (PDF / DOCX), with an OCR
fallback for scanned PDFs that have little or no extractable text layer.
"""
import logging

logger = logging.getLogger(__name__)

# Below this many non-whitespace characters per page (on average) we treat a
# PDF as "scanned" and attempt OCR instead.
MIN_CHARS_PER_PAGE_THRESHOLD = 20

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


class ResumeParsingError(Exception):
    pass


def extract_text_from_pdf(file_path: str) -> tuple[str, bool]:
    """Extract text from a PDF. Returns (text, ocr_used).

    Tries pdfplumber first. If the extracted text looks too sparse (typical of
    a scanned/image-only PDF), falls back to OCR via pdf2image + pytesseract.
    If OCR dependencies (poppler / tesseract) aren't installed, logs a warning
    and returns whatever text pdfplumber did manage to extract (or an empty
    string) rather than crashing.
    """
    text_parts: list[str] = []
    page_count = 0
    try:
        import pdfplumber

        with pdfplumber.open(file_path) as pdf:
            page_count = len(pdf.pages)
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_parts.append(page_text)
    except Exception as exc:
        logger.warning("pdfplumber failed to open/parse %s: %s", file_path, exc)

    text = "\n".join(text_parts).strip()
    avg_chars_per_page = len(text) / page_count if page_count else len(text)

    if avg_chars_per_page >= MIN_CHARS_PER_PAGE_THRESHOLD:
        return text, False

    # Looks like a scanned PDF (or pdfplumber failed) -- try OCR.
    ocr_text = _ocr_pdf(file_path)
    if ocr_text and len(ocr_text.strip()) > len(text):
        return ocr_text.strip(), True

    return text, False


def _ocr_pdf(file_path: str) -> str | None:
    """Run OCR over each page image of the PDF. Returns None on any failure
    (missing poppler-utils / tesseract-ocr system packages, etc.) so callers
    can gracefully fall back."""
    try:
        import pytesseract
        from pdf2image import convert_from_path

        images = convert_from_path(file_path)
        ocr_parts = []
        for image in images:
            ocr_parts.append(pytesseract.image_to_string(image))
        return "\n".join(ocr_parts)
    except Exception as exc:
        logger.warning(
            "OCR fallback unavailable/failed for %s (requires poppler-utils and "
            "tesseract-ocr system packages): %s",
            file_path,
            exc,
        )
        return None


def extract_text_from_docx(file_path: str) -> str:
    try:
        import docx

        document = docx.Document(file_path)
        parts = [p.text for p in document.paragraphs]
        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    parts.append(cell.text)
        return "\n".join(parts).strip()
    except Exception as exc:
        logger.error("Failed to parse DOCX %s: %s", file_path, exc)
        raise ResumeParsingError(f"Could not parse DOCX file: {exc}") from exc


def extract_text(file_path: str, filename: str) -> tuple[str, bool]:
    """Dispatch to the right extractor based on file extension.

    Returns (text, ocr_used).
    """
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    if lower.endswith(".docx"):
        return extract_text_from_docx(file_path), False
    raise ResumeParsingError(f"Unsupported file type for: {filename}")
