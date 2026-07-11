"""
Cache Header Utilities
"""
import hashlib, json
from typing import Any
from fastapi import Response


def add_cache_headers(
    response: Response,
    max_age: int = 0,
    public: bool = False,
    must_revalidate: bool = True,
) -> None:
    directives = ["public" if public else "private", f"max-age={max_age}"]
    if must_revalidate:
        directives.append("must-revalidate")
    response.headers["Cache-Control"] = ", ".join(directives)


def generate_etag(data: Any) -> str:
    """MD5-based ETag, RFC 7232 quoted."""
    digest = hashlib.md5(
        json.dumps(data, sort_keys=True, default=str).encode()
    ).hexdigest()
    return f'"{digest}"'


def check_etag(current_etag: str, client_etag: str) -> bool:
    return current_etag.strip('"') == client_etag.strip('"')
