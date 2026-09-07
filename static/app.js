'use strict';
(() => {
  const $ = (id) => document.getElementById(id);
  const form = $('budget-form');
  if (!form) return;
  const { categories, calculate } = BudgetCalculator;
  const fields = ['income', ...categories.map(([key]) => key), 'cut'];
  const euro = new Intl.NumberFormat('de-AT', { style: 'currency', currency: 'EUR', minimumFractionDigits: 2 });
  const format = (value) => euro.format(value);
  const values = () => Object.fromEntries(fields.map((key) => [key, $(key).value]));
  const initial = JSON.stringify(values());
  let leaving = false;
  const dirty = () => JSON.stringify(values()) !== initial;
  const dialog = $('confirm-dialog');
  let action = null;
  function confirmAction(title, text, callback) {
    $('confirm-title').textContent = title;
    $('confirm-text').textContent = text;
    action = callback;
    dialog.showModal();
  }
  $('confirm-cancel').addEventListener('click', () => { action = null; dialog.close(); });
  $('confirm-ok').addEventListener('click', () => {
    const callback = action;
    action = null;
    dialog.close();
    if (callback) callback();
  });
  dialog.addEventListener('cancel', () => { action = null; });

  function render() {
    const data = values();
    if (fields.some((key) => !$(key).validity.valid)) {
      $('save-status').textContent = 'Bitte prüfe deine Eingaben: 0 bis 1.000.000 €, maximal zwei Nachkommastellen.';
      ['income-summary', 'total', 'remaining', 'daily', 'saving', 'annual'].forEach((key) => { $(key).textContent = '—'; });
      return;
    }
    const result = calculate(data.income, data, data.cut);
    $('income-summary').textContent = format(result.income);
    $('total').textContent = format(result.total);
    $('remaining').textContent = format(result.remaining);
    $('remaining').closest('.metric').classList.toggle('is-negative', result.remaining < 0);
    $('result-note').textContent = result.remaining < 0 ? 'Deine Ausgaben sind höher als dein Einkommen.' : 'Nach deinen geplanten Ausgaben';
    $('ratio-caption').textContent = result.income > 0 ? `${Math.round(result.total / result.income * 100)} % deines Einkommens` : 'Über alle sieben Kategorien';
    $('expense-legend').textContent = format(result.total);
    $('free-legend').textContent = format(result.remaining);
    $('free-ratio').textContent = result.income ? `${Math.round(result.remaining / result.income * 100)} %` : '—';
    $('daily').textContent = result.income > 0 && result.remaining >= 0 ? format(result.remaining / 30) : '—';
    $('cut-label').textContent = `${data.cut} %`;
    $('saving').textContent = '+' + format(result.saving);
    $('annual').textContent = '+' + format(result.annual);
    const total = Math.max(result.income, result.total);
    const slices = categories.map(([key, , color]) => ({ amount: Number(data[key] || 0), color }));
    slices.push({ amount: Math.max(0, result.remaining), color: '#bbebdd' });
    const group = $('donut-segments');
    group.replaceChildren();
    let offset = 0;
    const circumference = 2 * Math.PI * 80;
    slices.forEach(({ amount, color }) => {
      if (!total || amount <= 0) return;
      const length = amount / total * circumference;
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      Object.entries({ cx: 100, cy: 100, r: 80, fill: 'none', stroke: color, 'stroke-width': 19,
        'stroke-dasharray': `${Math.max(0, length - 1.2)} ${circumference}`, 'stroke-dashoffset': -offset,
      }).forEach(([key, value]) => circle.setAttribute(key, value));
      group.appendChild(circle);
      offset += length;
    });
    const largest = categories.reduce((a, b) => Number(data[b[0]] || 0) > Number(data[a[0]] || 0) ? b : a, categories[0]);
    $('largest-title').textContent = result.total ? largest[1] : 'Dein größter Kostenblock';
    $('largest-note').textContent = result.total ? `${format(Number(data[largest[0]] || 0))} — ${Math.round(Number(data[largest[0]] || 0) / result.total * 100)} % deiner Ausgaben. Hier lohnt sich ein genauer Blick.` : 'Trag deine Ausgaben ein, um ihre Verteilung zu sehen.';
    $('future-title').textContent = result.saving ? `Mit deinem Sparplan: ${format(result.remaining + result.saving)}` : 'Dein möglicher Spielraum';
    $('future-note').textContent = result.saving ? 'So viel bliebe monatlich, wenn du die gewählte Reduktion erreichst.' : 'Mit dem Regler kannst du deinen Sparplan durchrechnen.';
    if (dirty()) $('save-status').textContent = 'Änderungen noch nicht gespeichert.';
    else $('save-status').textContent = initialStatus;
  }
  const initialStatus = $('save-status').textContent;
  form.addEventListener('input', render);
  $('example').addEventListener('click', () => {
    const fill = () => {
      const example = { income: 2400, rent: 850, energy: 110, food: 320, transport: 80, phone: 45, insurance: 120, other: 180, cut: 10 };
      Object.entries(example).forEach(([key, value]) => { $(key).value = value; });
      render();
    };
    if (fields.some((key) => key !== 'cut' && Number($(key).value))) confirmAction('Beispiel laden?', 'Deine aktuellen Eingaben werden ersetzt. Dein gespeichertes Budget bleibt bis zum erneuten Speichern unverändert.', fill);
    else fill();
  });
  $('reset').addEventListener('click', () => confirmAction('Eingaben leeren?', 'Die Eingaben auf dieser Seite werden auf 0 gesetzt. Dein gespeichertes Budget wird dadurch noch nicht geändert.', () => {
    fields.forEach((key) => { $(key).value = key === 'cut' ? 10 : 0; });
    render();
  }));
  window.addEventListener('beforeunload', (event) => {
    if (dirty() && !leaving) { event.preventDefault(); event.returnValue = ''; }
  });
  document.querySelectorAll('a[data-leave], .main-nav a, .month-history a, .brand, .mobile-brand').forEach((link) => {
    link.addEventListener('click', (event) => {
      if (!dirty() || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      confirmAction('Änderungen nicht gespeichert', 'Beim Verlassen dieser Seite gehen deine aktuellen Änderungen verloren. Trotzdem fortfahren?', () => { leaving = true; window.location.assign(link.href); });
    });
  });
  document.querySelectorAll('form[data-leave-form], .account-actions form').forEach((navigationForm) => {
    navigationForm.addEventListener('submit', (event) => {
      if (!dirty()) return;
      event.preventDefault();
      confirmAction('Seite verlassen?', 'Deine letzten Änderungen wurden noch nicht gespeichert.', () => { leaving = true; navigationForm.submit(); });
    });
  });
  form.addEventListener('submit', () => {
    leaving = true;
    const button = form.querySelector('button[type="submit"]');
    if (button) { button.disabled = true; button.textContent = 'Wird gespeichert …'; }
  });
  window.addEventListener('pageshow', () => {
    leaving = false;
    const button = form.querySelector('button[type="submit"]');
    if (button) { button.disabled = false; button.textContent = 'Budget speichern ↗'; }
  });
  render();
})();
