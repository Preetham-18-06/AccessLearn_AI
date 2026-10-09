
import fitz

MAX_PDF_SIZE = 10 * 1024 * 1024
MAX_TEXT_LENGTH = 30_000


def extract_pdf_text(pdf_bytes: bytes) -> str:
    if not pdf_bytes:
        raise ValueError("The uploaded PDF is empty.")

    if len(pdf_bytes) > MAX_PDF_SIZE:
        raise ValueError("PDF must be 10 MB or smaller.")

    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            if doc.is_encrypted:
                raise ValueError("Password-protected PDFs are not supported.")

            text = "\n".join(page.get_text() for page in doc)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Invalid or unreadable PDF.") from exc

    if not text.strip():
        raise ValueError("No readable text found. Scanned PDFs need OCR.")

    return text[:MAX_TEXT_LENGTH]


def prepare_text(text: str) -> str:
    text = text.strip()

    if not text:
        raise ValueError("Please provide study material.")

    return text[:MAX_TEXT_LENGTH]
