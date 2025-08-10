from typing import List, Dict, Any


def build_report(process: str, entries: List[Dict[str, Any]], required: List[str]) -> Dict[str, Any]:
    present_types = set(e["type"] for e in entries)
    missing = [r for r in required if r not in present_types]
    return {
        "process": process,
        "documents_uploaded": len(entries),
        "required_documents": len(required),
        "missing_documents": missing,
        "issues_found": [
            {
                "document": e["name"],
                "type": e["type"],
                "issues": e["issues"],
            }
            for e in entries
        ],
    }


