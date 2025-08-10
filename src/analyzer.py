from typing import List, Dict, Any


def identify_document_type(text: str) -> str:
    lowered = text.lower()
    if "articles of association" in lowered:
        return "Articles of Association"
    if "memorandum of association" in lowered or "memorandum" in lowered:
        return "Memorandum of Association"
    if "resolution" in lowered:
        return "Resolution"
    if "incorporation" in lowered:
        return "Incorporation Application"
    if "beneficial owner" in lowered or "ubo" in lowered:
        return "UBO Declaration"
    if "register of members" in lowered or "register of directors" in lowered:
        return "Register of Members and Directors"
    return "Unknown"


def basic_issue_scan(text: str) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    lowered = text.lower()
    if "dubai" in lowered or "uae federal" in lowered:
        issues.append({
            "issue": "Jurisdiction may not be ADGM",
            "severity": "High",
            "suggestion": "Confirm jurisdiction clauses reference ADGM Courts.",
            "citations": [
                "ADGM Rulebook – en.adgm.thomsonreuters.com",
            ],
        })
    if "[signature]" in lowered or "<signature>" in lowered:
        issues.append({
            "issue": "Signature placeholders detected",
            "severity": "Medium",
            "suggestion": "Ensure valid signatory blocks and execution pages are present.",
        })
    return issues


