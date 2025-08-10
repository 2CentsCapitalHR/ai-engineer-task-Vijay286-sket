from typing import List, Set


INCORPORATION_REQUIRED: List[str] = [
    "Articles of Association",
    "Memorandum of Association",
    "Resolution",
    "UBO Declaration",
    "Register of Members and Directors",
]


def infer_process(doc_types: List[str]) -> str:
    overlap: Set[str] = set(doc_types).intersection(set(INCORPORATION_REQUIRED))
    return "Company Incorporation" if len(overlap) >= 2 else "Unknown"


def required_for_process(process: str) -> List[str]:
    if process == "Company Incorporation":
        return INCORPORATION_REQUIRED
    return []


