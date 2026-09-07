const { test } = require('node:test');
const assert = require('node:assert/strict');
const { calculate } = require('../static/calculator.js');
test('sample budget and annual savings', () => {
  assert.deepEqual(calculate(2400, {rent:850,energy:110,food:320,transport:80,phone:45,insurance:120,other:180},10),
    {income:2400,total:1705,remaining:695,saving:62.5,annual:750});
});
test('cents are exact and halfway savings round up', () => {
  const result = calculate('0.30', {food:'0.10',other:'0.20'},5);
  assert.equal(result.remaining,0);
  assert.equal(result.saving,0.02);
  assert.equal(result.annual,0.24);
});
test('empty budget, zero reduction and deficit', () => {
  assert.equal(calculate('',{},0).total,0);
  assert.equal(calculate(100,{rent:150},0).remaining,-50);
  assert.equal(calculate(2000,{food:100},0).saving,0);
});
test('maximum values and 50 percent reduction stay within safe precision', () => {
  const result=calculate(1000000,{food:1000000,other:1000000,phone:1000000,transport:1000000},50);
  assert.equal(result.remaining,-3000000);
  assert.equal(result.saving,2000000);
});
