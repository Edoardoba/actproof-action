"""
ActProof.ai - Rate Limiting Middleware
Smart rate limiting with tiered quotas for SaaS platform
"""

import time
import logging
from typing import Dict, Optional, Tuple
from collections import defaultdict
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitTier:
    """Rate limit tier configuration"""

    def __init__(
        self,
        name: str,
        requests_per_minute: int,
        requests_per_hour: int,
        requests_per_day: int,
        burst_size: int = 10,
    ):
        self.name = name
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests_per_day = requests_per_day
        self.burst_size = burst_size


# Predefined tiers for SaaS platform
RATE_LIMIT_TIERS = {
    "free": RateLimitTier(
        name="Free",
        requests_per_minute=10,
        requests_per_hour=100,
        requests_per_day=500,
        burst_size=5,
    ),
    "starter": RateLimitTier(
        name="Starter",
        requests_per_minute=30,
        requests_per_hour=500,
        requests_per_day=5000,
        burst_size=15,
    ),
    "professional": RateLimitTier(
        name="Professional",
        requests_per_minute=100,
        requests_per_hour=2000,
        requests_per_day=20000,
        burst_size=50,
    ),
    "enterprise": RateLimitTier(
        name="Enterprise",
        requests_per_minute=500,
        requests_per_hour=10000,
        requests_per_day=100000,
        burst_size=200,
    ),
}


class RateLimiter:
    """
    Token bucket rate limiter with multiple time windows
    Supports tiered rate limiting for SaaS platform
    """

    def __init__(self):
        # Storage: customer_id -> {window -> (timestamp, count)}
        self.request_counts: Dict[str, Dict[str, Tuple[float, int]]] = defaultdict(
            lambda: defaultdict(lambda: (time.time(), 0))
        )

        # Customer tier mapping: customer_id -> tier_name
        self.customer_tiers: Dict[str, str] = {}

        # Token buckets for burst handling: customer_id -> (tokens, last_update)
        self.token_buckets: Dict[str, Tuple[int, float]] = {}

    def set_customer_tier(self, customer_id: str, tier: str):
        """
        Assign tier to a customer

        Args:
            customer_id: Customer identifier
            tier: Tier name (free, starter, professional, enterprise)
        """
        if tier not in RATE_LIMIT_TIERS:
            raise ValueError(f"Invalid tier: {tier}. Must be one of {list(RATE_LIMIT_TIERS.keys())}")

        self.customer_tiers[customer_id] = tier
        logger.info(f"Customer {customer_id} assigned to tier: {tier}")

    def get_customer_tier(self, customer_id: str) -> RateLimitTier:
        """
        Get rate limit tier for customer

        Args:
            customer_id: Customer identifier

        Returns:
            RateLimitTier configuration
        """
        tier_name = self.customer_tiers.get(customer_id, "free")
        return RATE_LIMIT_TIERS[tier_name]

    def _check_window(
        self, customer_id: str, window: str, limit: int, window_seconds: int
    ) -> Tuple[bool, int, int]:
        """
        Check if request is within rate limit for a time window

        Args:
            customer_id: Customer identifier
            window: Window identifier (minute, hour, day)
            limit: Maximum requests allowed in window
            window_seconds: Window size in seconds

        Returns:
            Tuple of (is_allowed, current_count, remaining)
        """
        current_time = time.time()
        timestamp, count = self.request_counts[customer_id][window]

        # Reset counter if window has elapsed
        if current_time - timestamp > window_seconds:
            timestamp = current_time
            count = 0

        # Check if limit exceeded
        is_allowed = count < limit
        remaining = max(0, limit - count)

        # Update counter if request is allowed
        if is_allowed:
            count += 1
            self.request_counts[customer_id][window] = (timestamp, count)

        return is_allowed, count, remaining

    def _check_burst(self, customer_id: str, burst_size: int, refill_rate: float) -> bool:
        """
        Check token bucket for burst protection

        Args:
            customer_id: Customer identifier
            burst_size: Maximum burst size
            refill_rate: Token refill rate per second

        Returns:
            True if request allowed, False otherwise
        """
        current_time = time.time()

        # Initialize bucket if not exists
        if customer_id not in self.token_buckets:
            self.token_buckets[customer_id] = (burst_size, current_time)

        tokens, last_update = self.token_buckets[customer_id]

        # Refill tokens based on time elapsed
        elapsed = current_time - last_update
        tokens = min(burst_size, tokens + int(elapsed * refill_rate))

        # Check if token available
        if tokens > 0:
            tokens -= 1
            self.token_buckets[customer_id] = (tokens, current_time)
            return True

        return False

    def check_rate_limit(self, customer_id: str) -> Dict[str, any]:
        """
        Check all rate limit windows for customer

        Args:
            customer_id: Customer identifier

        Returns:
            Dict with rate limit status and headers
        """
        tier = self.get_customer_tier(customer_id)

        # Check minute window
        minute_allowed, minute_count, minute_remaining = self._check_window(
            customer_id, "minute", tier.requests_per_minute, 60
        )

        # Check hour window
        hour_allowed, hour_count, hour_remaining = self._check_window(
            customer_id, "hour", tier.requests_per_hour, 3600
        )

        # Check day window
        day_allowed, day_count, day_remaining = self._check_window(
            customer_id, "day", tier.requests_per_day, 86400
        )

        # Check burst protection
        burst_allowed = self._check_burst(
            customer_id, tier.burst_size, tier.requests_per_minute / 60.0
        )

        # Determine if request is allowed (all windows must pass)
        is_allowed = minute_allowed and hour_allowed and day_allowed and burst_allowed

        # Find most restrictive window for headers
        if not minute_allowed:
            limit = tier.requests_per_minute
            remaining = minute_remaining
            reset_time = int(time.time()) + 60
        elif not hour_allowed:
            limit = tier.requests_per_hour
            remaining = hour_remaining
            reset_time = int(time.time()) + 3600
        elif not day_allowed:
            limit = tier.requests_per_day
            remaining = day_remaining
            reset_time = int(time.time()) + 86400
        else:
            limit = tier.requests_per_minute
            remaining = minute_remaining
            reset_time = int(time.time()) + 60

        return {
            "allowed": is_allowed,
            "tier": tier.name,
            "limit": limit,
            "remaining": remaining,
            "reset": reset_time,
            "minute_remaining": minute_remaining,
            "hour_remaining": hour_remaining,
            "day_remaining": day_remaining,
        }

    def cleanup_old_entries(self, max_age_seconds: int = 86400):
        """
        Remove old entries from memory

        Args:
            max_age_seconds: Maximum age before cleanup (default 24 hours)
        """
        current_time = time.time()

        # Cleanup request counts
        for customer_id in list(self.request_counts.keys()):
            for window in list(self.request_counts[customer_id].keys()):
                timestamp, _ = self.request_counts[customer_id][window]
                if current_time - timestamp > max_age_seconds:
                    del self.request_counts[customer_id][window]

            # Remove customer if no windows remain
            if not self.request_counts[customer_id]:
                del self.request_counts[customer_id]

        # Cleanup token buckets
        for customer_id in list(self.token_buckets.keys()):
            _, last_update = self.token_buckets[customer_id]
            if current_time - last_update > max_age_seconds:
                del self.token_buckets[customer_id]


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """
    Get global rate limiter instance (singleton)

    Returns:
        Shared RateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


async def rate_limit_middleware(request: Request, call_next):
    """
    FastAPI middleware for rate limiting

    Args:
        request: FastAPI request
        call_next: Next middleware/handler

    Returns:
        Response with rate limit headers
    """
    # Extract customer ID from headers or auth token
    customer_id = request.headers.get("X-Customer-ID", "anonymous")

    # Skip rate limiting for health check
    if request.url.path == "/health" or request.url.path == "/api/health":
        return await call_next(request)

    # Check rate limit
    rate_limiter = get_rate_limiter()
    result = rate_limiter.check_rate_limit(customer_id)

    # Add rate limit headers
    headers = {
        "X-RateLimit-Limit": str(result["limit"]),
        "X-RateLimit-Remaining": str(result["remaining"]),
        "X-RateLimit-Reset": str(result["reset"]),
        "X-RateLimit-Tier": result["tier"],
    }

    # Reject if rate limit exceeded
    if not result["allowed"]:
        logger.warning(
            f"Rate limit exceeded for customer {customer_id} "
            f"(tier: {result['tier']}, limit: {result['limit']})"
        )

        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Limit: {result['limit']} requests per window.",
                "tier": result["tier"],
                "reset": result["reset"],
                "upgrade_info": "Upgrade your plan for higher rate limits at https://actproof.ai/pricing"
            },
            headers=headers,
        )

    # Process request
    response = await call_next(request)

    # Add rate limit headers to response
    for key, value in headers.items():
        response.headers[key] = value

    return response


# Periodic cleanup task (should be run by background scheduler)
def cleanup_rate_limiter():
    """Cleanup old rate limiter entries"""
    rate_limiter = get_rate_limiter()
    rate_limiter.cleanup_old_entries()
    logger.info("Rate limiter cleanup completed")
