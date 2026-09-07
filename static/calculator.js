'use strict';
(function (root) {
  const categories = [
    ['rent', 'Wohnen & Betriebskosten', '#9a7de1'],
    ['energy', 'Strom & Heizung', '#e7bd78'],
    ['food', 'Lebensmittel', '#7fc6aa'],
    ['transport', 'Mobilität', '#89afe3'],
    ['phone', 'Internet & Handy', '#b19ad7'],
    ['insurance', 'Versicherungen & Raten', '#e1a4b1'],
    ['other', 'Freizeit & Sonstiges', '#a2adbc'],
  ];
  const toCents = (value) => Math.round(Number(value || 0) * 100);
  function calculate(income, expenses, cut) {
    const incomeCents = toCents(income);
    const totalCents = categories.reduce((sum, [key]) => sum + toCents(expenses[key]), 0);
    const flexibleCents = ['food', 'transport', 'phone', 'other'].reduce((sum, key) => sum + toCents(expenses[key]), 0);
    const savingCents = Math.round(flexibleCents * Number(cut) / 100);
    return { income: incomeCents / 100, total: totalCents / 100,
      remaining: (incomeCents - totalCents) / 100, saving: savingCents / 100,
      annual: savingCents * 12 / 100 };
  }
  const api = { categories, calculate };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.BudgetCalculator = api;
})(globalThis);
