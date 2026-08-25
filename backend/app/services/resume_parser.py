import io

import pdfplumber


def extract_resume_text(filename: str, file_bytes: bytes) -> str:
    """Extract plain text from an uploaded resume file (.pdf or .txt)."""
    if filename.lower().endswith(".pdf"):
        return _extract_pdf_text(file_bytes)
    return file_bytes.decode("utf-8", errors="replace")


def _extract_pdf_text(file_bytes: bytes) -> str:
    pages_text = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            pages_text.append(page.extract_text() or "")
    text = "\n".join(pages_text).strip()
    if not text:
        raise ValueError(
            "Could not extract any text from this PDF — it may be a scanned/image-based "
            "resume, which isn't supported yet."
        )
    return text
