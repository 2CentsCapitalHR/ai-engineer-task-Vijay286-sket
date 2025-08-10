from __future__ import annotations

import os
from typing import List
from docx import Document


SAMPLES = [
    (
        "Articles_of_Association.docx",
        "Articles of Association\n\nClause 3.1 Jurisdiction\nThis Company shall be governed by the laws of Dubai.\n\n[signature]",
    ),
    (
        "Memorandum_of_Association.docx",
        "Memorandum of Association\n\nPurpose: Sample text for demonstration.\n\n<signature>",
    ),
    (
        "Board_Resolution.docx",
        "Board Resolution\n\nResolved that the Company approve incorporation matters.\n\n[signature]",
    ),
    (
        "UBO_Declaration.docx",
        "Ultimate Beneficial Owner (UBO) Declaration\n\nWe hereby declare...",
    ),
    (
        "Register_of_Members_and_Directors.docx",
        "Register of Members and Directors\n\nMember: Jane Doe\nDirector: John Smith",
    ),
]


def generate_samples(target_dir: str = "sample_docs") -> List[str]:
    os.makedirs(target_dir, exist_ok=True)
    written: List[str] = []
    for name, content in SAMPLES:
        path = os.path.join(target_dir, name)
        doc = Document()
        for line in content.split("\n\n"):
            doc.add_paragraph(line)
        doc.save(path)
        written.append(path)
    return written


