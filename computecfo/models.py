"""
Data models and pricing configuration.
"""
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional


# ─── LLM Pricing (per 1M tokens, updated 2026-03) ───
MODEL_PRICING = {
    # Anthropic
    "claude-opus-4-20250514": {"input": 15.0, "output": 75.0, "provider": "anthropic"},
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0, "provider": "anthropic"},
    "claude-haiku-3.5": {"input": 0.80, "output": 4.0, "provider": "anthropic"},
    # OpenAI
    "gpt-4o": {"input": 5.0, "output": 15.0, "provider": "openai"},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60, "provider": "openai"},
    "gpt-4.1": {"input": 2.0, "output": 8.0, "provider": "openai"},
    "o3-mini": {"input": 1.10, "output": 4.40, "provider": "openai"},
    # Google
    "gemini-2.5-pro": {"input": 1.25, "output": 10.0, "provider": "google"},
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60, "provider": "google"},
    # DeepSeek
    "deepseek-v3": {"input": 0.27, "output": 1.10, "provider": "deepseek"},
    "deepseek-r1": {"input": 0.55, "output": 2.19, "provider": "deepseek"},
    # Default fallback
    "default": {"input": 3.0, "output": 15.0, "provider": "unknown"},
}


def calc_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost in USD for a single API call."""
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["default"])
    return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000


def get_model_tier(model: str) -> str:
    """Classify model into cost tier: premium / standard / economy."""
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["default"])
    avg = (pricing["input"] + pricing["output"]) / 2
    if avg > 20:
        return "premium"
    elif avg > 3:
        return "standard"
    return "economy"


@dataclass
class UsageRecord:
    """A single API usage record."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    model: str = ""
    module: str = ""          # which feature used it (e.g. "generation", "analysis")
    action: str = ""          # specific action (e.g. "summarize", "translate")
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    tier: str = ""            # premium / standard / economy
    cached: bool = False      # was this served from cache?
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        self.total_tokens = self.input_tokens + self.output_tokens
        if not self.cost_usd:
            self.cost_usd = calc_cost(self.model, self.input_tokens, self.output_tokens)
        if not self.tier:
            self.tier = get_model_tier(self.model)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "model": self.model,
            "module": self.module,
            "action": self.action,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": round(self.cost_usd, 6),
            "tier": self.tier,
            "cached": self.cached,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class BudgetConfig:
    """Budget limits configuration."""
    daily_limit: float = 5.0       # USD per day
    weekly_limit: float = 25.0     # USD per week
    monthly_limit: float = 100.0   # USD per month
    warn_threshold: float = 0.8    # warn at 80%
    critical_threshold: float = 1.0  # critical at 100%
    circuit_break_threshold: float = 1.5  # auto-stop at 150%
    auto_downgrade: bool = True    # auto-switch to cheaper model when over budget
    downgrade_map: dict = field(default_factory=lambda: {
        "claude-opus-4-20250514": "claude-sonnet-4-20250514",
        "gpt-4o": "gpt-4o-mini",
        "gemini-2.5-pro": "gemini-2.5-flash",
    })
