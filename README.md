# 🏦 ComputeCFO — Your AI Financial Officer

**Stop guessing your AI costs. Start managing them like a CFO.**

ComputeCFO is an AI Financial Officer Agent that tracks, analyzes, and optimizes your LLM API spending. It works both as a **standalone dashboard** and as a **Python library** you can integrate into any project. Inspired by Graham's value investing, Pacioli's double-entry bookkeeping, and Alphabet's independent accounting model.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Zero Dependencies](https://img.shields.io/badge/Core_Dependencies-Zero-green)
![Version](https://img.shields.io/badge/Version-1.1.0-brightgreen)

## Why ComputeCFO?

Every AI developer eventually faces these questions:

- 💸 "Wait, I spent HOW much this month?"
- 🤔 "Which feature is burning through my budget?"
- 📉 "Am I getting good ROI on this AI investment?"
- 🚨 "How do I prevent a $500 surprise bill?"
- 🏢 "How much is each project costing independently?"
- 🔍 "Is there an anomaly in my spending pattern?"

ComputeCFO answers all of these — as a library with **3 lines of code**, or as a full dashboard with **1 command**.

## Quick Start

### Option 1: Standalone Dashboard

```bash
pip install computecfo fastapi uvicorn
python -m computecfo.server  # or: python server.py
# Open http://localhost:8878
```

The dashboard provides real-time cost monitoring with:
- Financial overview with daily/weekly/monthly summaries
- Interactive spending trend charts
- Model value scoring (Graham-inspired)
- Project-level independent accounting
- Anomaly detection ("Mr. Market" alarm)
- Pre-call cost estimator
- Dark/Light theme toggle
- Chinese/English language switch

### Option 2: Python Library

```bash
pip install computecfo
```

```python
from computecfo import CostTracker

tracker = CostTracker()

# Record an API call (after your Claude/OpenAI/Gemini call)
tracker.record("claude-sonnet-4-20250514",
               input_tokens=1500, output_tokens=500,
               module="chatbot", action="respond",
               project="my-saas")

# Check spending
print(tracker.get_today())
# {'cost': 0.012, 'calls': 1, 'total_tokens': 2000, ...}
```

## Features

### 💰 Cost Tracking
```python
tracker.get_today()                      # Today's spending
tracker.get_this_month()                 # Monthly total
tracker.get_by_module()                  # Cost per feature
tracker.get_by_model()                   # Cost per model
tracker.get_by_project()                 # Cost per project
tracker.get_daily_trend(30)              # 30-day chart data
tracker.get_recent(20)                   # Last 20 API calls
tracker.get_projected_monthly()          # Projected monthly cost

# All query methods support project filtering:
tracker.get_today(project="my-saas")
tracker.get_by_model(project="internal-tools")
```

### 🎯 @track_cost Decorator
```python
from computecfo import CostTracker, track_cost

tracker = CostTracker()

@track_cost(tracker, module="chatbot", action="respond", project="my-saas")
def ask_claude(prompt):
    response = anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        messages=[{"role": "user", "content": prompt}]
    )
    return response

# Cost is automatically recorded — works with Anthropic, OpenAI, and dict responses
result = ask_claude("Hello!")
```

Supports sync and async functions, with auto-detection for Anthropic and OpenAI response formats.

### 🏢 Multi-Project Accounting
```python
# Alphabet-style independent cost tracking per project
tracker.record("claude-opus-4-20250514", 2000, 800,
               module="search", project="google-search")
tracker.record("gpt-4o", 1500, 600,
               module="vision", project="waymo")

# Independent P&L per project
for p in tracker.get_by_project():
    print(f"{p['project']}: ${p['cost']:.2f}")
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
else:
    print(f"Blocked: {check['reason']}")
```

**Three protection levels:**
| Level | Trigger | Action |
|-------|---------|--------|
| Warning | 80% of budget | Log warning |
| Critical | 100% of budget | Auto-downgrade model |
| Circuit Break | 150% of budget | Block all API calls |

### 🧮 Pre-Call Cost Estimation
```python
from computecfo.models import estimate_tokens

# Know the cost before you spend — Margin of Safety
estimate = budget.estimate_call_cost(
    model="claude-opus-4-20250514",
    prompt="Analyze this codebase and suggest improvements..."
)
print(f"Estimated cost: ${estimate['estimated_cost']:.4f}")
print(f"Budget remaining: ${estimate['budget_remaining']:.2f}")
if estimate.get("cheaper_alternative"):
    print(f"Try {estimate['cheaper_alternative']} instead")
```

### 📊 Model Value Scoring
```python
from computecfo import CostAnalyzer

analyzer = CostAnalyzer(tracker)

# Graham-inspired value analysis — find the "undervalued" models
for score in analyzer.get_model_value_scores():
    print(f"{score['model']}: {score['grade']} "
          f"(value: {score['value_score']}/100) — {score['recommendation']}")
```

### 🔍 Anomaly Detection
```python
# "Mr. Market" alarm — detect irrational spending patterns
anomalies = analyzer.detect_anomalies()
for a in anomalies:
    print(f"[{a['severity']}] {a['type']}: {a['message']}")
# [high] spending_spike: Spending on 2025-01-15 was 3.2x above average
# [medium] premium_creep: Premium model usage increased from 20% to 65%
```

### 🔔 Webhook Alerts
```python
from computecfo import AlertManager, AlertConfig, create_budget_callbacks

alerts = AlertManager(AlertConfig(
    telegram_bot_token="123456:ABC-DEF...",  # from @BotFather
    telegram_chat_id="-1001234567890",       # your chat/group/channel ID
    # Also supports:
    # slack_webhook="https://hooks.slack.com/services/...",
    # discord_webhook="https://discord.com/api/webhooks/...",
))

# Connect to budget system
callbacks = create_budget_callbacks(alerts)
budget = BudgetManager(tracker, config, callbacks=callbacks)
# Now you get Slack/Discord alerts on budget warnings, critical, and circuit breaks
```

### 🔌 FastAPI Integration
```python
from fastapi import FastAPI
from computecfo import CostTracker
from computecfo.api import create_router

app = FastAPI()
tracker = CostTracker()
app.include_router(create_router(tracker), prefix="/api/cost")

# 14 endpoints available:
# GET /api/cost/summary?days=7&project=my-saas
# GET /api/cost/by-module
# GET /api/cost/by-model
# GET /api/cost/by-project
# GET /api/cost/daily-trend
# GET /api/cost/recent
# GET /api/cost/budget
# GET /api/cost/estimate
# GET /api/cost/roi
# GET /api/cost/efficiency
# GET /api/cost/prediction
# GET /api/cost/savings
# GET /api/cost/model-values
# GET /api/cost/anomalies
# GET /api/cost/report
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
┌──────────────────────────────────────────┐
│           ComputeCFO Agent               │
├──────────────────────────────────────────┤
│                                          │
│  ┌─────────────┐   ┌─────────────────┐  │
│  │ Dashboard UI │   │ FastAPI Server  │  │
│  │ (HTML/JS/CSS)│◀─▶│ (server.py)     │  │
│  │ Chart.js     │   │ 14 REST APIs    │  │
│  │ i18n (中/EN) │   └────────┬────────┘  │
│  │ Dark/Light   │            │           │
│  └─────────────┘            ▼           │
│              ┌──────────────────────┐    │
│              │    Core Engine       │    │
│              ├──────────────────────┤    │
│              │ CostTracker  — track │    │
│              │ BudgetManager— guard │    │
│              │ CostAnalyzer — score │    │
│              │ AlertManager — alert │    │
│              │ @track_cost  — auto  │    │
│              └──────────┬───────────┘    │
│                         ▼               │
│              ┌──────────────────────┐    │
│              │  SQLite              │    │
│              │  ~/.computecfo/      │    │
│              │  usage.db            │    │
│              └──────────────────────┘    │
├──────────────────────────────────────────┤
│  Zero core dependencies │ Python 3.10+  │
└──────────────────────────────────────────┘
```

## Dashboard

The standalone dashboard provides a full financial overview with interactive charts.

**Features:**
- Real-time spending summaries (today / week / month / projected)
- Daily spending trend line chart
- Cost breakdown by model (doughnut chart)
- Project-level P&L with bar chart
- Model value scoring table (Graham-inspired grades A-F)
- Anomaly detection alerts
- Pre-call cost estimator
- Recent activity log
- Budget controls with 3-level protection
- Dark / Light theme toggle
- Chinese / English language switch
- Auto-refresh every 30 seconds

## Zero Dependencies

ComputeCFO's core uses only Python standard library + SQLite. No external packages required.

Optional: Install `fastapi` + `uvicorn` for the dashboard and API server.

## Examples

See [`examples/quickstart.py`](examples/quickstart.py) for a complete walkthrough covering all features.

## Use Cases

- **AI Chatbot** — Track cost per conversation, optimize model selection
- **Content Generation** — Measure cost per output, calculate production ROI
- **Code Assistant** — Budget controls for team usage, per-developer tracking
- **Research Agent** — Monitor long-running agent costs, prevent runaway spending
- **Multi-Model Pipeline** — Compare provider costs, find the cheapest sufficient model
- **Multi-Project Organization** — Independent P&L per project, Alphabet-style

## Contributing

Pull requests welcome! Please open an issue first to discuss changes.

## License

MIT — see [LICENSE](LICENSE)

---

Built by [@SilentFleetKK](https://github.com/SilentFleetKK)
