"""
Security Hardening Module for GenshinIQ (Phase 19).
Provides input sanitization, path traversal checks, security HTTP headers,
and rate limiting protection.
"""

from collections import defaultdict
import logging
import time
from typing import Dict, Tuple
from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


def validate_identifier(ident: str, max_length: int = 100) -> str:
    """
    Validate and sanitize user-provided string identifiers against
    path traversal sequences, null bytes, and excessive buffer lengths.
    Raises HTTP 400 if malformed.
    """
    if not ident or not isinstance(ident, str):
        raise HTTPException(
            status_code=400,
            detail="Identifier must be a non-empty string."
        )
    if len(ident) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"Identifier exceeds maximum allowed length of {max_length} characters."
        )
    if ".." in ident or "/" in ident or "\\" in ident or "\x00" in ident:
        raise HTTPException(
            status_code=400,
            detail="Path traversal sequences or control characters are not permitted."
        )
    return ident.strip()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds essential defense-in-depth HTTP security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


class RateLimitAndSizeMiddleware(BaseHTTPMiddleware):
    """
    In-memory rate limiter and payload size guard.
    - Limits payload size to 10 MB (HTTP 413).
    - Tracks client IP sliding window (e.g. 300 requests per 10s window) (HTTP 429).
    """

    def __init__(self, app, max_requests_per_window: int = 300, window_seconds: float = 10.0, max_body_size: int = 10 * 1024 * 1024):
        super().__init__(app)
        self.max_requests = max_requests_per_window
        self.window_seconds = window_seconds
        self.max_body_size = max_body_size
        # IP -> list of timestamps
        self.requests_by_ip: Dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # 1. Payload size check
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_body_size:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "Payload too large. Maximum allowed size is 10MB."}
                    )
            except ValueError:
                pass

        # 2. Rate limiting check
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        # Cleanup old timestamps
        history = self.requests_by_ip[client_ip]
        cutoff = now - self.window_seconds
        self.requests_by_ip[client_ip] = [t for t in history if t > cutoff]
        
        if len(self.requests_by_ip[client_ip]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."}
            )

        self.requests_by_ip[client_ip].append(now)
        return await call_next(request)
