/* A static evidence walkthrough. Backend classification and review are future work. */
const money = new Intl.NumberFormat('en-US', {style: 'currency', currency: 'USD', maximumFractionDigits: 0});
const dollar = value => value === null ? 'Unknown' : money.format(value / 100);
const percent = value => `${(value * 100).toFixed(1)}%`;
const $ = id => document.getElementById(id);
let sample;
let selected = 'atlas';
const accepted = new Set();
const copy = {
  atlas: {route: 'Commercial investigation', type: '', observation: 'Spend fell 62.5% while the seven-day plan stayed at $3.5M. All required delivery is present. The decline warrants a closer look.', next: 'Ask the account owner to inspect active campaign constraints, budget settings, and delivery context. This observation does not establish a cause or churn risk.'},
  beacon: {route: 'Planned change', type: 'planned', observation: 'The campaign flight ended on August 24. Current spend and the current plan are both zero. The scheduled ending explains the comparison.', next: 'Confirm the agreed flight schedule. Keep this account out of an unexpected-decline queue; an ending alone is not evidence of client loss.'},
  harbor: {route: 'Data investigation', type: 'data', observation: 'One required delivery partition is missing on August 31. The current seven-day total is unknown. Summing the other six dates would conceal incomplete evidence.', next: 'Locate the missing audio delivery file and verify its expected campaign coverage. Reassess the account after the source arrives.'},
  maple: {route: 'Commercial investigation', type: '', observation: 'Complete delivery files explicitly report zero spend across the current week, against a $3.5M plan. This is observed zero, with a 100% spend decline.', next: 'Ask the owner whether campaigns were paused or delivery was constrained while the plan remained active. Confirm context before considering client outreach.'}
};

function summarize(days) {
  return {spend: days.some(day => day.spend_cents === null) ? null : days.reduce((sum, day) => sum + day.spend_cents, 0), plan: days.reduce((sum, day) => sum + day.plan_cents, 0)};
}

function render() {
  const account = sample.accounts.find(account => account.id === selected);
  const days = structuredClone(account.days);
  const key = selected === 'atlas' ? 'correct_atlas' : selected === 'harbor' ? 'late_harbor' : null;
  const applied = accepted.has(key);
  if (applied) {
    const event = sample.events[key];
    const day = days.find(day => day.date === event.date);
    day.spend_cents = event.spend_cents;
    day.state = 'complete';
    day.evidence = day.evidence.map(item => ({...item, delivery_version: event.version, delivery_file_id: null}));
  }
  const prior = summarize(days.slice(0, 7));
  const current = summarize(days.slice(7));
  let detail = {...copy[selected]};
  if (applied && selected === 'atlas') detail.observation = 'A corrected August 31 file raises current spend to $1.30M. The decline is now 53.6%, with the same $3.5M plan. A correction changes the evidence without erasing the prior version.';
  if (applied && selected === 'harbor') detail = {route: 'No decline observed', type: 'planned', observation: 'The late file supplies $400,000 for August 31. Current spend now equals prior spend at $2.80M, with complete coverage. The apparent drop was a data gap.', next: 'Close the data investigation after validating the late file. This sample shows no period spend decline; other commercial questions require separate evidence.'};
  $('account-name').textContent = account.name;
  $('owner').textContent = `Fictional owner: ${account.owner} · Two adjacent seven-day windows`;
  $('route').textContent = detail.route;
  $('route').className = `route ${detail.type}`;
  $('prior-spend').textContent = dollar(prior.spend);
  $('current-spend').textContent = dollar(current.spend);
  $('current-plan').textContent = dollar(current.plan);
  const change = current.spend === null ? null : current.spend - prior.spend;
  $('change').textContent = change === null ? 'Not eligible' : dollar(change);
  $('change-detail').textContent = change === null ? 'Missing expected delivery' : `${change > 0 ? '+' : ''}${percent(change / prior.spend)} versus prior`;
  $('pacing').textContent = current.spend === null ? 'Pacing unknown' : current.plan === 0 ? 'Pacing undefined: no plan' : `${percent(current.spend / current.plan)} pacing`;
  $('observation').textContent = detail.observation;
  $('next-check').textContent = detail.next;
  document.querySelectorAll('[data-account]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.account === selected)));
  const max = Math.max(...days.map(day => Math.max(day.plan_cents, day.spend_cents || 0)), 1);
  $('daily-chart').replaceChildren();
  $('daily-table').replaceChildren();
  for (const [index, day] of days.entries()) {
    const column = document.createElement('div');
    column.className = `day-column ${index >= 7 ? 'current' : ''} ${day.spend_cents === null ? 'missing' : day.spend_cents === 0 && day.plan_cents > 0 ? 'zero' : ''}`;
    column.style.setProperty('--plan', `${day.plan_cents / max * 95}%`);
    column.style.setProperty('--spend', `${(day.spend_cents || 0) / max * 95}%`);
    column.title = `${day.date}: spend ${dollar(day.spend_cents)}, plan ${dollar(day.plan_cents)}; ${day.state}`;
    const plan = document.createElement('i'); plan.className = 'plan-bar';
    const spend = document.createElement('i'); spend.className = 'spend-bar';
    column.append(plan, spend);
    $('daily-chart').append(column);
    const references = [...new Set(day.evidence.map(item => item.delivery_file_id === null ? `${item.partition} v${item.delivery_version || '—'} (${applied && index === 13 ? 'sample event' : 'not received'})` : `file #${item.delivery_file_id} · ${item.partition} v${item.delivery_version}`))].join('; ') || 'No active campaign keys';
    const row = document.createElement('tr');
    for (const value of [day.date, dollar(day.spend_cents), dollar(day.plan_cents), day.state, references]) {
      const cell = document.createElement('td'); cell.textContent = value; row.append(cell);
    }
    $('daily-table').append(row);
  }
  $('daily-chart').setAttribute('aria-label', `${account.name}: daily delivery August 18 to 31. Prior spend ${dollar(prior.spend)}, current spend ${dollar(current.spend)}, current plan ${dollar(current.plan)}. Daily values follow in the source evidence table.`);
  $('event-description').textContent = key ? applied ? 'Sample event accepted. The browser shows updated evidence; your database is unchanged.' : selected === 'atlas' ? 'Source event: a corrected final-day file changes Atlas spend from $150,000 to $400,000.' : 'Source event: a late audio file supplies the missing $400,000 final-day delivery.' : 'Try Atlas or Harbor to explore a source correction or late arrival.';
  $('event-button').hidden = !key || applied;
  $('event-button').textContent = selected === 'atlas' ? 'Accept sample correction' : 'Accept sample late file';
  $('event-button').onclick = () => {accepted.add(key); render();};
  $('reset-button').hidden = !applied;
  $('reset-button').onclick = () => {accepted.delete(key); render();};
  $('source-note').textContent = 'Baseline references identify accepted delivery files from the verified PostgreSQL export. Coverage and budget file references are included in demo.json. Sample events show a source partition and version, not a new database file ID.';
}

async function start() {
  try {
    const response = await fetch('demo.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    sample = await response.json();
    document.querySelectorAll('[data-account]').forEach(button => {button.onclick = () => {selected = button.dataset.account; render();};});
    render();
    $('demo').hidden = false;
    $('load-status').hidden = true;
  } catch (error) {
    $('load-status').textContent = 'The sample could not load. Reload the page or read the four cases in the repository README.';
    console.error('Unable to load verified sample', error);
  }
}
start();
