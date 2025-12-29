"""
Rate limiting middleware

Simple in-memory rate limiting (production: use Redis).
"""

import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware

    Limits requests per IP address based on configured window and limits.

    Note: This is a simple in-memory implementation.
    For production, use Redis-based rate limiting.
    """

    def __init__(self, app):
        super().__init__(app)
        # Store: {ip_address: (request_count, window_start_time)}
        self.requests: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, time.time()))

    async def dispatch(self, request: Request, call_next):
        """
        Process request with rate limiting

        Args:
            request: FastAPI Request
            call_next: Next middleware/endpoint

        Returns:
            Response or 429 Too Many Requests
        """
        # Skip rate limiting if disabled
        if not settings.rate_limit_enabled:
            return await call_next(request)

        # Skip rate limiting for health check
        if request.url.path == "/health":
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host

        # Get current request count and window start
        request_count, window_start = self.requests[client_ip]
        current_time = time.time()

        # Check if window has expired
        if current_time - window_start > settings.rate_limit_window:
            # Reset window
            self.requests[client_ip] = (1, current_time)
            return await call_next(request)

        # Check if limit exceeded
        if request_count >= settings.rate_limit_requests:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}", extra={
                "ip": client_ip,
                "requests": request_count,
                "limit": settings.rate_limit_requests,
                "window": settings.rate_limit_window
            })

            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "message": "Too many requests. Please try again later.",
                    "error": {
                        "type": "RateLimitExceeded",
                        "limit": settings.rate_limit_requests,
                        "window_seconds": settings.rate_limit_window,
                        "retry_after": int(settings.rate_limit_window - (current_time - window_start))
                    }
                },
                headers={
                    "Retry-After": str(int(settings.rate_limit_window - (current_time - window_start)))
                }
            )

        # Increment request count
        self.requests[client_ip] = (request_count + 1, window_start)

        return await call_next(request)
