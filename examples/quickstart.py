"""
Quick start example — Track your first API calls in 30 seconds.
"""
from computecfo import CostTracker, BudgetManager, CostAnalyzer
from computecfo.models import BudgetConfig

# 1. Create tracker (stores in ~/.computecfo/usage.db by default)
tracker = CostTracker()

# 2. Record some API calls
tracker.record("claude-sonnet-4-20250514", input_tokens=1500, output_tokens=500,
               module="chatbot", action="respond")

tracker.record("claude-opus-4-20250514", input_tokens=3000, output_tokens=2000,
               module="analysis", action="deep_research")

tracker.record("gpt-4o-mini", input_tokens=500, output_tokens=200,
               module="chatbot", action="quick_reply")

# 3. Check spending
print("📊 Today's spending:")
today = tracker.get_today()
print(f"   ${today['cost']:.4f} | {today['calls']} calls | {today['total_tokens']} tokens")

print("\n📈 By model:")
for m in tracker.get_by_model():
    print(f"   {m['model']}: ${m['cost']:.4f} ({m['calls']} calls)")

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

# 6. Get savings suggestions
analyzer = CostAnalyzer(tracker)
print("\n💡 Savings suggestions:")
for s in analyzer.get_savings_suggestions():
    print(f"   [{s['priority']}] {s['suggestion']}")

# 7. Efficiency score
eff = analyzer.get_efficiency_score()
print(f"\n🎯 Efficiency: {eff['score']}/100 (Grade: {eff['grade']})")
