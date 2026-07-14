import io
from pathlib import Path

import docx2txt
import markdown
import pandas as pd
from pypdf import PdfReader

from app.utils.errors import AppError
from app.utils.text_cleaner import clean_text

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".csv", ".xlsx", ".md"}


def extract_text(filename: str, content: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise AppError(
            f"Unsupported file format. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
            status_code=400,
        )

    if ext == ".pdf":
        reader = PdfReader(io.BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages)
    elif ext == ".docx":
        text = docx2txt.process(io.BytesIO(content)) or ""
    elif ext in {".txt", ".md"}:
        text = content.decode("utf-8", errors="ignore")
        if ext == ".md":
            text = markdown.markdown(text)
    elif ext == ".csv":
        df = pd.read_csv(io.BytesIO(content))
        text = df.to_string(index=False)
    elif ext == ".xlsx":
        df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
        text = df.to_string(index=False)
    else:
        raise AppError("Unsupported file format", status_code=400)

    cleaned = clean_text(text)
    if not cleaned:
        raise AppError("Document contains no extractable text", status_code=400)
    return cleaned
