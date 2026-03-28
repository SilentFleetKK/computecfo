"""
💰 CostTracker — Core tracking engine.
Records every API call, stores in SQLite, provides query interface.
"""
import json
import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional
from .models import UsageRecord, calc_cost, get_model_tier

log = logging.getLogger("computecfo")

DEFAULT_DB = Path.home() / ".computecfo" / "usage.db"


class CostTracker:
    """Track LLM API costs with zero configuration."""

    def __init__(self, db_path: str | Path = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usage (
                id TEXT PRIMARY KEY,
                model TEXT NOT NULL,
                module TEXT DEFAULT '',
                action TEXT DEFAULT '',
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                cost_usd REAL DEFAULT 0,
                tier TEXT DEFAULT '',
                cached INTEGER DEFAULT 0,
                timestamp TEXT NOT NULL,
                metadata TEXT DEFAULT '{}'
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON usage(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_module ON usage(module)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_model ON usage(model)")
        conn.commit()
        conn.close()

    def record(self, model: str, input_tokens: int, output_tokens: int,
               module: str = "", action: str = "", cached: bool = False,
               metadata: dict = None) -> UsageRecord:
        """Record a single API call."""
        record = UsageRecord(
            model=model,
            module=module,
            action=action,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached=cached,
            metadata=metadata or {},
        )

        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            """INSERT INTO usage (id, model, module, action, input_tokens, output_tokens,
               total_tokens, cost_usd, tier, cached, timestamp, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record.id, record.model, record.module, record.action,
             record.input_tokens, record.output_tokens, record.total_tokens,
             record.cost_usd, record.tier, int(record.cached),
             record.timestamp.isoformat(), json.dumps(record.metadata))
        )
        conn.commit()
        conn.close()

        log.info(f"Recorded: {model} | {module}/{action} | "
                 f"{input_tokens}+{output_tokens} tokens | ${record.cost_usd:.4f}")
        return record

    # ─── Query Methods ───

    def get_summary(self, days: int = None) -> dict:
        """Get cost summary. days=None for all-time, 1 for today, 7 for week, 30 for month."""
        conn = sqlite3.connect(str(self.db_path))

        where = ""
        if days:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            where = f"WHERE timestamp >= '{cutoff}'"

        row = conn.execute(f"""
            SELECT COALESCE(SUM(cost_usd), 0),
                   COALESCE(SUM(input_tokens), 0),
                   COALESCE(SUM(output_tokens), 0),
                   COALESCE(SUM(total_tokens), 0),
                   COUNT(*)
            FROM usage {where}
        """).fetchone()

        conn.close()
        return {
            "cost": round(row[0], 4),
            "input_tokens": row[1],
            "output_tokens": row[2],
            "total_tokens": row[3],
            "calls": row[4],
            "period_days": days or "all",
        }

    def get_today(self) -> dict:
        return self.get_summary(days=1)

    def get_this_week(self) -> dict:
        return self.get_summary(days=7)

    def get_this_month(self) -> dict:
        return self.get_summary(days=30)

    def get_by_module(self, days: int = 30) -> list[dict]:
        """Cost breakdown by module."""
        conn = sqlite3.connect(str(self.db_path))
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        rows = conn.execute("""
            SELECT module, SUM(cost_usd), SUM(total_tokens), COUNT(*)
            FROM usage WHERE timestamp >= ? GROUP BY module ORDER BY SUM(cost_usd) DESC
        """, (cutoff,)).fetchall()
        conn.close()
        return [{"module": r[0] or "unknown", "cost": round(r[1], 4), "tokens": r[2], "calls": r[3]} for r in rows]

    def get_by_model(self, days: int = 30) -> list[dict]:
        """Cost breakdown by model."""
        conn = sqlite3.connect(str(self.db_path))
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        rows = conn.execute("""
            SELECT model, SUM(cost_usd), SUM(total_tokens), COUNT(*)
            FROM usage WHERE timestamp >= ? GROUP BY model ORDER BY SUM(cost_usd) DESC
        """, (cutoff,)).fetchall()
        conn.close()
        return [{"model": r[0], "cost": round(r[1], 4), "tokens": r[2], "calls": r[3]} for r in rows]

    def get_daily_trend(self, days: int = 30) -> list[dict]:
        """Daily cost trend for charting."""
        conn = sqlite3.connect(str(self.db_path))
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        rows = conn.execute("""
            SELECT DATE(timestamp) as day, SUM(cost_usd), SUM(total_tokens), COUNT(*)
            FROM usage WHERE timestamp >= ?
            GROUP BY DATE(timestamp) ORDER BY day
        """, (cutoff,)).fetchall()
        conn.close()
        return [{"date": r[0], "cost": round(r[1], 4), "tokens": r[2], "calls": r[3]} for r in rows]

    def get_recent(self, limit: int = 20) -> list[dict]:
        """Most recent API calls."""
        conn = sqlite3.connect(str(self.db_path))
        rows = conn.execute("""
            SELECT id, model, module, action, input_tokens, output_tokens,
                   total_tokens, cost_usd, tier, cached, timestamp
            FROM usage ORDER BY timestamp DESC LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [{
            "id": r[0], "model": r[1], "module": r[2], "action": r[3],
            "input_tokens": r[4], "output_tokens": r[5], "total_tokens": r[6],
            "cost_usd": round(r[7], 6), "tier": r[8], "cached": bool(r[9]),
            "timestamp": r[10],
        } for r in rows]

    def get_projected_monthly(self) -> float:
        """Project monthly cost based on current spending rate."""
        today_data = self.get_today()
        if today_data["calls"] == 0:
            week_data = self.get_this_week()
            daily_avg = week_data["cost"] / max(week_data["period_days"], 1)
        else:
            daily_avg = today_data["cost"]
        return round(daily_avg * 30, 2)
