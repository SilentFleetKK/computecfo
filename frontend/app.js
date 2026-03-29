/**
 * 🏦 ComputeCFO Dashboard — Frontend Application
 * Fetches data from the FastAPI backend and renders charts/tables.
 * Supports dark/light theme and Chinese/English i18n.
 */

const API = '/api/cost';
const COLORS = {
  blue: '#3b82f6', purple: '#8b5cf6', green: '#10b981',
  orange: '#f59e0b', red: '#ef4444', cyan: '#06b6d4',
  pink: '#ec4899', indigo: '#6366f1', teal: '#14b8a6',
  amber: '#d97706', lime: '#84cc16', rose: '#f43f5e',
};
const PALETTE = Object.values(COLORS);

let trendChart = null;
let modelChart = null;
let projectChart = null;

// ═══════════════════════════════════════════════
//  i18n — Chinese / English translations
// ═══════════════════════════════════════════════
const I18N = {
  en: {
    // Nav
    nav_overview: 'Overview', nav_budget: 'Budget', nav_models: 'Models',
    nav_projects: 'Projects', nav_anomalies: 'Anomalies', nav_estimator: 'Estimator',
    nav_activity: 'Activity',
    // Titles
    title_overview: 'Financial Overview', title_budget: 'Budget Controls',
    title_models: 'Model Value Scores', title_projects: 'Project Accounting',
    title_anomalies: 'Anomaly Detection', title_estimator: 'Pre-Call Cost Estimator',
    title_activity: 'Recent Activity',
    // Subtitles
    subtitle_models: 'Graham-inspired value analysis — find the "undervalued" models',
    subtitle_projects: 'Alphabet-style independent cost tracking per project',
    subtitle_anomalies: '"Mr. Market" alarm — detect irrational spending patterns',
    subtitle_estimator: 'Know the cost before you spend — Margin of Safety',
    // Cards
    today: 'Today', this_week: 'This Week', this_month: 'This Month',
    projected_monthly: 'Projected Monthly', all_projects: 'All Projects',
    // Chart titles
    daily_trend: 'Daily Spending Trend', cost_by_model: 'Cost by Model',
    efficiency_score: 'Efficiency Score', savings_suggestions: 'Savings Suggestions',
    cost_by_project: 'Cost by Project', project_breakdown: 'Project Breakdown',
    // Table headers
    th_model: 'Model', th_tier: 'Tier', th_value_score: 'Value Score',
    th_grade: 'Grade', th_cost_1k: 'Cost/1K Tokens', th_total_spent: 'Total Spent',
    th_calls: 'Calls', th_recommendation: 'Recommendation', th_project: 'Project',
    th_cost: 'Cost', th_tokens: 'Tokens', th_time: 'Time', th_module: 'Module',
    th_action: 'Action',
    // Estimator
    est_model: 'Model', est_prompt_label: 'Prompt (or paste text to estimate)',
    est_prompt_placeholder: 'Paste your prompt here to estimate cost...',
    est_token_label: 'Or specify token count directly', est_button: 'Estimate Cost',
    est_input_tokens: 'Input Tokens (est.)', est_output_tokens: 'Output Tokens (est.)',
    est_cost: 'Estimated Cost', est_remaining: 'Budget Remaining',
    est_cheaper: 'Cheaper Alternative',
    // Budget
    budget_used: 'used', budget_remaining: 'remaining',
    // Misc
    refresh_hint: 'Auto-refreshes every 30s',
    calls_unit: 'calls', tokens_unit: 'tokens',
  },
  zh: {
    // Nav
    nav_overview: '总览', nav_budget: '预算', nav_models: '模型',
    nav_projects: '项目', nav_anomalies: '异常检测', nav_estimator: '成本估算',
    nav_activity: '调用记录',
    // Titles
    title_overview: '财务总览', title_budget: '预算控制',
    title_models: '模型性价比评估', title_projects: '项目独立核算',
    title_anomalies: '异常消费检测', title_estimator: '预检成本估算',
    title_activity: '最近调用记录',
    // Subtitles
    subtitle_models: '格雷厄姆内在价值分析 — 找到"被低估"的高性价比模型',
    subtitle_projects: 'Alphabet 式独立核算 — 按项目追踪每一分钱',
    subtitle_anomalies: '"市场先生"警报 — 检测非理性消费模式',
    subtitle_estimator: '先算账再花钱 — 安全边际思维',
    // Cards
    today: '今日', this_week: '本周', this_month: '本月',
    projected_monthly: '月度预测', all_projects: '全部项目',
    // Chart titles
    daily_trend: '每日花费趋势', cost_by_model: '按模型分布',
    efficiency_score: '效率评分', savings_suggestions: '节省建议',
    cost_by_project: '按项目分布', project_breakdown: '项目明细',
    // Table headers
    th_model: '模型', th_tier: '层级', th_value_score: '性价比',
    th_grade: '评级', th_cost_1k: '每千Token成本', th_total_spent: '总花费',
    th_calls: '调用数', th_recommendation: '建议', th_project: '项目',
    th_cost: '成本', th_tokens: 'Token数', th_time: '时间', th_module: '模块',
    th_action: '操作',
    // Estimator
    est_model: '模型', est_prompt_label: '输入提示词（粘贴文本以估算）',
    est_prompt_placeholder: '在此粘贴提示词以估算成本...',
    est_token_label: '或直接输入Token数', est_button: '估算成本',
    est_input_tokens: '输入Token（估）', est_output_tokens: '输出Token（估）',
    est_cost: '预估成本', est_remaining: '剩余预算',
    est_cheaper: '更便宜的替代',
    // Budget
    budget_used: '已用', budget_remaining: '剩余',
    // Misc
    refresh_hint: '每30秒自动刷新',
    calls_unit: '次调用', tokens_unit: 'tokens',
  },
};

let currentLang = localStorage.getItem('computecfo-lang') || 'en';

function t(key) { return (I18N[currentLang] || I18N.en)[key] || key; }

function applyI18n() {
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    const text = t(key);
    if (text) el.textContent = text;
  });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    const text = t(key);
    if (text) el.placeholder = text;
  });
  // Update lang toggle button text
  const langBtn = document.querySelector('#lang-toggle .toggle-icon');
  if (langBtn) langBtn.textContent = currentLang === 'en' ? '中' : 'EN';
}

// ═══════════════════════════════════════════════
//  Theme — Dark / Light toggle
// ═══════════════════════════════════════════════
let currentTheme = localStorage.getItem('computecfo-theme') || 'dark';

function applyTheme(theme) {
  currentTheme = theme;
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('computecfo-theme', theme);
  const icon = document.getElementById('theme-icon');
  if (icon) icon.textContent = theme === 'dark' ? '☀️' : '🌙';
  // Re-render charts with correct colors
  if (trendChart || modelChart || projectChart) {
    loadDashboard();
  }
}

function getChartColors() {
  const style = getComputedStyle(document.documentElement);
  return {
    grid: style.getPropertyValue('--chart-grid').trim() || 'rgba(42,53,72,0.5)',
    tick: style.getPropertyValue('--chart-tick').trim() || '#5a6a7a',
    legend: style.getPropertyValue('--chart-legend').trim() || '#8899aa',
  };
}

// Init theme & lang
document.getElementById('theme-toggle').addEventListener('click', () => {
  applyTheme(currentTheme === 'dark' ? 'light' : 'dark');
});

document.getElementById('lang-toggle').addEventListener('click', () => {
  currentLang = currentLang === 'en' ? 'zh' : 'en';
  localStorage.setItem('computecfo-lang', currentLang);
  applyI18n();
  loadDashboard(); // Re-render dynamic content with new language
});

applyTheme(currentTheme);
applyI18n();

// ─── Navigation ───
document.querySelectorAll('.nav-links li').forEach(li => {
  li.addEventListener('click', () => {
    document.querySelectorAll('.nav-links li').forEach(l => l.classList.remove('active'));
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    li.classList.add('active');
    document.getElementById(li.dataset.section).classList.add('active');
  });
});

// ─── API helpers ───
async function api(path) {
  const res = await fetch(`${API}${path}`);
  return res.json();
}

function $(id) { return document.getElementById(id); }
function fmt(n) { return `$${Number(n).toFixed(2)}`; }
function fmtSmall(n) { return `$${Number(n).toFixed(4)}`; }

// ─── Load all data ───
async function loadDashboard() {
  const [summary, trend, byModel, byProject, budget, efficiency,
         suggestions, modelValues, anomalies, recent, prediction] = await Promise.all([
    api('/summary'),
    api('/daily-trend?days=30'),
    api('/by-model'),
    api('/by-project'),
    api('/budget'),
    api('/efficiency'),
    api('/savings'),
    api('/model-values'),
    api('/anomalies'),
    api('/recent?limit=50'),
    api('/prediction'),
  ]);

  renderSummary(summary, prediction);
  renderTrendChart(trend);
  renderModelChart(byModel);
  renderEfficiency(efficiency);
  renderSuggestions(suggestions);
  renderBudget(budget);
  renderModelValues(modelValues);
  renderProjects(byProject);
  renderAnomalies(anomalies);
  renderActivity(recent);
  populateProjectFilter(byProject);
  applyI18n(); // re-apply translations after dynamic render
}

// ─── Summary Cards ───
function renderSummary(s, prediction) {
  $('today-cost').textContent = fmt(s.today.cost);
  $('today-calls').textContent = `${s.today.calls} ${t('calls_unit')} · ${s.today.total_tokens.toLocaleString()} ${t('tokens_unit')}`;
  $('week-cost').textContent = fmt(s.week.cost);
  $('week-calls').textContent = `${s.week.calls} ${t('calls_unit')}`;
  $('month-cost').textContent = fmt(s.month.cost);
  $('month-calls').textContent = `${s.month.calls} ${t('calls_unit')}`;
  $('projected-cost').textContent = fmt(s.projected_monthly);

  if (prediction && prediction.direction) {
    const arrows = { increasing: '↑ Increasing', decreasing: '↓ Decreasing', stable: '→ Stable' };
    $('projected-direction').textContent = `${arrows[prediction.direction] || '—'} (${prediction.confidence} confidence)`;
  }
}

// ─── Trend Chart ───
function renderTrendChart(data) {
  const ctx = $('trend-chart').getContext('2d');
  if (trendChart) trendChart.destroy();
  const cc = getChartColors();

  trendChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.map(d => d.date.slice(5)),
      datasets: [{
        label: currentLang === 'zh' ? '每日成本 ($)' : 'Daily Cost ($)',
        data: data.map(d => d.cost),
        borderColor: COLORS.blue,
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.3,
        pointRadius: 3,
        pointHoverRadius: 6,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => `$${ctx.parsed.y.toFixed(4)} · ${data[ctx.dataIndex].calls} ${t('calls_unit')}`,
          },
        },
      },
      scales: {
        x: { grid: { color: cc.grid }, ticks: { color: cc.tick, font: { size: 11 } } },
        y: {
          grid: { color: cc.grid },
          ticks: { color: cc.tick, font: { size: 11 }, callback: v => `$${v.toFixed(2)}` },
        },
      },
    },
  });

  $('trend-chart').parentElement.style.height = '260px';
  $('trend-chart').style.height = '220px';
}

// ─── Model Donut Chart ───
function renderModelChart(data) {
  const ctx = $('model-chart').getContext('2d');
  if (modelChart) modelChart.destroy();
  const cc = getChartColors();

  modelChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: data.map(d => d.model.split('-').slice(0, 2).join('-')),
      datasets: [{
        data: data.map(d => d.cost),
        backgroundColor: PALETTE.slice(0, data.length),
        borderWidth: 0,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: {
          position: 'right',
          labels: { color: cc.legend, font: { size: 11 }, padding: 8, usePointStyle: true },
        },
        tooltip: {
          callbacks: { label: ctx => ` ${ctx.label}: $${ctx.parsed.toFixed(4)}` },
        },
      },
    },
  });

  $('model-chart').parentElement.style.height = '260px';
  $('model-chart').style.height = '220px';
}

// ─── Efficiency Score ───
function renderEfficiency(data) {
  const score = data.score || 0;
  $('efficiency-score').textContent = score;
  $('efficiency-grade').textContent = data.grade || data.message || '';

  // Animate ring
  const circumference = 2 * Math.PI * 52;
  const offset = circumference - (score / 100) * circumference;
  const fill = $('ring-fill');
  fill.style.strokeDasharray = circumference;
  fill.style.strokeDashoffset = offset;

  // Color based on score
  const color = score >= 80 ? COLORS.green : score >= 60 ? COLORS.orange : COLORS.red;
  fill.style.stroke = color;

  // Deductions
  const list = $('efficiency-deductions');
  list.innerHTML = '';
  (data.deductions || []).forEach(d => {
    const li = document.createElement('li');
    li.textContent = d;
    list.appendChild(li);
  });
  if (!data.deductions?.length) {
    const li = document.createElement('li');
    li.textContent = data.message || 'No deductions';
    list.appendChild(li);
  }
}

// ─── Suggestions ───
function renderSuggestions(data) {
  const container = $('suggestions-list');
  container.innerHTML = '';

  if (!data.length) {
    container.innerHTML = '<div class="empty-state">No suggestions yet</div>';
    return;
  }

  data.forEach(s => {
    const div = document.createElement('div');
    div.className = `suggestion-item ${s.priority}`;
    div.innerHTML = `
      <div class="suggestion-priority">${s.priority}</div>
      <div>${s.suggestion}</div>
      ${s.potential_savings ? `<div style="margin-top:4px;color:var(--accent-green);font-size:12px">Potential savings: ${s.potential_savings}</div>` : ''}
    `;
    container.appendChild(div);
  });
}

// ─── Budget ───
function renderBudget(data) {
  const grid = $('budget-grid');
  grid.innerHTML = '';

  ['daily', 'weekly', 'monthly'].forEach(period => {
    const d = data[period];
    if (!d) return;
    const pct = Math.min(d.ratio * 100, 100);

    const card = document.createElement('div');
    card.className = 'budget-card';
    card.innerHTML = `
      <h3>${period}</h3>
      <div style="font-size:28px;font-weight:700;font-variant-numeric:tabular-nums">
        ${fmt(d.spent)} <span style="font-size:16px;color:var(--text-muted)">/ ${fmt(d.limit)}</span>
      </div>
      <div class="budget-bar-track">
        <div class="budget-bar-fill ${d.status}" style="width:${pct}%"></div>
      </div>
      <div class="budget-stats">
        <span>${d.percent} ${t('budget_used')}</span>
        <span>${fmt(d.remaining)} ${t('budget_remaining')}</span>
      </div>
      <span class="budget-status ${d.status}">${d.status.replace('_', ' ')}</span>
      <div style="margin-top:8px;font-size:12px;color:var(--text-muted)">${d.calls} API calls</div>
    `;
    grid.appendChild(card);
  });

  if (data.circuit_broken) {
    const warning = document.createElement('div');
    warning.className = 'anomaly-card high';
    warning.style.gridColumn = '1 / -1';
    warning.innerHTML = `
      <div class="anomaly-icon">🚨</div>
      <div class="anomaly-body">
        <div class="anomaly-type">CIRCUIT BREAKER ACTIVE</div>
        <div class="anomaly-message">All API calls are blocked. Budget exceeded 150%. Reset the circuit breaker to resume.</div>
      </div>
    `;
    grid.appendChild(warning);
  }
}

// ─── Model Values ───
function renderModelValues(data) {
  const tbody = $('model-value-table').querySelector('tbody');
  tbody.innerHTML = '';

  data.forEach(m => {
    const barColor = m.value_score >= 70 ? COLORS.green : m.value_score >= 40 ? COLORS.orange : COLORS.red;
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${m.model}</strong></td>
      <td><span class="tier-badge ${m.tier}">${m.tier}</span></td>
      <td>
        <span class="value-bar"><span class="value-bar-fill" style="width:${m.value_score}%;background:${barColor}"></span></span>
        ${m.value_score}
      </td>
      <td><span class="grade-badge ${m.grade}">${m.grade}</span></td>
      <td>${fmtSmall(m.cost_per_1k_tokens)}</td>
      <td>${fmtSmall(m.total_spent)}</td>
      <td>${m.calls}</td>
      <td style="font-size:12px;max-width:200px">${m.recommendation || '—'}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ─── Projects ───
function renderProjects(data) {
  // Chart
  const ctx = $('project-chart').getContext('2d');
  if (projectChart) projectChart.destroy();

  const cc2 = getChartColors();
  projectChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.map(d => d.project),
      datasets: [{
        label: currentLang === 'zh' ? '成本 ($)' : 'Cost ($)',
        data: data.map(d => d.cost),
        backgroundColor: PALETTE.slice(0, data.length).map(c => c + '99'),
        borderColor: PALETTE.slice(0, data.length),
        borderWidth: 1,
        borderRadius: 6,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => ` $${ctx.parsed.x.toFixed(4)}` } },
      },
      scales: {
        x: {
          grid: { color: cc2.grid },
          ticks: { color: cc2.tick, callback: v => `$${v.toFixed(2)}` },
        },
        y: { grid: { display: false }, ticks: { color: cc2.legend, font: { size: 12 } } },
      },
    },
  });

  $('project-chart').parentElement.style.height = `${Math.max(200, data.length * 50 + 60)}px`;

  // Table
  const tbody = $('project-table').querySelector('tbody');
  tbody.innerHTML = '';
  data.forEach(p => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${p.project}</strong></td>
      <td>${fmtSmall(p.cost)}</td>
      <td>${p.tokens.toLocaleString()}</td>
      <td>${p.calls}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ─── Anomalies ───
function renderAnomalies(data) {
  const container = $('anomalies-list');
  container.innerHTML = '';

  data.forEach(a => {
    const severity = a.severity || 'info';
    const icons = { high: '🚨', medium: '⚠️', info: 'ℹ️' };

    const card = document.createElement('div');
    card.className = `anomaly-card ${severity}`;
    card.innerHTML = `
      <div class="anomaly-icon">${icons[severity] || '🔍'}</div>
      <div class="anomaly-body">
        <div class="anomaly-type">${a.type.replace(/_/g, ' ')}</div>
        <div class="anomaly-message">${a.message}</div>
        ${a.date ? `<div class="anomaly-meta">Date: ${a.date}</div>` : ''}
        ${a.z_score ? `<div class="anomaly-meta">Z-score: ${a.z_score} · Daily avg: ${fmtSmall(a.daily_average)}</div>` : ''}
      </div>
    `;
    container.appendChild(card);
  });
}

// ─── Activity Table ───
function renderActivity(data) {
  const tbody = $('activity-table').querySelector('tbody');
  tbody.innerHTML = '';

  data.forEach(r => {
    const time = new Date(r.timestamp).toLocaleString('en-US', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    });

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${time}</td>
      <td>${r.model}</td>
      <td>${r.project || '—'}</td>
      <td>${r.module || '—'}</td>
      <td>${r.action || '—'}</td>
      <td>${r.total_tokens.toLocaleString()}</td>
      <td>${fmtSmall(r.cost_usd)}</td>
      <td><span class="tier-badge ${r.tier}">${r.tier}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

// ─── Project Filter ───
function populateProjectFilter(projects) {
  const sel = $('project-filter');
  // Keep first "All Projects" option, remove rest
  while (sel.options.length > 1) sel.remove(1);
  projects.forEach(p => {
    const opt = document.createElement('option');
    opt.value = p.project;
    opt.textContent = `${p.project} (${fmt(p.cost)})`;
    sel.appendChild(opt);
  });
}

$('project-filter').addEventListener('change', async () => {
  const project = $('project-filter').value;
  const q = project ? `?project=${encodeURIComponent(project)}` : '';
  const summary = await api(`/summary${q}`);
  renderSummary(summary, null);
});

// ─── Estimator ───
$('est-btn').addEventListener('click', async () => {
  const model = $('est-model').value;
  const prompt = $('est-prompt').value;
  const tokens = parseInt($('est-tokens').value) || 0;

  const params = new URLSearchParams({ model });
  if (prompt) params.set('prompt', prompt);
  if (tokens > 0) params.set('tokens', tokens);

  const result = await api(`/estimate?${params}`);

  $('est-result').style.display = 'block';
  $('est-r-model').textContent = result.model;
  $('est-r-input').textContent = `~${result.estimated_input_tokens.toLocaleString()}`;
  $('est-r-output').textContent = `~${result.estimated_output_tokens.toLocaleString()}`;
  $('est-r-cost').textContent = fmtSmall(result.estimated_cost);
  $('est-r-remaining').textContent = fmt(result.budget_remaining);

  const altRow = $('est-r-alt-row');
  if (result.cheaper_alternative) {
    altRow.style.display = 'flex';
    const alt = result.cheaper_alternative;
    $('est-r-alt').textContent = `${alt.model} → ${fmtSmall(alt.estimated_cost)} (save ${fmtSmall(alt.savings)})`;
  } else {
    altRow.style.display = 'none';
  }

  // Flash warning if will exceed
  if (result.will_exceed_budget) {
    $('est-r-remaining').style.color = 'var(--accent-red)';
  } else {
    $('est-r-remaining').style.color = '';
  }
});

// ─── Init ───
loadDashboard();
setInterval(loadDashboard, 30000); // Auto-refresh every 30s
