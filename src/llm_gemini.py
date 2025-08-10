from __future__ import annotations

import os
from typing import List, Dict, Any, Optional

import google.generativeai as genai


DEFAULT_MODEL = "models/gemini-1.5-pro"


def get_client(api_key: Optional[str] = None) -> None:
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not provided")
    genai.configure(api_key=key)


def analyze_doc_with_citations(
    text: str,
    citations: List[Dict[str, str]] | None = None,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Ask Gemini to find issues and suggestions, optionally grounded by citations.

    Returns a list of {issue, severity, suggestion, section?} dicts.
    """
    get_client(api_key)
    sys_prompt = (
        "You are an ADGM compliance assistant. Analyze the document text for red flags "
        "(jurisdiction, missing clauses, ambiguity, signatures) and propose concise suggestions. "
        "Return a compact JSON array in an object with key 'issues', and each issue has keys: issue, severity (High/Medium/Low), suggestion, section."
    )
    context_block = "\n\nCitations (optional):\n" + "\n".join(
        f"- Source: {c.get('source','')}\n  Snippet: {c.get('snippet','')[:300]}" for c in (citations or [])
    )
    user_prompt = f"{sys_prompt}\n\nDocument text (truncated to 8k chars):\n{text[:8000]}{context_block}\n\nRespond with JSON only."

    model_ref = genai.GenerativeModel(model)
    resp = model_ref.generate_content(user_prompt, generation_config={"temperature": temperature})
    content = resp.text or "{}"
    import json
    try:
        data = json.loads(content)
        issues = data.get("issues")
        if isinstance(issues, list):
            return issues
    except Exception:
        pass
    return []


