"""
Quick start example — Track your first API calls in 30 seconds.
Now with v1.1 features: multi-project, value scoring, anomaly detection,
pre-call estimation, and decorator tracking.
"""
from computecfo import CostTracker, BudgetManager, CostAnalyzer
from computecfo.models import BudgetConfig

# 1. Create tracker (stores in ~/.computecfo/usage.db by default)
tracker = CostTracker()

# 2. Record some API calls — now with project support
tracker.record("claude-sonnet-4-20250514", input_tokens=1500, output_tokens=500,
               module="chatbot", action="respond", project="my-saas")

tracker.record("claude-opus-4-20250514", input_tokens=3000, output_tokens=2000,
               module="analysis", action="deep_research", project="my-saas")

tracker.record("gpt-4o-mini", input_tokens=500, output_tokens=200,
               module="chatbot", action="quick_reply", project="side-project")

tracker.record("gpt-4o", input_tokens=2000, output_tokens=1000,
               module="generation", action="content", project="side-project")

# 3. Check spending
print("📊 Today's spending:")
today = tracker.get_today()
print(f"   ${today['cost']:.4f} | {today['calls']} calls | {today['total_tokens']} tokens")

print("\n📈 By model:")
for m in tracker.get_by_model():
    print(f"   {m['model']}: ${m['cost']:.4f} ({m['calls']} calls)")

# NEW: By project (Alphabet-style independent accounting)
print("\n🏢 By project:")
for p in tracker.get_by_project():
    print(f"   {p['project']}: ${p['cost']:.4f} ({p['calls']} calls)")

# 4. Set up budget controls
config = BudgetConfig(daily_limit=5.0, monthly_limit=50.0)
budget = BudgetManager(tracker, config)

print("\n🚨 Budget status:")
status = budget.check_all()
for period, data in status.items():
    if isinstance(data, dict) and "percent" in data:
        emoji = "🟢" if data["status"] == "ok" else "🟡" if data["status"] == "warning" else "🔴"
        print(f"   {emoji} {period}: {data['percent']} used (${data['spent']:.2f} / ${data['limit']:.2f})")

# 5. Pre-call budget check (with auto-downgrade)
print("\n🤖 Pre-call check:")
check = budget.pre_call_check("claude-opus-4-20250514")
if check["approved"]:
    model = check["model"]
    if check.get("downgraded"):
        print(f"   ⚠️ Downgraded: {check['original_model']} → {model}")
    else:
        print(f"   ✅ Approved: {model} (${check['remaining']:.2f} remaining)")
else:
    print(f"   ❌ Blocked: {check['reason']}")

# NEW: Pre-call cost estimation
print("\n💰 Cost estimation (before calling API):")
estimate = budget.estimate_call_cost(
    "claude-opus-4-20250514",
    prompt="Analyze this quarterly financial report and provide key insights...",
)
print(f"   Model: {estimate['model']}")
print(f"   Estimated tokens: ~{estimate['estimated_input_tokens']} in / ~{estimate['estimated_output_tokens']} out")
print(f"   Estimated cost: ${estimate['estimated_cost']:.4f}")
print(f"   Budget remaining: ${estimate['budget_remaining']:.2f}")
if estimate['cheaper_alternative']:
    alt = estimate['cheaper_alternative']
    print(f"   💡 Cheaper option: {alt['model']} at ${alt['estimated_cost']:.4f} (save ${alt['savings']:.4f})")

# 6. Get savings suggestions
analyzer = CostAnalyzer(tracker)
print("\n💡 Savings suggestions:")
for s in analyzer.get_savings_suggestions():
    print(f"   [{s['priority']}] {s['suggestion']}")

# 7. Efficiency score
eff = analyzer.get_efficiency_score()
if "grade" in eff:
    print(f"\n🎯 Efficiency: {eff['score']}/100 (Grade: {eff['grade']})")
else:
    print(f"\n🎯 Efficiency: {eff.get('message', 'Not enough data')}")

# NEW: Model value-for-money scores (Graham's intrinsic value)
print("\n📊 Model Value Scores (性价比):")
for v in analyzer.get_model_value_scores():
    print(f"   {v['model']}: {v['value_score']}/100 (Grade {v['grade']}) — ${v['cost_per_1k_tokens']:.4f}/1k tokens")
    if v['recommendation']:
        print(f"      💡 {v['recommendation']}")

# NEW: Anomaly detection (Mr. Market alarm)
print("\n🔍 Anomaly Detection:")
for a in analyzer.detect_anomalies():
    severity = {"high": "🚨", "medium": "⚠️", "info": "ℹ️"}.get(a.get("severity", ""), "")
    print(f"   {severity} [{a['type']}] {a['message']}")

# ─── Decorator example (commented — requires actual API client) ───
# from computecfo import track_cost
#
# @track_cost(tracker, module="chatbot", action="respond", project="my-saas")
# def ask_claude(prompt):
#     import anthropic
#     client = anthropic.Anthropic()
#     return client.messages.create(
#         model="claude-sonnet-4-20250514",
#         max_tokens=1024,
#         messages=[{"role": "user", "content": prompt}],
#     )
#
# response = ask_claude("Hello!")  # cost auto-tracked!

# ─── Webhook alerts example (commented — requires webhook URL) ───
# from computecfo import AlertManager, AlertConfig, create_budget_callbacks
#
# alerts = AlertManager(AlertConfig(
#     slack_webhook="https://hooks.slack.com/services/T.../B.../...",
#     discord_webhook="https://discord.com/api/webhooks/...",
# ))
# callbacks = create_budget_callbacks(alerts)
# budget = BudgetManager(tracker, config,
#                        on_warn=callbacks["on_warn"],
#                        on_critical=callbacks["on_critical"],
#                        on_circuit_break=callbacks["on_circuit_break"])
