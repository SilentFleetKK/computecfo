"""
🏦 ComputeCFO Server — Standalone AI Financial Officer
Run: python3 server.py
"""
import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from computecfo import CostTracker
from computecfo.api import create_router
from computecfo.models import BudgetConfig

# ─── Config ───
HOST = "0.0.0.0"
PORT = 8878
DB_PATH = None  # None = default ~/.computecfo/usage.db

# ─── App ───
app = FastAPI(
    title="ComputeCFO",
    description="Your AI Financial Officer — Track, analyze, and optimize LLM API spending",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── API ───
tracker = CostTracker(db_path=DB_PATH)
budget_config = BudgetConfig(daily_limit=10.0, monthly_limit=200.0)
app.include_router(create_router(tracker, budget_config), prefix="/api/cost")


# ─── Seed demo data (only if DB is empty) ───
@app.on_event("startup")
async def seed_demo_data():
    """Seed demo data so the dashboard isn't empty on first launch."""
    summary = tracker.get_summary()
    if summary["calls"] > 0:
        return

    import random
    from datetime import datetime, timezone, timedelta

    models_config = [
        ("claude-sonnet-4-20250514", "chatbot", ["respond", "summarize", "translate"]),
        ("claude-opus-4-20250514", "analysis", ["deep_research", "report"]),
        ("gpt-4o-mini", "chatbot", ["quick_reply", "classify"]),
        ("gpt-4o", "generation", ["content", "outline"]),
        ("gemini-2.5-flash", "pipeline", ["extract", "validate"]),
        ("deepseek-v3", "pipeline", ["batch_process", "embed"]),
    ]
    projects = ["saas-app", "research-agent", "content-engine"]

    # Generate 14 days of realistic data
    for days_ago in range(14, 0, -1):
        num_calls = random.randint(5, 20)
        for _ in range(num_calls):
            model, module, actions = random.choice(models_config)
            action = random.choice(actions)
            project = random.choice(projects)
            input_t = random.randint(200, 5000)
            output_t = random.randint(100, 3000)

            record = tracker.record(
                model=model,
                input_tokens=input_t,
                output_tokens=output_t,
                module=module,
                action=action,
                project=project,
            )
            # Backdate the timestamp
            import sqlite3
            ts = (datetime.now(timezone.utc) - timedelta(
                days=days_ago,
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )).isoformat()
            conn = sqlite3.connect(str(tracker.db_path))
            conn.execute("UPDATE usage SET timestamp = ? WHERE id = ?", (ts, record.id))
            conn.commit()
            conn.close()


# ─── Static files ───
FRONTEND_DIR = Path(__file__).parent / "frontend"


@app.get("/")
async def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# ─── Run ───
if __name__ == "__main__":
    import uvicorn
    print(f"\n🏦 ComputeCFO Dashboard → http://localhost:{PORT}\n")
    uvicorn.run(app, host=HOST, port=PORT)
