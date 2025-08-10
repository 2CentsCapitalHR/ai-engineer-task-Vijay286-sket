from __future__ import annotations

import os
from typing import List, Tuple
import requests


DEFAULT_LINKS: List[Tuple[str, str]] = [
    (
        "adgm_registration_and_incorporation.html",
        "https://www.adgm.com/registration-authority/registration-and-incorporation",
    ),
    (
        "adgm_guidance_and_policy.html",
        "https://www.adgm.com/legal-framework/guidance-and-policy-statements",
    ),
]


def download_refs(dest_dir: str, links: List[Tuple[str, str]] | None = None) -> int:
    os.makedirs(dest_dir, exist_ok=True)
    count = 0
    for filename, url in (links or DEFAULT_LINKS):
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            path = os.path.join(dest_dir, filename)
            with open(path, "wb") as f:
                f.write(resp.content)
            count += 1
        except Exception:
            # Skip failed items in this minimal helper
            pass
    return count


