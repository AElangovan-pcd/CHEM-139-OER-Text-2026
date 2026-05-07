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

import { addPreservingDecimalPlaces } from './engine.js';

test('addPreservingDecimalPlaces: textbook example', () => {
  const r = addPreservingDecimalPlaces(['2.45', '12.1', '0.378']);
  assert.equal(r.rawSum, '14.928');
  assert.equal(r.finalSum, '14.9');
  assert.equal(r.limitingDecimalPlaces, 1);
  assert.equal(r.limitingValue, '12.1');
});

test('addPreservingDecimalPlaces: subtraction (negative)', () => {
  const r = addPreservingDecimalPlaces(['8.42', '-6.1']);
  assert.equal(r.finalSum, '2.3');
  assert.equal(r.limitingDecimalPlaces, 1);
  assert.equal(r.limitingValue, '-6.1');
});

test('addPreservingDecimalPlaces: integer + decimal', () => {
  const r = addPreservingDecimalPlaces(['100', '0.5']);
  assert.equal(r.limitingDecimalPlaces, 0);
});

import { multiplyPreservingSigFigs } from './engine.js';

test('multiplyPreservingSigFigs: textbook example', () => {
  const r = multiplyPreservingSigFigs(['7.20', '3.0']);
  // 7.20 × 3.0 = 21.6; limit to 2 sig figs by 3.0 → 22
  assert.equal(r.limitingSigFigs, 2);
  assert.equal(r.limitingValue, '3.0');
});

test('multiplyPreservingSigFigs: three-factor product', () => {
  const r = multiplyPreservingSigFigs(['3.75', '2.0', '4.50']);
  assert.equal(r.limitingSigFigs, 2);
  assert.equal(r.limitingValue, '2.0');
  assert.equal(r.finalProduct, '34');  // 33.75 → 34 with 2 sig figs
});

import { evaluateLinearFunction } from './engine.js';

test('evaluateLinearFunction: textbook example', () => {
  const r = evaluateLinearFunction({ slope: '0.025', intercept: '6.83', x: '50' });
  // 0.025 × 50 + 6.83 = 1.25 + 6.83 = 8.08
  assert.equal(r.y, '8.08');
  assert.match(r.latex, /0\.025/);
  assert.match(r.latex, /6\.83/);
});

test('evaluateLinearFunction: zero intercept', () => {
  const r = evaluateLinearFunction({ slope: '2.0', intercept: '0', x: '5.0' });
  assert.equal(r.y, '10');
});

import { mulberry32, sampleValue } from './engine.js';

test('mulberry32: deterministic with seed', () => {
  const a = mulberry32(42);
  const b = mulberry32(42);
  for (let i = 0; i < 100; i++) {
    assert.equal(a(), b());
  }
});

test('mulberry32: produces values in [0, 1)', () => {
  const rng = mulberry32(123);
  for (let i = 0; i < 1000; i++) {
    const v = rng();
    assert.ok(v >= 0 && v < 1, `value out of range: ${v}`);
  }
});

test('sampleValue: range with decimal_places', () => {
  const rng = mulberry32(7);
  const v = sampleValue({ range: [1.0, 100.0], decimal_places: 2 }, rng);
  assert.match(v, /^\d+\.\d{2}$/);
  const num = parseFloat(v);
  assert.ok(num >= 1.0 && num <= 100.0);
});

test('sampleValue: range with sig_figs (deviation from plan)', () => {
  const rng = mulberry32(7);
  const v = sampleValue({ range: [10, 100], sig_figs: 3 }, rng);
  // 3 sig figs over [10, 100] formats as XX.X most of the time, possibly 100.
  assert.match(v, /^\d+(?:\.\d+)?$/);
  const num = parseFloat(v);
  assert.ok(num >= 10 && num <= 100, `value out of range: ${v}`);
});

import { generateVariant } from './engine.js';

test('generateVariant: subtract operation', () => {
  const spec = {
    id: 'test.subtract',
    variables: {
      a: { range: [5.0, 50.0], decimal_places: 2 },
      b: { range: [1.0, 5.0], decimal_places: 1 },
    },
    answer: { operation: 'subtract', unit: 'm' },
    constraints: { result_must_be_positive: true },
  };
  const rng = mulberry32(123);
  const v = generateVariant(spec, rng);
  assert.ok('a' in v.params);
  assert.ok('b' in v.params);
  assert.ok(parseFloat(v.computed.finalSum) > 0);
});

test('generateVariant: throws on guardrail cap (deviation from plan)', () => {
  // Both vars locked to 1.0; subtract → 0.0; result_range [100,200] never satisfied.
  const impossibleSpec = {
    id: 'test.impossible',
    variables: {
      a: { range: [1.0, 1.0], decimal_places: 1 },
      b: { range: [1.0, 1.0], decimal_places: 1 },
    },
    answer: { operation: 'subtract' },
    constraints: { result_range: [100, 200] },
  };
  const rng = mulberry32(123);
  assert.throws(() => generateVariant(impossibleSpec, rng), /guardrail/i);
});

import { renderLatexForOperation, substituteTemplate } from './engine.js';

test('renderLatexForOperation: subtract', () => {
  const latex = renderLatexForOperation('subtract',
    { params: { a: '8.42', b: '6.1' }, computed: { finalSum: '2.3' } },
    { unit: 'm' }
  );
  assert.match(latex, /8\.42/);
  assert.match(latex, /6\.1/);
  assert.match(latex, /2\.3/);
  assert.match(latex, /\\,\\text\{m\}/);
});

test('substituteTemplate: fills tokens', () => {
  const out = substituteTemplate(
    'Sum is {finalSum}; limited by {limitingValue} ({limitingDecimalPlaces} dp).',
    { finalSum: '14.9', limitingValue: '12.1', limitingDecimalPlaces: 1 }
  );
  assert.equal(out, 'Sum is 14.9; limited by 12.1 (1 dp).');
});

import { factorLabelChain } from './engine.js';

test('factorLabelChain: single-step exact metric', () => {
  // 0.025 g × (1000 mg / 1 g) = 25 mg; sig figs = 2 (limited by 0.025)
  const r = factorLabelChain('0.025', 2, 'g', [
    { num_value: 1000, num_unit: 'mg', den_value: 1, den_unit: 'g', exact: true },
  ]);
  assert.equal(r.finalResult, '25');
  assert.equal(r.finalUnit, 'mg');
  assert.equal(r.limitingSigFigs, 2);
});

test('factorLabelChain: two-step English-metric mixed exact/inexact', () => {
  // 5.00 lb × (453.59 g / 1 lb) × (1 kg / 1000 g) = 2.27 kg; sig figs = 3 (limited by 5.00)
  const r = factorLabelChain('5.00', 3, 'lb', [
    { num_value: 453.59, num_unit: 'g',  den_value: 1, den_unit: 'lb', sig_figs: 5 },
    { num_value: 1,      num_unit: 'kg', den_value: 1000, den_unit: 'g', exact: true },
  ]);
  assert.equal(r.finalResult, '2.27');
  assert.equal(r.finalUnit, 'kg');
  assert.equal(r.limitingSigFigs, 3);
  assert.equal(r.limitingSource, 'value');
});

test('factorLabelChain: limiting sig figs from a non-exact factor', () => {
  // 100. yd × (0.91 m / 1 yd) where 0.91 has 2 sig figs
  const r = factorLabelChain('100.', 3, 'yd', [
    { num_value: 0.91, num_unit: 'm', den_value: 1, den_unit: 'yd', sig_figs: 2 },
  ]);
  assert.equal(r.finalResult, '91');  // limited by the 2-sig-fig factor
  assert.equal(r.limitingSigFigs, 2);
  assert.equal(r.limitingSource, 'step[0]');
});

test('factorLabelChain: density chain (kg → g → mL via density)', () => {
  // 1.50 kg × (1000 g / 1 kg) × (1 mL / 13.546 g) = 110.74... → 111 mL (3 sig figs)
  const r = factorLabelChain('1.50', 3, 'kg', [
    { num_value: 1000, num_unit: 'g',  den_value: 1,      den_unit: 'kg', exact: true },
    { num_value: 1,    num_unit: 'mL', den_value: 13.546, den_unit: 'g',  sig_figs: 5 },
  ]);
  assert.equal(r.finalResult, '111');
  assert.equal(r.finalUnit, 'mL');
  assert.equal(r.limitingSigFigs, 3);
});

test('factorLabelChain: throws on cancellation mismatch at step 0', () => {
  assert.throws(
    () => factorLabelChain('5.00', 3, 'lb', [
      { num_value: 1, num_unit: 'kg', den_value: 1, den_unit: 'oz', exact: true },  // den should be lb
    ]),
    /cancellation mismatch at step 0/i,
  );
});

test('factorLabelChain: throws on cancellation mismatch at step 1', () => {
  assert.throws(
    () => factorLabelChain('5.00', 3, 'lb', [
      { num_value: 453.59, num_unit: 'g',  den_value: 1, den_unit: 'lb', sig_figs: 5 },
      { num_value: 1,      num_unit: 'kg', den_value: 1, den_unit: 'mg', exact: true },  // should be g
    ]),
    /cancellation mismatch at step 1/i,
  );
});

test('factorLabelChain: missing sig_figs on non-exact factor throws', () => {
  assert.throws(
    () => factorLabelChain('5.00', 3, 'lb', [
      { num_value: 453.59, num_unit: 'g', den_value: 1, den_unit: 'lb' },  // neither exact nor sig_figs
    ]),
    /must declare sig_figs or set exact: true/i,
  );
});

test('factorLabelChain: dosage equivalence (mg per kg)', () => {
  // 70.0 kg × (5.00 mg / 1 kg) = 350. mg
  const r = factorLabelChain('70.0', 3, 'kg', [
    { num_value: 5.00, num_unit: 'mg', den_value: 1, den_unit: 'kg', sig_figs: 3 },
  ]);
  assert.equal(r.finalResult, '350');
  assert.equal(r.finalUnit, 'mg');
  assert.equal(r.limitingSigFigs, 3);
});

import { renderFactorLabelLatex } from './engine.js';

test('renderFactorLabelLatex: single-step exact metric', () => {
  const latex = renderFactorLabelLatex(
    '0.025', 'g',
    [{ num_value: 1000, num_unit: 'mg', den_value: 1, den_unit: 'g', exact: true }],
    '25', 'mg'
  );
  // 0.025\,\cancel{\text{g}} \times \frac{1000\,\text{mg}}{1\,\cancel{\text{g}}} = 25\,\text{mg}
  assert.match(latex, /0\.025\\,\\cancel\{\\text\{g\}\}/);
  assert.match(latex, /\\frac\{1000\\,\\text\{mg\}\}\{1\\,\\cancel\{\\text\{g\}\}\}/);
  assert.match(latex, /=\s*25\\,\\text\{mg\}/);
});

test('renderFactorLabelLatex: two-step chain has both \\cancel{} segments', () => {
  const latex = renderFactorLabelLatex(
    '5.00', 'lb',
    [
      { num_value: 453.59, num_unit: 'g',  den_value: 1, den_unit: 'lb', sig_figs: 5 },
      { num_value: 1,      num_unit: 'kg', den_value: 1000, den_unit: 'g', exact: true },
    ],
    '2.27', 'kg'
  );
  assert.match(latex, /5\.00\\,\\cancel\{\\text\{lb\}\}/);
  assert.match(latex, /\\cancel\{\\text\{lb\}\}\}/);  // lb cancellation in step 0 denominator
  assert.match(latex, /\\cancel\{\\text\{g\}\}/);     // g cancellation in step 1 denominator
  assert.match(latex, /=\s*2\.27\\,\\text\{kg\}/);
});

test('renderFactorLabelLatex: unit names with spaces', () => {
  // mass-percent style: g alloy → g Ag
  const latex = renderFactorLabelLatex(
    '50.0', 'g alloy',
    [{ num_value: 35.0, num_unit: 'g Ag', den_value: 100, den_unit: 'g alloy', sig_figs: 3 }],
    '17.5', 'g Ag'
  );
  assert.match(latex, /\\cancel\{\\text\{g alloy\}\}/);  // works with spaces
  assert.match(latex, /\\text\{g Ag\}/);                 // numerator unit
  assert.match(latex, /=\s*17\.5\\,\\text\{g Ag\}/);
});

test('renderFactorLabelLatex: chain has explicit \\times separators between steps', () => {
  const latex = renderFactorLabelLatex(
    '5.00', 'lb',
    [
      { num_value: 453.59, num_unit: 'g',  den_value: 1, den_unit: 'lb', sig_figs: 5 },
      { num_value: 1,      num_unit: 'kg', den_value: 1000, den_unit: 'g', exact: true },
    ],
    '2.27', 'kg'
  );
  // Should be value\,\cancel{\text{...}} \times \frac{...}{...} \times \frac{...}{...} = result\,\text{...}
  const timesMatches = latex.match(/\\times/g) || [];
  assert.equal(timesMatches.length, 2);
});

test('generateVariant: factor_label end-to-end', () => {
  const spec = {
    id: 'test.factor_label',
    variables: {
      mass: { range: [1.0, 10.0], decimal_places: 2 },
    },
    answer: {
      operation: 'factor_label',
      value_param: 'mass',
      input_unit: 'lb',
      chain: [
        { num_value: 453.59, num_unit: 'g',  den_value: 1, den_unit: 'lb', sig_figs: 5 },
        { num_value: 1,      num_unit: 'kg', den_value: 1000, den_unit: 'g', exact: true },
      ],
      target_unit: 'kg',
    },
  };
  const rng = mulberry32(42);
  const v = generateVariant(spec, rng);
  assert.ok('mass' in v.params);
  assert.ok(parseFloat(v.computed.finalResult) > 0);
  assert.equal(v.computed.finalUnit, 'kg');
});

test('renderLatexForOperation: factor_label dispatches correctly', () => {
  const variant = {
    params: { mass: '5.00' },
    computed: {
      rawResult: '2.26795',
      finalResult: '2.27',
      finalUnit: 'kg',
      limitingSigFigs: 3,
    },
  };
  const answerSpec = {
    operation: 'factor_label',
    value_param: 'mass',
    input_unit: 'lb',
    chain: [
      { num_value: 453.59, num_unit: 'g',  den_value: 1, den_unit: 'lb', sig_figs: 5 },
      { num_value: 1,      num_unit: 'kg', den_value: 1000, den_unit: 'g', exact: true },
    ],
  };
  const latex = renderLatexForOperation('factor_label', variant, answerSpec);
  assert.match(latex, /5\.00\\,\\cancel\{\\text\{lb\}\}/);
  assert.match(latex, /=\s*2\.27\\,\\text\{kg\}/);
});

import { formatNumberForLatex } from './engine.js';

test('formatNumberForLatex: positive sci-notation', () => {
  assert.equal(formatNumberForLatex('6.022e+23'), '6.022 \\times 10^{23}');
  assert.equal(formatNumberForLatex('1.0e+22'), '1.0 \\times 10^{22}');
});

test('formatNumberForLatex: negative exponent', () => {
  assert.equal(formatNumberForLatex('3.5e-4'), '3.5 \\times 10^{-4}');
});

test('formatNumberForLatex: plain decimals pass through', () => {
  assert.equal(formatNumberForLatex('5.00'), '5.00');
  assert.equal(formatNumberForLatex('0.025'), '0.025');
  assert.equal(formatNumberForLatex('350'), '350');
});

test('formatNumberForLatex: numeric input is coerced to string', () => {
  assert.equal(formatNumberForLatex(6.022e23), '6.022 \\times 10^{23}');
  assert.equal(formatNumberForLatex(42), '42');
});

test('factorLabelChain: large-magnitude result routes through sci-notation', () => {
  // 0.100 mol × (6.022e+23 molecules / 1 mol) = 6.022e+22 molecules
  // Engineering threshold (>= 1e6) routes through decimalToSciNotation —
  // bypasses formatWithSigFigs's integer-branch IEEE-754 noise.
  const r = factorLabelChain('0.100', 3, 'mol', [
    { num_value: 6.022e+23, num_unit: 'molecules', den_value: 1, den_unit: 'mol', sig_figs: 4 },
  ]);
  assert.equal(r.finalResult, '6.02e+22');
  assert.equal(r.finalResultLatex, '6.02 \\times 10^{22}');
  assert.equal(r.finalUnit, 'molecules');
});

test('factorLabelChain: decimal-magnitude result keeps decimal form', () => {
  // 70.0 kg × (5.00 mg / 1 kg) = 350 mg — well below 1e6, decimal branch.
  const r = factorLabelChain('70.0', 3, 'kg', [
    { num_value: 5.00, num_unit: 'mg', den_value: 1, den_unit: 'kg', sig_figs: 3 },
  ]);
  assert.equal(r.finalResult, '350');
  assert.equal(r.finalResultLatex, '350');
});

test('renderFactorLabelLatex: emits \\times 10^{N} form for sci-notation factors', () => {
  // Avogadro factor: den_value 6.022e+23 must render as "6.022 \times 10^{23}",
  // not as JS-default "6.022e+23" plain text.
  const latex = renderFactorLabelLatex(
    '0.100', 'mol',
    [{ num_value: 6.022e+23, num_unit: 'molecules', den_value: 1, den_unit: 'mol', sig_figs: 4 }],
    '6.02e+22', 'molecules', '6.02 \\times 10^{22}',
  );
  assert.match(latex, /6\.022 \\times 10\^\{23\}/);  // factor's numerator
  assert.match(latex, /6\.02 \\times 10\^\{22\}/);   // final result
  assert.doesNotMatch(latex, /e\+/);                 // no JS sci-notation leakage
});

test('substituteTemplate: tokens inside \\(\\) get latex-formatted', () => {
  const out = substituteTemplate(
    'mass = \\({finalResult}\\) g, count = {limitingSigFigs}',
    { finalResult: '6.02e+22', limitingSigFigs: 3 }
  );
  assert.equal(out, 'mass = \\(6.02 \\times 10^{22}\\) g, count = 3');
});

test('substituteTemplate: plain prose substitution stays raw', () => {
  // No \(...\) wrap → tokens substitute as raw strings (existing behavior).
  const out = substituteTemplate(
    'mass = {finalResult} g',
    { finalResult: '6.02e+22' }
  );
  assert.equal(out, 'mass = 6.02e+22 g');
});

test('substituteTemplate: mixed mathjax and plain regions', () => {
  const out = substituteTemplate(
    'For \\({n_atoms}\\) atoms, sig figs = {sigFigs}',
    { n_atoms: '5.70e+23', sigFigs: 3 }
  );
  assert.equal(out, 'For \\(5.70 \\times 10^{23}\\) atoms, sig figs = 3');
});

test('passesGuardrails: result_range works with factor_label finalResult', () => {
  const spec = {
    id: 'test.factor_label_constrained',
    variables: {
      mass: { range: [1.0, 1.0], decimal_places: 1 },  // always 1.0
    },
    answer: {
      operation: 'factor_label',
      value_param: 'mass',
      input_unit: 'lb',
      chain: [
        { num_value: 1, num_unit: 'kg', den_value: 1, den_unit: 'lb', exact: true },
      ],
      target_unit: 'kg',
    },
    constraints: { result_range: [100, 200] },  // never satisfied (result is 1.0 kg)
  };
  const rng = mulberry32(42);
  assert.throws(() => generateVariant(spec, rng), /guardrail/i);
});

import { computeMassPercent } from './engine.js';

test('computeMassPercent: textbook example NH3 -> 82.27%', () => {
  // 14.01 / 17.03 * 100 = 82.267... -> 2 decimals -> 82.27
  const r = computeMassPercent(
    { partial_mass_param: 'p', total_mass_param: 't', decimal_places: 2 },
    { p: '14.01', t: '17.03' }
  );
  assert.equal(r.finalPercent, '82.27');
  assert.equal(r.finalPercentLatex, '82.27');
  assert.match(r.rawPercent, /^82\.26/);
});

test('computeMassPercent: heavy-element compound at 1 decimal', () => {
  // % Pb in PbO: 207.2 / 223.2 * 100 = 92.83... -> 1 decimal -> 92.8
  const r = computeMassPercent(
    { partial_mass_param: 'p', total_mass_param: 't', decimal_places: 1 },
    { p: '207.2', t: '223.2' }
  );
  assert.equal(r.finalPercent, '92.8');
});

test('computeMassPercent: defaults to 2 decimal places when omitted', () => {
  const r = computeMassPercent(
    { partial_mass_param: 'p', total_mass_param: 't' },
    { p: '12.01', t: '44.01' }
  );
  assert.equal(r.finalPercent, '27.29');
});

test('computeAnswer: mass_percent dispatches via generateVariant', () => {
  const spec = {
    id: 'test.mp',
    variables: {
      p: { range: [14.01, 14.01], decimal_places: 2 },
      t: { range: [17.03, 17.03], decimal_places: 2 },
    },
    answer: {
      operation: 'mass_percent',
      partial_mass_param: 'p',
      total_mass_param: 't',
      element_label_param: 'sym',
      compound_label_param: 'cmp',
      decimal_places: 2,
    },
  };
  // sym/cmp aren't generated as variables here; computeMassPercent only reads
  // partial_mass_param + total_mass_param. Label params are read by the LaTeX
  // renderer, tested separately below.
  const rng = mulberry32(1);
  const v = generateVariant(spec, rng);
  assert.equal(v.computed.finalPercent, '82.27');
});

test('renderLatexForOperation: mass_percent emits proper formula form', () => {
  const variant = {
    params: { p: '14.01', t: '17.03', sym: 'N', cmp: 'NH₃' },
    computed: { finalPercent: '82.27', finalPercentLatex: '82.27' },
  };
  const answerSpec = {
    operation: 'mass_percent',
    partial_mass_param: 'p',
    total_mass_param: 't',
    element_label_param: 'sym',
    compound_label_param: 'cmp',
  };
  const latex = renderLatexForOperation('mass_percent', variant, answerSpec);
  assert.match(latex, /\\dfrac\{14\.01\\,\\text\{g N\}\}/);
  assert.match(latex, /\{17\.03\\,\\text\{g NH₃\}\}/);
  assert.match(latex, /\\times 100\\% = 82\.27\\%/);
});
