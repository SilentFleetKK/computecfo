"""
🔔 Alerts — Multi-channel webhook notifications.
Supports Slack, Discord, Telegram Bot, generic webhooks, and custom handlers.
Uses only stdlib (urllib) — zero external dependencies.
"""
import json
import logging
from dataclasses import dataclass, field
from typing import Callable, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError

log = logging.getLogger("computecfo")


@dataclass
class AlertConfig:
    """Configuration for alert channels."""
    slack_webhook: str = ""          # Slack incoming webhook URL
    discord_webhook: str = ""        # Discord webhook URL
    telegram_bot_token: str = ""     # Telegram Bot API token (from @BotFather)
    telegram_chat_id: str = ""       # Telegram chat/group/channel ID
    custom_webhooks: list[str] = field(default_factory=list)  # Generic webhook URLs
    custom_handler: Optional[Callable] = None  # Custom callback function
    enabled: bool = True
    include_details: bool = True     # Include full budget data in alert


class AlertManager:
    """Send budget alerts to multiple channels."""

    def __init__(self, config: AlertConfig = None):
        self.config = config or AlertConfig()

    def send(self, level: str, message: str, data: dict = None):
        """
        Send an alert to all configured channels.

        Args:
            level: "warning", "critical", or "circuit_break"
            message: Human-readable alert message
            data: Optional budget/spending data to include
        """
        if not self.config.enabled:
            return

        if self.config.slack_webhook:
            self._send_slack(level, message, data)

        if self.config.discord_webhook:
            self._send_discord(level, message, data)

        if self.config.telegram_bot_token and self.config.telegram_chat_id:
            self._send_telegram(level, message, data)

        for url in self.config.custom_webhooks:
            self._send_generic(url, level, message, data)

        if self.config.custom_handler:
            try:
                self.config.custom_handler(level, message, data)
            except Exception as e:
                log.error(f"Custom alert handler failed: {e}")

    def _send_slack(self, level: str, message: str, data: dict = None):
        """Send alert to Slack via incoming webhook."""
        emoji = {"warning": "⚠️", "critical": "🔴", "circuit_break": "🚨"}.get(level, "ℹ️")
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"{emoji} ComputeCFO {level.upper()}"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": message}
            },
        ]
        if data and self.config.include_details:
            details = "\n".join(f"• *{k}*: {v}" for k, v in data.items() if k != "status")
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": details}
            })

        payload = {"blocks": blocks, "text": f"{emoji} {message}"}
        self._post(self.config.slack_webhook, payload, "Slack")

    def _send_discord(self, level: str, message: str, data: dict = None):
        """Send alert to Discord via webhook."""
        color = {"warning": 0xFFA500, "critical": 0xFF0000, "circuit_break": 0x8B0000}.get(level, 0x808080)
        embed = {
            "title": f"ComputeCFO {level.upper()}",
            "description": message,
            "color": color,
        }
        if data and self.config.include_details:
            embed["fields"] = [
                {"name": k, "value": str(v), "inline": True}
                for k, v in data.items() if k != "status"
            ]

        payload = {"embeds": [embed]}
        self._post(self.config.discord_webhook, payload, "Discord")

    def _send_telegram(self, level: str, message: str, data: dict = None):
        """Send alert to Telegram via Bot API."""
        emoji = {"warning": "\u26a0\ufe0f", "critical": "\U0001f534", "circuit_break": "\U0001f6a8"}.get(level, "\u2139\ufe0f")
        lines = [f"{emoji} *ComputeCFO {level.upper()}*", "", message]
        if data and self.config.include_details:
            lines.append("")
            for k, v in data.items():
                if k != "status":
                    lines.append(f"\u2022 *{k}*: `{v}`")

        text = "\n".join(lines)
        url = (f"https://api.telegram.org/bot{self.config.telegram_bot_token}"
               f"/sendMessage")
        payload = {
            "chat_id": self.config.telegram_chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }
        self._post(url, payload, "Telegram")

    def _send_generic(self, url: str, level: str, message: str, data: dict = None):
        """Send alert to a generic webhook (POST JSON)."""
        payload = {
            "source": "computecfo",
            "level": level,
            "message": message,
        }
        if data and self.config.include_details:
            payload["data"] = data
        self._post(url, payload, "webhook")

    @staticmethod
    def _post(url: str, payload: dict, channel_name: str):
        """POST JSON to a URL using stdlib."""
        try:
            body = json.dumps(payload).encode("utf-8")
            req = Request(url, data=body, headers={"Content-Type": "application/json"})
            with urlopen(req, timeout=5) as resp:
                if resp.status >= 300:
                    log.warning(f"Alert to {channel_name} returned HTTP {resp.status}")
        except URLError as e:
            log.error(f"Failed to send alert to {channel_name}: {e}")
        except Exception as e:
            log.error(f"Unexpected error sending alert to {channel_name}: {e}")


def create_budget_callbacks(alert_manager: AlertManager) -> dict:
    """
    Create callback functions for BudgetManager integration.

    Usage:
        alerts = AlertManager(AlertConfig(slack_webhook="https://..."))
        callbacks = create_budget_callbacks(alerts)
        budget = BudgetManager(tracker, config,
                               on_warn=callbacks["on_warn"],
                               on_critical=callbacks["on_critical"],
                               on_circuit_break=callbacks["on_circuit_break"])
    """
    def on_warn(data: dict):
        alert_manager.send(
            "warning",
            f"Budget warning: {data['period']} at {data['percent']} "
            f"(${data['spent']:.2f} / ${data['limit']:.2f})",
            data,
        )

    def on_critical(data: dict):
        alert_manager.send(
            "critical",
            f"Budget CRITICAL: {data['period']} at {data['percent']} "
            f"(${data['spent']:.2f} / ${data['limit']:.2f}). Models will be auto-downgraded.",
            data,
        )

    def on_circuit_break(data: dict):
        alert_manager.send(
            "circuit_break",
            f"CIRCUIT BREAKER TRIPPED: {data['period']} exceeded 150%! "
            f"(${data['spent']:.2f} / ${data['limit']:.2f}). All API calls blocked.",
            data,
        )

    return {
        "on_warn": on_warn,
        "on_critical": on_critical,
        "on_circuit_break": on_circuit_break,
    }
