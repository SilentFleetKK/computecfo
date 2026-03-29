"""
🎯 Decorators — Zero-intrusion cost tracking.
Wrap your API call functions with @track_cost to auto-capture usage.

Supports: Anthropic, OpenAI, Google, and custom response formats.
"""
import functools
import logging
from typing import Callable, Optional

log = logging.getLogger("computecfo")


def _extract_anthropic(response) -> dict | None:
    """Extract usage from Anthropic SDK response."""
    usage = getattr(response, "usage", None)
    if usage and hasattr(usage, "input_tokens") and hasattr(usage, "output_tokens"):
        model = getattr(response, "model", None)
        if model:
            return {
                "model": model,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
            }
    return None


def _extract_openai(response) -> dict | None:
    """Extract usage from OpenAI SDK response."""
    usage = getattr(response, "usage", None)
    if usage and hasattr(usage, "prompt_tokens") and hasattr(usage, "completion_tokens"):
        model = getattr(response, "model", None)
        if model:
            return {
                "model": model,
                "input_tokens": usage.prompt_tokens,
                "output_tokens": usage.completion_tokens,
            }
    return None


def _extract_dict(response) -> dict | None:
    """Extract usage from dict-style responses (Google, custom)."""
    if isinstance(response, dict):
        usage = response.get("usage") or response.get("usageMetadata", {})
        model = response.get("model", response.get("modelId", ""))
        input_t = usage.get("input_tokens") or usage.get("promptTokenCount") or usage.get("prompt_tokens", 0)
        output_t = usage.get("output_tokens") or usage.get("candidatesTokenCount") or usage.get("completion_tokens", 0)
        if model and (input_t or output_t):
            return {"model": model, "input_tokens": input_t, "output_tokens": output_t}
    return None


# Ordered extractors — try each until one works
_EXTRACTORS = [_extract_anthropic, _extract_openai, _extract_dict]


def track_cost(tracker, module: str = "", action: str = "",
               project: str = "", extractor: Callable = None):
    """
    Decorator to auto-track cost of API call functions.

    Usage:
        @track_cost(tracker, module="chatbot", action="respond")
        def ask_claude(prompt):
            return client.messages.create(model="claude-sonnet-4-20250514", ...)

    The decorated function must return an API response object.
    Supports Anthropic, OpenAI, and dict-format responses out of the box.
    Pass a custom `extractor` function for other formats:
        extractor(response) -> {"model": str, "input_tokens": int, "output_tokens": int}
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            response = func(*args, **kwargs)
            _record_from_response(tracker, response, module, action, project, extractor)
            return response

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            response = await func(*args, **kwargs)
            _record_from_response(tracker, response, module, action, project, extractor)
            return response

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    return decorator


def _record_from_response(tracker, response, module, action, project, extractor):
    """Try to extract usage from response and record it."""
    usage_data = None

    # Try custom extractor first
    if extractor:
        try:
            usage_data = extractor(response)
        except Exception as e:
            log.warning(f"Custom extractor failed: {e}")

    # Try built-in extractors
    if not usage_data:
        for ext in _EXTRACTORS:
            usage_data = ext(response)
            if usage_data:
                break

    if usage_data:
        kwargs = {
            "model": usage_data["model"],
            "input_tokens": usage_data["input_tokens"],
            "output_tokens": usage_data["output_tokens"],
            "module": module,
            "action": action,
        }
        if project:
            kwargs["project"] = project
        tracker.record(**kwargs)
    else:
        log.warning(f"track_cost: could not extract usage from {type(response).__name__} response")
