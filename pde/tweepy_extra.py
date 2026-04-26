"""Helpers for Tweepy / X API v2 response metadata (no extra HTTP)."""

from __future__ import annotations

from typing import Any


def rate_limit_caption_from_response(tweepy_response: Any) -> str:
    """Build a one-line status from a tweepy Response if raw HTTP is attached."""
    r = getattr(tweepy_response, "response", None)
    if r is None:
        return ""
    h = getattr(r, "headers", None) or {}
    if not h:
        return ""
    get = h.get
    rem = get("x-rate-limit-remaining") or get("X-Rate-Limit-Remaining")
    limit = get("x-rate-limit-limit") or get("X-Rate-Limit-Limit")
    reset = get("x-rate-limit-reset") or get("X-Rate-Limit-Reset")
    if rem is not None and reset is not None and limit is not None:
        return (
            f"X API: {rem} call(s) remaining this window (of {limit}); reset (UTC epoch) = {reset}"
        )
    if rem is not None and limit is not None:
        return f"X API: {rem} call(s) remaining (of {limit}) this window"
    if rem is not None:
        return f"X API: rate limit remaining = {rem}"
    return ""


def rate_caption_from_exception(err: BaseException) -> str:
    """On HTTP errors, Tweepy often attaches a ``response`` with the same headers."""
    r = getattr(err, "response", None)
    if r is None or not hasattr(r, "headers"):
        return ""
    h = r.headers
    if not h:
        return ""
    get = h.get
    rem = get("x-rate-limit-remaining") or get("X-Rate-Limit-Remaining")
    limit = get("x-rate-limit-limit") or get("X-Rate-Limit-Limit")
    reset = get("x-rate-limit-reset") or get("X-Rate-Limit-Reset")
    if rem is not None and limit is not None and reset is not None:
        return f"X API: {rem} call(s) remaining (of {limit}); reset (UTC epoch) = {reset}"
    if rem is not None and limit is not None:
        return f"X API: {rem} call(s) remaining (of {limit})"
    if rem is not None:
        return f"X API: rate limit remaining = {rem}"
    return ""
