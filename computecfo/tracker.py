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
                project TEXT DEFAULT '',
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
        conn.execute("CREATE INDEX IF NOT EXISTS idx_project ON usage(project)")
        # Migration: add project column to existing databases
        try:
            conn.execute("ALTER TABLE usage ADD COLUMN project TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass  # column already exists
        conn.commit()
        conn.close()

    def record(self, model: str, input_tokens: int, output_tokens: int,
               module: str = "", action: str = "", project: str = "",
               cached: bool = False, metadata: dict = None) -> UsageRecord:
        """Record a single API call."""
        record = UsageRecord(
            model=model,
            module=module,
            action=action,
            project=project,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached=cached,
            metadata=metadata or {},
        )

        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            """INSERT INTO usage (id, model, module, action, project, input_tokens, output_tokens,
               total_tokens, cost_usd, tier, cached, timestamp, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record.id, record.model, record.module, record.action, record.project,
             record.input_tokens, record.output_tokens, record.total_tokens,
             record.cost_usd, record.tier, int(record.cached),
             record.timestamp.isoformat(), json.dumps(record.metadata))
        )
        conn.commit()
        conn.close()

        log.info(f"Recorded: {model} | {project}/{module}/{action} | "
                 f"{input_tokens}+{output_tokens} tokens | ${record.cost_usd:.4f}")
        return record

    # ─── Query Methods ───
    # All query methods accept optional `project` param for independent accounting.

    @staticmethod
    def _build_where(days: int = None, project: str = "") -> tuple[str, list]:
        """Build parameterized WHERE clause. Returns (sql_fragment, params)."""
        conditions = []
        params = []
        if days:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            conditions.append("timestamp >= ?")
            params.append(cutoff)
        if project:
            conditions.append("project = ?")
            params.append(project)
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        return where, params

    def get_summary(self, days: int = None, project: str = "") -> dict:
        """Get cost summary. days=None for all-time, 1 for today, 7 for week, 30 for month."""
        conn = sqlite3.connect(str(self.db_path))
        where, params = self._build_where(days, project)

        row = conn.execute(f"""
            SELECT COALESCE(SUM(cost_usd), 0),
                   COALESCE(SUM(input_tokens), 0),
                   COALESCE(SUM(output_tokens), 0),
                   COALESCE(SUM(total_tokens), 0),
                   COUNT(*)
            FROM usage {where}
        """, params).fetchone()

        conn.close()
        result = {
            "cost": round(row[0], 4),
            "input_tokens": row[1],
            "output_tokens": row[2],
            "total_tokens": row[3],
            "calls": row[4],
            "period_days": days or "all",
        }
        if project:
            result["project"] = project
        return result

    def get_today(self, project: str = "") -> dict:
        return self.get_summary(days=1, project=project)

    def get_this_week(self, project: str = "") -> dict:
        return self.get_summary(days=7, project=project)

    def get_this_month(self, project: str = "") -> dict:
        return self.get_summary(days=30, project=project)

    def get_by_module(self, days: int = 30, project: str = "") -> list[dict]:
        """Cost breakdown by module."""
        conn = sqlite3.connect(str(self.db_path))
        where, params = self._build_where(days, project)
        rows = conn.execute(f"""
            SELECT module, SUM(cost_usd), SUM(total_tokens), COUNT(*)
            FROM usage {where} GROUP BY module ORDER BY SUM(cost_usd) DESC
        """, params).fetchall()
        conn.close()
        return [{"module": r[0] or "unknown", "cost": round(r[1], 4), "tokens": r[2], "calls": r[3]} for r in rows]

    def get_by_model(self, days: int = 30, project: str = "") -> list[dict]:
        """Cost breakdown by model."""
        conn = sqlite3.connect(str(self.db_path))
        where, params = self._build_where(days, project)
        rows = conn.execute(f"""
            SELECT model, SUM(cost_usd), SUM(total_tokens), COUNT(*)
            FROM usage {where} GROUP BY model ORDER BY SUM(cost_usd) DESC
        """, params).fetchall()
        conn.close()
        return [{"model": r[0], "cost": round(r[1], 4), "tokens": r[2], "calls": r[3]} for r in rows]

    def get_by_project(self, days: int = 30) -> list[dict]:
        """Cost breakdown by project — Alphabet-style independent accounting."""
        conn = sqlite3.connect(str(self.db_path))
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        rows = conn.execute("""
            SELECT project, SUM(cost_usd), SUM(total_tokens), COUNT(*)
            FROM usage WHERE timestamp >= ? GROUP BY project ORDER BY SUM(cost_usd) DESC
        """, (cutoff,)).fetchall()
        conn.close()
        return [{"project": r[0] or "default", "cost": round(r[1], 4), "tokens": r[2], "calls": r[3]} for r in rows]

    def get_daily_trend(self, days: int = 30, project: str = "") -> list[dict]:
        """Daily cost trend for charting."""
        conn = sqlite3.connect(str(self.db_path))
        where, params = self._build_where(days, project)
        rows = conn.execute(f"""
            SELECT DATE(timestamp) as day, SUM(cost_usd), SUM(total_tokens), COUNT(*)
            FROM usage {where}
            GROUP BY DATE(timestamp) ORDER BY day
        """, params).fetchall()
        conn.close()
        return [{"date": r[0], "cost": round(r[1], 4), "tokens": r[2], "calls": r[3]} for r in rows]

    def get_recent(self, limit: int = 20, project: str = "") -> list[dict]:
        """Most recent API calls."""
        conn = sqlite3.connect(str(self.db_path))
        params = []
        where = ""
        if project:
            where = "WHERE project = ?"
            params.append(project)
        params.append(limit)
        rows = conn.execute(f"""
            SELECT id, model, module, action, project, input_tokens, output_tokens,
                   total_tokens, cost_usd, tier, cached, timestamp
            FROM usage {where} ORDER BY timestamp DESC LIMIT ?
        """, params).fetchall()
        conn.close()
        return [{
            "id": r[0], "model": r[1], "module": r[2], "action": r[3],
            "project": r[4], "input_tokens": r[5], "output_tokens": r[6],
            "total_tokens": r[7], "cost_usd": round(r[8], 6), "tier": r[9],
            "cached": bool(r[10]), "timestamp": r[11],
        } for r in rows]

    def get_projected_monthly(self, project: str = "") -> float:
        """Project monthly cost based on current spending rate."""
        today_data = self.get_today(project=project)
        if today_data["calls"] == 0:
            week_data = self.get_this_week(project=project)
            daily_avg = week_data["cost"] / max(week_data["period_days"], 1)
        else:
            daily_avg = today_data["cost"]
        return round(daily_avg * 30, 2)
