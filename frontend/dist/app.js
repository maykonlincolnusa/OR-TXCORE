const API = new URLSearchParams(location.search).get('api') || 'http://127.0.0.1:8000';
const services = ['payment-core', 'fraudshield-ml', 'outbox-worker', 'NATS JetStream', 'audit-service'];
const seed = [
  ['pay_01J4…C9A2', 'Conta • 1d8f → 93ae', 'POSTED', 'ALLOW', 'R$ 1.248,00', 'payment.posted'],
  ['pay_01J4…A73E', 'Conta • c822 → 1fab', 'POSTED', 'ALLOW', 'R$ 89,40', 'payment.posted'],
  ['pay_01J4…FF12', 'Conta • 5b30 → b4c1', 'REVIEW', 'SCORE 62', 'R$ 8.900,00', 'payment.risk_assessed'],
  ['pay_01J4…91BD', 'Conta • e11a → 12de', 'POSTED', 'ALLOW', 'R$ 320,00', 'payment.posted'],
  ['pay_01J4…D6F1', 'Conta • 6d0e → 77a9', 'DENY', 'SCORE 94', 'R$ 15.000,00', 'payment.rejected']
];
const explanations = {
  volume: 'Volume liquidado soma somente pagamentos POSTED. REVIEW, DENY e FAILED não movem saldo.',
  authorized: 'POSTED significa que as duas contas foram bloqueadas, saldo validado e journal balanceado foi gravado.',
  review: 'REVIEW não debita nem credita. O próximo passo é a decisão do operador/case management.',
  locks: 'É o tempo de espera pelo SELECT FOR UPDATE das contas. Locks evitam double spending; otimize consultas e contenção, não remova a proteção.'
};
const list = document.querySelector('#transactions');
const template = document.querySelector('#row');
let paused = false, connected = false, selected = seed[0];
function toast(text) { const el = document.querySelector('#toast'); el.textContent = text; el.classList.add('show'); setTimeout(() => el.classList.remove('show'), 3400); }
function sourceLabel() { return connected ? 'API LOCAL / AO VIVO' : 'MODO DEMONSTRATIVO'; }
function renderTrace(item = selected) {
  const stages = item[2] === 'POSTED' ? [['payment.requested', 'Recebido com chave de idempotência'], ['payment.risk_assessed', `FraudShield: ${item[3]}`], ['ledger.journal_posted', 'Débito e crédito balanceados'], ['payment.posted', 'Outbox pronto para publicar']] : [['payment.requested', 'Recebido com chave de idempotência'], ['payment.risk_assessed', `FraudShield: ${item[3]}`], [item[5], item[2] === 'REVIEW' ? 'Aguardando decisão; nenhum saldo mudou' : 'Rejeitado; nenhum saldo mudou']];
  document.querySelector('#eventTrace').innerHTML = stages.map(([event, text], i) => `<li><b>${String(i + 1).padStart(2, '0')}</b><div><strong>${event}</strong><span>${text}</span></div><em>${connected ? 'registrado' : 'amostra'}</em></li>`).join('');
  document.querySelector('#traceMode').textContent = connected ? 'API' : 'AMOSTRA';
}
function showDetail(item) {
  selected = item; renderTrace(item); document.querySelector('#detailTitle').textContent = item[0];
  document.querySelector('#detailContent').innerHTML = `<dl><dt>Estado</dt><dd>${item[2]}</dd><dt>Decisão de risco</dt><dd>${item[3]}</dd><dt>Valor</dt><dd>${item[4]}</dd><dt>Garantia</dt><dd>${item[2] === 'POSTED' ? 'Ledger com débito/crédito e outbox na mesma transação.' : 'Nenhuma movimentação de saldo foi confirmada.'}</dd><dt>Próxima ação</dt><dd>${item[2] === 'REVIEW' ? 'Decidir o caso antes de qualquer posting.' : 'Consultar a trilha de eventos pelo correlation_id.'}</dd></dl>`;
  document.querySelector('#detailDialog').showModal();
}
function addTransaction(item, prepend = false) {
  const node = template.content.cloneNode(true); node.querySelector('strong').textContent = item[0]; node.querySelector('small').textContent = item[1]; node.querySelector('.status').textContent = item[2]; node.querySelector('.risk').textContent = item[3]; node.querySelector('.amount').textContent = item[4];
  const row = node.querySelector('.transaction'); row.tabIndex = 0; row.setAttribute('role', 'button'); row.setAttribute('aria-label', `Detalhes de ${item[0]}`);
  if (item[2] === 'REVIEW') row.querySelector('.status').style.color = 'var(--amber)'; if (item[2] === 'DENY') row.querySelector('.status').style.color = '#ff8a87';
  row.onclick = () => showDetail(item); row.onkeydown = e => { if (e.key === 'Enter') showDetail(item); }; prepend ? list.prepend(node) : list.append(node);
}
function renderSeed() { list.innerHTML = ''; seed.forEach(item => addTransaction(item)); renderTrace(); }
function renderServices() { document.querySelector('#serviceList').innerHTML = services.map((name, i) => `<div class="service"><span>${String(i + 1).padStart(2, '0')} · ${name}</span><b>${name === 'payment-core' ? (connected ? 'ONLINE' : 'OFFLINE') : 'DEPENDENCY'}</b></div>`).join(''); document.querySelector('#serviceSummary').textContent = connected ? 'API conectada' : 'amostra local'; }
async function checkApi() {
  try {
    const response = await fetch(`${API}/v1/operations/overview`, { signal: AbortSignal.timeout(1200) });
    if (!response.ok) throw new Error('overview unavailable');
    const overview = await response.json(); connected = true;
    document.querySelector('#authorized').textContent = Number(overview.posted_count).toLocaleString('pt-BR');
    document.querySelector('#review').textContent = String(overview.review_count).padStart(2, '0');
    document.querySelector('#volume').textContent = (Number(overview.posted_volume_minor) / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    document.querySelector('#locks').nextElementSibling.innerHTML = `API · ${overview.outbox_pending} evento(s) pendente(s) no outbox`;
    document.querySelector('#controlsSource').textContent = 'API / DADOS REAIS';
    document.querySelector('#reconciliationStatus').textContent = `${overview.journal_count} journals postados`;
    document.querySelector('#outboxControl').textContent = `${overview.outbox_pending} evento(s)`;
    document.querySelector('#reviewControl').textContent = `${String(overview.review_count).padStart(2, '0')} em fila`;
    document.querySelector('#exceptionsControl').textContent = `${String(overview.review_count).padStart(2, '0')} REVIEW`;
    document.querySelector('#volumeControl').textContent = (Number(overview.posted_volume_minor) / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    document.querySelector('#ledgerBalance').textContent = `${overview.journal_count} journal(s)`;
    document.querySelector('#auditCount').textContent = `${overview.audit_count} registros`;
    document.querySelector('#eventControl').textContent = `${overview.audit_count} no core`;
    if (overview.recent_payments.length) {
      list.innerHTML = '';
      overview.recent_payments.forEach(payment => addTransaction([payment.id.slice(0, 13), 'Conta protegida → beneficiário', payment.status, payment.risk_decision, (payment.amount_minor / 100).toLocaleString('pt-BR', { style: 'currency', currency: payment.currency }), payment.status === 'POSTED' ? 'payment.posted' : 'payment.risk_assessed']));
      renderTrace();
    }
  } catch { connected = false; }
  document.querySelector('#environment').innerHTML = `<i></i>${sourceLabel()}`; document.querySelector('#environment').classList.toggle('offline', !connected); renderServices();
}
function clock() { document.querySelector('#clock').textContent = new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit', timeZoneName: 'short' }).format(new Date()); }
document.querySelectorAll('[data-explain]').forEach(button => button.onclick = () => toast(explanations[button.dataset.explain]));
document.querySelector('#pause').onclick = e => { paused = !paused; e.target.textContent = paused ? 'Retomar fluxo' : 'Pausar fluxo'; toast(paused ? 'A visualização foi pausada; os serviços não foram alterados.' : 'A visualização foi retomada.'); };
document.querySelector('#simulate').onclick = () => { if (paused) return toast('Retome o fluxo visual para inserir uma simulação.'); const amount = (Math.random() * 4000 + 20).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }); const id = `pay_01J4…${Math.random().toString(16).slice(2, 6).toUpperCase()}`; const item = [id, 'Conta sintética → beneficiário', 'POSTED', 'ALLOW', amount, 'payment.posted']; addTransaction(item, true); showDetail(item); const count = document.querySelector('#authorized'); count.textContent = (Number(count.textContent.replace('.', '')) + 1).toLocaleString('pt-BR'); };
document.querySelector('#refresh').onclick = () => checkApi().then(() => toast(connected ? 'Saúde da API atualizada.' : 'API indisponível; permanecendo em modo demonstrativo.'));
document.querySelector('#closeDialog').onclick = () => document.querySelector('#detailDialog').close();
clock(); setInterval(clock, 1000); renderSeed(); checkApi();
