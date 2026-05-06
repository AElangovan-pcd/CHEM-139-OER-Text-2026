import { test } from 'node:test';
import assert from 'node:assert/strict';
import { countSigFigs } from './engine.js';

test('countSigFigs: simple integer', () => {
  const r = countSigFigs('305.20');
  assert.equal(r.count, 5);
  assert.match(r.ruleExplanation, /trailing zero/i);
});

test('countSigFigs: leading zeros excluded', () => {
  assert.equal(countSigFigs('0.0030').count, 2);
});

test('countSigFigs: captive zeros included', () => {
  assert.equal(countSigFigs('4002').count, 4);
});

test('countSigFigs: scientific notation', () => {
  assert.equal(countSigFigs('7.000e6').count, 4);
  assert.equal(countSigFigs('1.20e3').count, 3);
});

test('countSigFigs: ambiguous trailing zeros without decimal', () => {
  const r = countSigFigs('600');
  assert.equal(r.ambiguous, true);
  assert.match(r.ruleExplanation, /ambiguous/i);
});

test('countSigFigs: 100. with decimal point', () => {
  assert.equal(countSigFigs('100.').count, 3);
});

test('countSigFigs: 0.020080', () => {
  assert.equal(countSigFigs('0.020080').count, 5);
});

test('countSigFigs: pure zero with decimal point', () => {
  assert.equal(countSigFigs('0.0').count, 1);
  assert.equal(countSigFigs('0.').count, 1);
});

import { formatWithSigFigs } from './engine.js';

test('formatWithSigFigs: round to 3 sig figs', () => {
  assert.equal(formatWithSigFigs(12.3456, 3), '12.3');
  assert.equal(formatWithSigFigs(0.012345, 3), '0.0123');
  assert.equal(formatWithSigFigs(123456, 3), '123000');
});

test('formatWithSigFigs: preserves trailing zeros', () => {
  assert.equal(formatWithSigFigs(2.5, 3), '2.50');
  assert.equal(formatWithSigFigs(40.7, 4), '40.70');
});

test('formatWithSigFigs: handles negative', () => {
  assert.equal(formatWithSigFigs(-12.34, 3), '-12.3');
});

test('formatWithSigFigs: integer with N=2 from N=4', () => {
  assert.equal(formatWithSigFigs(1234, 2), '1200');
});
