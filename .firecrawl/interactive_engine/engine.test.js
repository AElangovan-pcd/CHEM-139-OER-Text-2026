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

test('formatWithSigFigs: cross-decade rounding', () => {
  assert.equal(formatWithSigFigs(0.099999, 1), '0.1');
  assert.equal(formatWithSigFigs(0.9999, 1), '1');
  assert.equal(formatWithSigFigs(9.95, 2), '10');
});

import { decimalToSciNotation } from './engine.js';

test('decimalToSciNotation: positive small', () => {
  const r = decimalToSciNotation(0.00038, 2);
  assert.equal(r.coefficient, '3.8');
  assert.equal(r.exponent, -4);
  assert.equal(r.latex, '3.8 \\times 10^{-4}');
});

test('decimalToSciNotation: large with 3 sig figs', () => {
  const r = decimalToSciNotation(420000, 3);
  assert.equal(r.coefficient, '4.20');
  assert.equal(r.exponent, 5);
});

test('decimalToSciNotation: between 1 and 10', () => {
  const r = decimalToSciNotation(4.56, 3);
  assert.equal(r.coefficient, '4.56');
  assert.equal(r.exponent, 0);
});

test('decimalToSciNotation: cross-decade coefficient overflow', () => {
  const r1 = decimalToSciNotation(9.95, 2);
  assert.equal(r1.coefficient, '1.0');
  assert.equal(r1.exponent, 1);

  const r2 = decimalToSciNotation(0.0099, 1);
  assert.equal(r2.coefficient, '1');
  assert.equal(r2.exponent, -2);

  const r3 = decimalToSciNotation(-9.95, 2);
  assert.equal(r3.coefficient, '-1.0');
  assert.equal(r3.exponent, 1);
});

import { sciNotationToDecimal } from './engine.js';

test('sciNotationToDecimal: positive integer exponent', () => {
  assert.equal(sciNotationToDecimal({ coefficient: '9.20', exponent: 5 }), '920000');
});

test('sciNotationToDecimal: negative exponent', () => {
  assert.equal(sciNotationToDecimal({ coefficient: '4.56', exponent: -5 }), '0.0000456');
});

test('sciNotationToDecimal: small positive exponent preserves trailing zeros', () => {
  assert.equal(sciNotationToDecimal({ coefficient: '4.20', exponent: 2 }), '420');
});
