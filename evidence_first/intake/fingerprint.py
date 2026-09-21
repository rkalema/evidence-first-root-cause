from __future__ import annotations

import hashlib


def fingerprint_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def fingerprint_text(text: str) -> str:
    return fingerprint_bytes(text.encode("utf-8"))
