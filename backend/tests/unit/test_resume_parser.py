import io
from pathlib import Path

import pytest
from reportlab.pdfgen import canvas

from app.services.resume_parser import extract_resume_text

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_extract_resume_text_from_txt():
    text = extract_resume_text("resume.txt", b"Jordan Smith\nSenior Software Engineer")
    assert "Jordan Smith" in text


def test_extract_resume_text_from_pdf():
    pdf_bytes = (FIXTURES / "sample_resume.pdf").read_bytes()
    text = extract_resume_text("resume.pdf", pdf_bytes)
    assert "Jordan Smith" in text
    assert "FastAPI" in text


def test_extract_resume_text_from_blank_pdf_raises():
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.showPage()
    c.save()
    with pytest.raises(ValueError, match="scanned/image-based"):
        extract_resume_text("blank.pdf", buf.getvalue())
