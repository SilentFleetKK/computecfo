# 🏦 ComputeCFO — 算力财务官 — Your AI Financial Officer

**Stop guessing your AI costs. Start managing them.**

ComputeCFO is a lightweight, zero-dependency Python library that tracks, analyzes, and optimizes your LLM API spending. Think of it as a CFO for your AI project — it watches every dollar, warns you before you overspend, and tells you how to save more.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero-green)

## Why ComputeCFO?

Every AI developer eventually faces these questions:

- 💸 "Wait, I spent HOW much this month?"
- 🤔 "Which feature is burning through my budget?"
- 📉 "Am I getting good ROI on this AI investment?"
- 🚨 "How do I prevent a $500 surprise bill?"

ComputeCFO answers all of these with **3 lines of code**.

## Quick Start

```bash
pip install computecfo
```

```python
from computecfo import CostTracker

tracker = CostTracker()

# Record an API call (after your Claude/OpenAI/Gemini call)
tracker.record("claude-sonnet-4-20250514",
               input_tokens=1500, output_tokens=500,
               module="chatbot", action="respond")

# Check spending
print(tracker.get_today())
# {'cost': 0.012, 'calls': 1, 'total_tokens': 2000, ...}
```

That's it. ComputeCFO auto-calculates cost, stores in SQLite, and you're tracking.

## Features

### 💰 Cost Tracking
```python
tracker.get_today()           # Today's spending
tracker.get_this_month()      # Monthly total
tracker.get_by_module()       # Cost per feature
tracker.get_by_model()        # Cost per model
tracker.get_daily_trend(30)   # 30-day chart data
tracker.get_recent(20)        # Last 20 API calls
```

### 🚨 Budget Controls
```python
from computecfo import BudgetManager
from computecfo.models import BudgetConfig

config = BudgetConfig(
    daily_limit=5.0,      # $5/day
    monthly_limit=100.0,  # $100/month
    auto_downgrade=True,  # auto-switch to cheaper model when over budget
)

budget = BudgetManager(tracker, config)

# Before each API call:
check = budget.pre_call_check("claude-opus-4-20250514")
if check["approved"]:
    model = check["model"]  # might be downgraded to sonnet!
    # make your API call with `model`
else:
    print(f"Blocked: {check['reason']}")
```

**Three protection levels:**
| Level | Trigger | Action |
|-------|---------|--------|
| ⚠️ Warning | 80% of budget | Log warning |
| 🔴 Critical | 100% of budget | Auto-downgrade model |
| 🚨 Circuit Break | 150% of budget | Block all API calls |

### 📊 ROI Analysis
```python
from computecfo import CostAnalyzer

analyzer = CostAnalyzer(tracker)

# How efficient is your spending?
efficiency = analyzer.get_efficiency_score()
# {'score': 78, 'grade': 'B', 'deductions': [...]}

# What should you optimize?
suggestions = analyzer.get_savings_suggestions()
# [{'priority': 'high', 'suggestion': 'Premium models account for 70% of spending...'}]

# Cost prediction
prediction = analyzer.predict_monthly_cost()
# {'projected_monthly': 45.20, 'direction': 'stable', 'confidence': 'high'}
```

### 🔌 FastAPI Integration
```python
from fastapi import FastAPI
from computecfo import CostTracker
from computecfo.api import create_router

app = FastAPI()
tracker = CostTracker()
app.include_router(create_router(tracker), prefix="/api/cost")

# Now you have 11 endpoints:
# GET /api/cost/summary
# GET /api/cost/budget
# GET /api/cost/roi
# GET /api/cost/efficiency
# GET /api/cost/savings
# GET /api/cost/prediction
# GET /api/cost/report    ← full comprehensive report
# ...and more
```

## Supported Models

| Provider | Models | Auto-Pricing |
|----------|--------|-------------|
| **Anthropic** | Claude Opus 4, Sonnet 4, Haiku 3.5 | ✅ |
| **OpenAI** | GPT-4o, GPT-4o-mini, GPT-4.1, o3-mini | ✅ |
| **Google** | Gemini 2.5 Pro, Gemini 2.5 Flash | ✅ |
| **DeepSeek** | DeepSeek V3, DeepSeek R1 | ✅ |
| **Custom** | Any model — add your own pricing | ✅ |

Add custom models:
```python
from computecfo.models import MODEL_PRICING

MODEL_PRICING["my-custom-model"] = {"input": 2.0, "output": 8.0, "provider": "custom"}
```

## Architecture

```
┌──────────────┐
│  Your App    │
│  (API calls) │
└──────┬───────┘
       │ tracker.record(...)
       ▼
┌──────────────┐     ┌──────────────┐
│  ComputeCFO   │────▶│   SQLite     │
│  Core        │     │   (~/.computecfo/usage.db)
├──────────────┤     └──────────────┘
│ CostTracker  │ — record, query, trend
│ BudgetManager│ — limits, alerts, circuit breaker
│ CostAnalyzer │ — ROI, efficiency, prediction
│ FastAPI API  │ — drop-in router (optional)
└──────────────┘
```

## Zero Dependencies

ComputeCFO's core uses only Python standard library + SQLite. No external packages required.

Optional: Install `fastapi` for the API router, or `uvicorn` to serve it.

## Examples

See [`examples/quickstart.py`](examples/quickstart.py) for a complete walkthrough.

## Use Cases

- **AI Chatbot** — Track cost per conversation, optimize model selection
- **Content Generation** — Measure cost per output, calculate production ROI
- **Code Assistant** — Budget controls for team usage, per-developer tracking
- **Research Agent** — Monitor long-running agent costs, prevent runaway spending
- **Multi-Model Pipeline** — Compare provider costs, find the cheapest sufficient model

## Roadmap

- [ ] Webhook alerts (Slack, Discord, email)
- [ ] Multi-tenant support (per-user budgets)
- [ ] Dashboard UI (React component)
- [ ] Prometheus metrics exporter
- [ ] Cost anomaly detection (ML-based)

## Contributing

Pull requests welcome! Please open an issue first to discuss changes.

## License

MIT — see [LICENSE](LICENSE)

---

Built by [@SilentFleetKK](https://github.com/SilentFleetKK)
