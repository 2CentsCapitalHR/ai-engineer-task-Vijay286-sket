from __future__ import annotations

import os
from typing import List, Dict, Any, Optional

from groq import Groq


DEFAULT_MODEL = "llama-3.3-70b-versatile"


def get_client(api_key: Optional[str] = None) -> Groq:
    key = api_key or os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY not provided")
    return Groq(api_key=key)


def analyze_doc_with_citations(
    text: str,
    citations: List[Dict[str, str]] | None = None,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Ask Groq LLM to find issues and suggestions, optionally grounded by citations.

    Returns a list of {issue, severity, suggestion, section?} dicts.
    """
    client = get_client(api_key)
    sys_prompt = (
        "You are an ADGM compliance assistant. Analyze the document text for red flags "
        "(jurisdiction, missing clauses, ambiguity, signatures) and propose concise suggestions. "
        "Return a compact JSON array of objects with keys: issue, severity (High/Medium/Low), suggestion, section."
    )
    context_block = "\n\nCitations (optional):\n" + "\n".join(
        f"- Source: {c.get('source','')}\n  Snippet: {c.get('snippet','')[:300]}" for c in (citations or [])
    )
    user_prompt = f"Document text (truncated to 8k chars):\n{text[:8000]}{context_block}\n\nRespond with JSON only."

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    content = completion.choices[0].message.content or "{}"
    # The model is asked to return an object with key 'issues'
    import json
    try:
        data = json.loads(content)
        issues = data.get("issues")
        if isinstance(issues, list):
            return issues
    except Exception:
        pass
    return []


