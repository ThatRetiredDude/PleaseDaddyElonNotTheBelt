"""Token budgeting and ToS review batching."""

from .constants import (
    AI_CONTEXT_FALLBACK_TOKENS,
    AI_CONTEXT_SAFETY_FACTOR,
    AI_MODEL_CONTEXT_TOKENS,
    AI_RESERVED_TOKENS,
    CHARS_PER_TOKEN,
    TWEET_OVERHEAD_CHARS,
)


def get_model_context_tokens(model_id: str) -> int:
    """Return max context tokens for model; fallback for unknown models."""
    return AI_MODEL_CONTEXT_TOKENS.get((model_id or "").strip(), AI_CONTEXT_FALLBACK_TOKENS)


def estimate_tokens_for_tweet(tweet) -> int:
    """Conservative token estimate from tweet text (chars/3 + overhead)."""
    text = tweet.get("text") or ""
    return max(1, (len(text) + TWEET_OVERHEAD_CHARS) // CHARS_PER_TOKEN)


def get_batch_token_budget(model_id: str) -> int:
    """Input token budget for one batch (90% of context minus reserved)."""
    ctx = get_model_context_tokens(model_id)
    return max(500, int(ctx * AI_CONTEXT_SAFETY_FACTOR) - AI_RESERVED_TOKENS)


def build_ai_batches(tweets, model_id):
    """Split tweets into batches that fit within model context. Yields list of tweet lists."""
    budget = get_batch_token_budget(model_id)
    batch = []
    used = 0
    for t in tweets:
        need = estimate_tokens_for_tweet(t)
        if batch and used + need > budget:
            yield batch
            batch = []
            used = 0
        batch.append(t)
        used += need
    if batch:
        yield batch
