import re
import pdfplumber


def load_pdf(file_bytes: bytes, filename: str) -> list[dict]:
    """Extract text from PDF, return list of {page, text} dicts."""
    pages = []
    with pdfplumber.open(file_bytes) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            text = _clean(text)
            if text.strip():
                pages.append({"page": i + 1, "text": text, "source": filename})
    return pages


def load_txt(file_bytes: bytes, filename: str) -> list[dict]:
    """Load plain text file, treat entire file as page 1."""
    text = file_bytes.decode("utf-8", errors="replace")
    text = _clean(text)
    return [{"page": 1, "text": text, "source": filename}]


def _clean(text: str) -> str:
    """Normalize whitespace and strip non-printable characters."""
    text = re.sub(r"[^\x20-\x7E\n\t]", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
