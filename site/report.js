/* Presentation only: Python owns eligibility, ranking, and all aggregate values. */
const element = id => document.getElementById(id);
const moneyFormat = new Intl.NumberFormat('en-US', {style:'currency',currency:'USD',minimumFractionDigits:2,maximumFractionDigits:2});
const compactFormat = new Intl.NumberFormat('en-US', {style:'currency',currency:'USD',notation:'compact',maximumFractionDigits:2});
const money = cents => cents === null ? 'Unknown' : moneyFormat.format(cents / 100);
const compact = cents => cents === null ? 'Unknown' : compactFormat.format(cents / 100);
const pct = ratio => `${(ratio * 100).toFixed(1)}%`;
const dateLabel = iso => new Date(`${iso}T12:00:00`).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});
const names = {commercial_investigation:'Unexpected declines',planned_change:'Planned endings',no_decline_signal:'Other complete accounts',plan_context:'Changed plan context',no_baseline:'No prior spend baseline'};

function node(tag, text, className) {
  const result = document.createElement(tag);
  if (text !== undefined) result.textContent = text;
  if (className) result.className = className;
  return result;
}

function evidence(account) {
  const details = node('details', undefined, 'account-evidence');
  details.append(node('summary','Inspect the comparison and evidence'));
  details.append(node('p',`Prior spend ${money(account.prior.spend_cents)} against plan ${money(account.prior.plan_cents)}; current spend ${money(account.current.spend_cents)} against plan ${money(account.current.plan_cents)}. ${account.missing_dates.length ? `Missing delivery dates: ${account.missing_dates.join(', ')}.` : 'Both windows have complete required delivery.'}`));
  const wrapper = node('div',undefined,'table-scroll');
  const table = node('table');
  table.append(node('caption',`${account.name}: accepted source references`,'sr-only'));
  const head = node('thead'); const header = node('tr');
  for (const text of ['Date','Partition','Delivery','Budget / coverage']) {const cell=node('th',text);cell.scope='col';header.append(cell);}
  head.append(header);table.append(head);
  const body = node('tbody');
  for (const ref of account.evidence) {
    const row = node('tr');
    for (const text of [ref.date,ref.partition,ref.delivery_file_id === null ? 'Not received' : `#${ref.delivery_file_id} · v${ref.delivery_version}`,`#${ref.budget_file_id} / #${ref.coverage_file_id}`]) row.append(node('td',text));
    body.append(row);
  }
  table.append(body);wrapper.append(table);details.append(wrapper);
  return details;
}

function priority(account, rank) {
  const card = node('article',undefined,'priority-card');
  const top = node('div',undefined,'priority-top');
  const title = node('div');title.append(node('span',`PRIORITY ${String(rank).padStart(2,'0')}`,'priority-rank'),node('h3',account.name),node('p',`Owner: ${account.owner} · Complete evidence`));
  const loss = node('div',undefined,'priority-loss');loss.append(node('strong',compact(account.change_cents)),node('span',`${pct(account.change_cents / account.prior.spend_cents)} versus prior`));
  top.append(title,loss);card.append(top);
  const values = node('div',undefined,'priority-values');
  for (const [label,value] of [['Prior spend',account.prior.spend_cents],['Current spend',account.current.spend_cents],['Current plan',account.current.plan_cents]]) {const item=node('div');item.append(node('small',label),node('strong',compact(value)));values.append(item);}
  card.append(values);
  card.append(node('p',`Current plan is ${pct(account.current.plan_cents / account.prior.plan_cents)} of prior; pacing fell from ${pct(account.prior.spend_cents / account.prior.plan_cents)} to ${pct(account.current.spend_cents / account.current.plan_cents)}. ${account.current.spend_cents === 0 ? 'Complete delivery explicitly reports zero.' : 'Delivery is lower despite a stable plan.'}`,'priority-explanation'));
  const next=node('div',undefined,'next-check-box');next.append(node('span','NEXT CHECK','small-label'),node('p',account.next_check));card.append(next,evidence(account));
  return card;
}

function render(report, url) {
  const s=report.summary, p=report.periods;
  element('period-label').textContent=`${dateLabel(p.current_start)}–${dateLabel(p.current_end)} vs ${dateLabel(p.prior_start)}–${dateLabel(p.prior_end)}`;
  element('takeaway-title').textContent=s.candidate_count ? `${s.candidate_count} account${s.candidate_count === 1 ? '' : 's'} warrant an owner review.` : 'No accounts meet the unexpected-decline rule.';
  element('takeaway-copy').textContent=`Comparable spend ${s.change_cents < 0 ? 'fell' : 'rose'} ${pct(Math.abs(s.change_cents) / (s.prior_spend_cents || 1))} (${compact(Math.abs(s.change_cents))}). ${compact(s.candidate_decline_cents)} of observed decline sits in accounts meeting the review rule; ${compact(Math.abs(s.planned_change_cents))} of movement sits in ${s.planned_count} planned ending${s.planned_count === 1 ? '' : 's'}. ${s.excluded_accounts} account${s.excluded_accounts === 1 ? ' is' : 's are'} excluded because delivery is incomplete.`;
  element('portfolio-spend').textContent=compact(s.current_spend_cents);
  element('portfolio-change').textContent=`${compact(s.change_cents)} · ${s.prior_spend_cents ? pct(s.change_cents / s.prior_spend_cents) : 'No prior baseline'} vs prior`;
  element('signal-loss').textContent=compact(s.candidate_decline_cents);
  element('signal-count').textContent=`${s.candidate_count} accounts meet the owner-review rule`;
  element('planned-loss').textContent=compact(s.planned_change_cents);
  element('planned-count').textContent=`${s.planned_count} scheduled ending${s.planned_count === 1 ? '' : 's'}`;
  element('coverage').textContent=pct(s.comparable_accounts / s.total_accounts);
  element('coverage-count').textContent=`${s.comparable_accounts.toLocaleString()} of ${s.total_accounts.toLocaleString()} accounts comparable`;
  element('cohort-note').textContent=`The same ${s.comparable_accounts.toLocaleString()} complete accounts appear in both periods. ${s.excluded_accounts} incomplete account${s.excluded_accounts === 1 ? ' is' : 's are'} excluded from both.`;
  const max=Math.max(...report.daily.flatMap(day=>[day.prior_spend_cents,day.current_spend_cents]),1);
  for (const day of report.daily) {
    const row=node('div',undefined,'trend-row');
    row.append(node('span',new Date(`${day.current_date}T12:00:00`).toLocaleDateString('en-US',{weekday:'short'})));
    const pair=node('div',undefined,'trend-pair');
    for (const [period,amount,dayDate] of [['prior',day.prior_spend_cents,day.prior_date],['current',day.current_spend_cents,day.current_date]]) {
      const series=node('div',undefined,`trend-series ${period}`), bar=node('i',undefined,'trend-bar');
      bar.style.setProperty('--width',`${amount / max * 72}%`);
      series.setAttribute('aria-label',`${dateLabel(dayDate)}: ${money(amount)}`);
      series.append(bar,node('span',compact(amount)));pair.append(series);
    }
    row.append(pair);element('portfolio-trend').append(row);
  }
  for (const cohort of report.cohorts) {
    const row=node('div',undefined,'bridge-row');const label=node('div');
    label.append(node('span',names[cohort.route] || cohort.route),node('small',`${cohort.accounts.toLocaleString()} account${cohort.accounts === 1 ? '' : 's'}`));
    row.append(label,node('strong',compact(cohort.change_cents)));element('movement-bridge').append(row);
  }
  const total=node('div',undefined,'bridge-row bridge-total');total.append(node('span','Net portfolio change'),node('strong',money(s.change_cents)));element('movement-bridge').append(total);
  element('queue-note').textContent=`${s.queued_count} of ${s.candidate_count} eligible accounts shown, ranked by observed dollar decline. Capacity: ${report.capacity}. ${s.deferred_count ? `${s.deferred_count} deferred for the next review.` : 'No eligible accounts deferred.'}`;
  report.queue.forEach((account,index)=>element('priority-cards').append(priority(account,index+1)));
  if (!report.queue.length) element('priority-cards').append(node('p','No complete accounts meet the current review rule.'));
  element('data-title').textContent=s.excluded_accounts ? 'Resolve the evidence gap first.' : 'All accounts have complete delivery.';
  element('data-copy').textContent=`Excluded accounts have ${compact(s.excluded_prior_known_cents)} known prior spend and ${compact(s.excluded_current_known_cents)} known current spend. These partial amounts are outside the portfolio comparison; incomplete period totals remain unknown.`;
  for (const account of report.data_issues) {
    const item=node('div',undefined,'context-account');item.append(node('h4',`${account.name} · ${account.owner}`),node('p',`Current period: ${money(account.current.spend_cents)}. Missing dates: ${account.missing_dates.join(', ')}.`),node('p',account.next_check),evidence(account));element('data-issues').append(item);
  }
  for (const account of report.planned_changes) {
    const item=node('div',undefined,'context-account');item.append(node('h4',`${account.name} · ${account.owner}`),node('p',`Spend ${compact(account.prior.spend_cents)} → ${compact(account.current.spend_cents)}. Current plan ${compact(account.current.plan_cents)}.`),node('p',account.next_check),evidence(account));element('planned-accounts').append(item);
  }
  if (!report.planned_changes.length) element('planned-accounts').append(node('p','No scheduled endings in this comparison.'));
  element('data-end').textContent=dateLabel(p.current_end);
  element('snapshot-note').textContent=`Snapshot ${report.snapshot_id} · Rule ${report.rule_version}. Source references identify accepted account, budget, coverage, and delivery versions from PostgreSQL. CSV and website use the same comparison output. The report has no live review or scheduling backend.`;
  element('snapshot-link').href=url;
  element('download-csv').href=url.replace('report.json','accounts.csv');element('download-csv').hidden=false;
}

element('print-report').onclick=()=>window.print();
async function start() {
  try {
    const pointerResponse=await fetch('reports/latest.json');
    if (!pointerResponse.ok) throw new Error('Report pointer unavailable');
    const pointer=await pointerResponse.json();
    if (!/^[a-f0-9]{16}$/.test(pointer.snapshot_id)) throw new Error('Invalid snapshot identifier');
    const url=`reports/${pointer.snapshot_id}/report.json`, response=await fetch(url);
    if (!response.ok) throw new Error('Report snapshot unavailable');
    const report=await response.json();
    if (report.snapshot_id !== pointer.snapshot_id) throw new Error('Snapshot mismatch');
    render(report,url);element('briefing').hidden=false;element('report-loading').hidden=true;
  } catch(error) {
    element('report-loading').textContent='The briefing could not load. Reload this page or read the account cases in the repository.';
    console.error('Unable to load executive briefing',error);
  }
}
start();
