import io
from typing import List
from docx import Document


def extract_text(file_bytes: bytes) -> str:
    with io.BytesIO(file_bytes) as buffer:
        doc = Document(buffer)
    return "\n".join(p.text for p in doc.paragraphs)


def split_into_sections(text: str) -> List[str]:
    lines = [ln.strip() for ln in text.splitlines()]
    sections: List[str] = []
    current: List[str] = []
    for ln in lines:
        if ln and (ln.isupper() or ln.lower().startswith("clause ") or ln.lower().startswith("article ")):
            if current:
                sections.append("\n".join(current))
                current = []
        current.append(ln)
    if current:
        sections.append("\n".join(current))
    return sections


