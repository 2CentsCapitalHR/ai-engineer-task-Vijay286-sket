from __future__ import annotations

import os
from typing import List

from bs4 import BeautifulSoup
from pypdf import PdfReader


def read_pdf_text(path: str) -> str:
    reader = PdfReader(path)
    pages: List[str] = []
    for p in reader.pages:
        pages.append(p.extract_text() or "")
    return "\n".join(pages)


def read_html_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(" ")


def discover_and_read(dir_path: str) -> List[tuple[str, str]]:
    texts: List[tuple[str, str]] = []
    for root, _, files in os.walk(dir_path):
        for name in files:
            p = os.path.join(root, name)
            lower = name.lower()
            try:
                if lower.endswith(".pdf"):
                    texts.append((p, read_pdf_text(p)))
                elif lower.endswith(".html") or lower.endswith(".htm"):
                    texts.append((p, read_html_text(p)))
                elif lower.endswith(".txt"):
                    with open(p, "r", encoding="utf-8", errors="ignore") as f:
                        texts.append((p, f.read()))
            except Exception:
                # Ignore unreadable files in this lightweight ingest
                pass
    return texts


