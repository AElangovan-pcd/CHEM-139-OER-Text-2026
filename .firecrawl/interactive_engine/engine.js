// engine.js — variable-problem pilot engine
// ES module. Runs in modern browsers and Node 20+.

/**
 * Count significant figures in a numeric string.
 * Returns { count, ruleExplanation, ambiguous? }.
 */
export function countSigFigs(s) {
  const trimmed = String(s).trim();

  // Scientific notation: 7.000e6 — count digits in coefficient.
  const sciMatch = trimmed.match(/^([+-]?\d+(?:\.\d+)?)[eE]([+-]?\d+)$/);
  if (sciMatch) {
    const coeff = sciMatch[1].replace(/^[+-]/, '');
    const digits = coeff.replace('.', '');
    // Leading zeros in the coefficient still don't count
    const significant = digits.replace(/^0+/, '') || '0';
    return {
      count: significant.length,
      ruleExplanation: 'Scientific notation: all digits in the coefficient are significant.',
    };
  }

  const negStripped = trimmed.replace(/^[+-]/, '');
  const hasDecimal = negStripped.includes('.');

  if (!hasDecimal) {
    // No decimal point — trailing zeros ambiguous.
    const stripped = negStripped.replace(/^0+/, '');
    if (stripped === '') return { count: 1, ruleExplanation: 'Zero by itself is one sig fig.' };
    if (/0+$/.test(stripped)) {
      return {
        count: stripped.replace(/0+$/, '').length,
        ambiguous: true,
        ruleExplanation: 'Trailing zeros without a decimal point are ambiguous (1 to ' + stripped.length + ' sig figs). Express as scientific notation to disambiguate.',
      };
    }
    return { count: stripped.length, ruleExplanation: 'All digits are non-zero or captive zeros.' };
  }

  // Has decimal point.
  const [intPart, decPart] = negStripped.split('.');
  const intStripped = intPart.replace(/^0+/, '');
  if (intStripped === '') {
    // 0.xxx — leading zeros in decimal part don't count
    const decStripped = decPart.replace(/^0+/, '');
    if (decStripped === '') {
      // Pure-zero input like '0.0', '0.00', '0.' — treat as 1 sig fig
      // (the explicit decimal point makes the zero significant per Rule 4a).
      return {
        count: 1,
        ruleExplanation: 'Pure zero with explicit decimal point — treated as one significant figure.',
      };
    }
    return {
      count: decStripped.length,
      ruleExplanation: 'Leading zeros do not count; remaining digits (including trailing zeros after the decimal point) all count.',
    };
  }
  // Has integer part — all digits after the leading zeros count, including trailing.
  return {
    count: (intStripped + decPart).length,
    ruleExplanation: 'Captive zeros count; trailing zeros after the decimal point count.',
  };
}

/**
 * Format a number to exactly N significant figures.
 * Preserves trailing zeros (e.g., formatWithSigFigs(2.5, 3) → "2.50").
 * Recomputes magnitude after rounding to handle cross-decade boundaries
 * (e.g., 0.9999 at n=1 rounds to 1, not "1.0").
 */
export function formatWithSigFigs(value, n) {
  if (value === 0) return n === 1 ? '0' : '0.' + '0'.repeat(n - 1);
  const sign = value < 0 ? '-' : '';
  const abs = Math.abs(value);
  const magnitude = Math.floor(Math.log10(abs));
  const factor = Math.pow(10, n - 1 - magnitude);
  const rounded = Math.round(abs * factor) / factor;
  // Recompute magnitude from the rounded value: rounding can push us across
  // a power-of-10 boundary (e.g., 0.9999 → 1.0), invalidating the original.
  const finalMagnitude = Math.floor(Math.log10(rounded));
  const decimals = Math.max(0, n - 1 - finalMagnitude);
  if (decimals === 0) {
    return sign + Math.round(rounded).toString();
  }
  return sign + rounded.toFixed(decimals);
}

/**
 * Convert a decimal value to scientific notation form.
 * Output coefficient is always in [1, 10) (or [-10, -1] for negatives) —
 * if rounding pushes the coefficient across the decade boundary,
 * the exponent is bumped and the coefficient is renormalized.
 *
 * @param {number} value
 * @param {number} sigFigs
 * @returns {{coefficient: string, exponent: number, latex: string}}
 */
export function decimalToSciNotation(value, sigFigs) {
  if (value === 0) return { coefficient: '0', exponent: 0, latex: '0' };
  const sign = value < 0 ? '-' : '';
  const abs = Math.abs(value);
  let exponent = Math.floor(Math.log10(abs));
  const coefficientNum = abs / Math.pow(10, exponent);
  let coefficient = formatWithSigFigs(coefficientNum, sigFigs);
  // Cross-decade guard: rounding may produce a coefficient ≥ 10 (e.g. 9.95→'10' at n=2).
  // Renormalize by bumping the exponent and dividing the coefficient by 10.
  if (parseFloat(coefficient) >= 10) {
    exponent += 1;
    coefficient = formatWithSigFigs(parseFloat(coefficient) / 10, sigFigs);
  }
  const latex = sign + coefficient + ' \\times 10^{' + exponent + '}';
  return { coefficient: sign + coefficient, exponent, latex };
}

/**
 * Convert {coefficient, exponent} back to decimal form.
 * Preserves trailing-zero significance.
 */
export function sciNotationToDecimal({ coefficient, exponent }) {
  const sign = coefficient.startsWith('-') ? '-' : '';
  const absCoeff = coefficient.replace(/^[+-]/, '');
  const [intPart, decPart = ''] = absCoeff.split('.');
  const allDigits = intPart + decPart;
  const decimalPos = intPart.length + exponent;

  if (decimalPos >= allDigits.length) {
    // Pad with zeros on the right
    return sign + allDigits + '0'.repeat(decimalPos - allDigits.length);
  } else if (decimalPos <= 0) {
    // Pad with zeros on the left after "0."
    return sign + '0.' + '0'.repeat(-decimalPos) + allDigits;
  } else {
    return sign + allDigits.slice(0, decimalPos) + '.' + allDigits.slice(decimalPos);
  }
}

/**
 * Add a list of numeric strings; round to least decimal places per sig-fig rule.
 */
export function addPreservingDecimalPlaces(values) {
  const decimalPlacesOf = (s) => {
    const stripped = s.replace(/^[+-]/, '');
    if (!stripped.includes('.')) return 0;
    return stripped.split('.')[1].length;
  };
  const places = values.map(decimalPlacesOf);
  const minPlaces = Math.min(...places);
  const limitingIdx = places.indexOf(minPlaces);
  const limitingValue = values[limitingIdx];
  const sumNum = values.reduce((acc, v) => acc + parseFloat(v), 0);
  const maxPlaces = Math.max(...places);
  const rawSum = sumNum.toFixed(maxPlaces);
  const finalSum = sumNum.toFixed(minPlaces);
  return { rawSum, finalSum, limitingDecimalPlaces: minPlaces, limitingValue };
}

/**
 * Multiply a list of numeric strings; round to fewest sig figs per sig-fig rule.
 */
export function multiplyPreservingSigFigs(values) {
  const sigFigsOf = (s) => countSigFigs(s).count;
  const sigs = values.map(sigFigsOf);
  const minSigs = Math.min(...sigs);
  const limitingIdx = sigs.indexOf(minSigs);
  const limitingValue = values[limitingIdx];
  const product = values.reduce((acc, v) => acc * parseFloat(v), 1);
  const rawProduct = product.toString();
  const finalProduct = formatWithSigFigs(product, minSigs);
  return { rawProduct, finalProduct, limitingSigFigs: minSigs, limitingValue };
}

/**
 * Evaluate y = slope*x + intercept. Format y to the intercept's decimal places —
 * this matches the textbook convention for linear-extrapolation problems where
 * inputs are treated as effectively exact and the answer's precision is anchored
 * to the intercept's measured precision.
 *
 * @param {{slope: string, intercept: string, x: string}} args
 * @returns {{y: string, latex: string}}
 */
export function evaluateLinearFunction({ slope, intercept, x }) {
  const y = parseFloat(slope) * parseFloat(x) + parseFloat(intercept);
  const decimalPlacesOf = (s) => {
    const stripped = s.replace(/^[+-]/, '');
    if (!stripped.includes('.')) return 0;
    return stripped.split('.')[1].length;
  };
  const decimals = decimalPlacesOf(intercept);
  const yFormatted = y.toFixed(decimals);
  const latex = slope + ' \\times ' + x + ' + ' + intercept + ' = ' + yFormatted;
  return { y: yFormatted, latex };
}

/**
 * Tiny seedable RNG (mulberry32). Returns a function () → number in [0, 1).
 */
export function mulberry32(seed) {
  let a = seed | 0;
  return function () {
    a |= 0;
    a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Sample a single variable per its spec. Returns a numeric string formatted to declared precision.
 */
export function sampleValue(spec, rng) {
  if (spec.range) {
    const [low, high] = spec.range;
    const raw = low + rng() * (high - low);
    if (spec.decimal_places !== undefined) return raw.toFixed(spec.decimal_places);
    if (spec.sig_figs !== undefined) return formatWithSigFigs(raw, spec.sig_figs);
    return raw.toString();
  }
  throw new Error('sampleValue: unsupported spec shape: ' + JSON.stringify(spec));
}

const MAX_RETRIES = 50;

/**
 * Sample a full variant for a problem spec, running the declared operation
 * and enforcing guardrails. Throws if cap hit; caller falls back to original.
 */
export function generateVariant(problemSpec, rng) {
  for (let i = 0; i < MAX_RETRIES; i++) {
    const params = {};
    for (const [name, varSpec] of Object.entries(problemSpec.variables || {})) {
      params[name] = sampleValue(varSpec, rng);
    }
    const computed = computeAnswer(problemSpec.answer, params);
    if (passesGuardrails(problemSpec.constraints || {}, params, computed)) {
      return { params, computed };
    }
  }
  throw new Error('Guardrail cap hit (' + MAX_RETRIES + ' retries) for spec: ' + problemSpec.id);
}

function computeAnswer(answerSpec, params) {
  const op = answerSpec.operation;
  const values = Object.values(params);
  switch (op) {
    case 'subtract': {
      const [a, b] = values;
      return addPreservingDecimalPlaces([a, '-' + b.replace(/^[+-]/, '')]);
    }
    case 'add':
      return addPreservingDecimalPlaces(values);
    case 'multiply':
      return multiplyPreservingSigFigs(values);
    case 'count_sig_figs':
      return countSigFigs(values[0]);
    case 'to_sci_notation':
      return decimalToSciNotation(parseFloat(values[0]), countSigFigs(values[0]).count);
    case 'sci_notation_arithmetic':
      return computeSciNotationArith(answerSpec, params);
    case 'linear_function':
      return evaluateLinearFunction(params);
    default:
      throw new Error('Unknown operation: ' + op);
  }
}

function computeSciNotationArith(answerSpec, params) {
  // For Ch 1 pilot: support multiply on (coeff, exp) pairs
  const a = parseFloat(params.a_coefficient) * Math.pow(10, parseInt(params.a_exponent, 10));
  const b = parseFloat(params.b_coefficient) * Math.pow(10, parseInt(params.b_exponent, 10));
  const product = a * b;
  const sigFigs = Math.min(
    countSigFigs(params.a_coefficient).count,
    countSigFigs(params.b_coefficient).count
  );
  return decimalToSciNotation(product, sigFigs);
}

function passesGuardrails(constraints, params, computed) {
  // result_must_be_positive
  if (constraints.result_must_be_positive) {
    const final = parseFloat(computed.finalSum ?? computed.finalProduct ?? computed.y ?? '0');
    if (final <= 0) return false;
  }
  // result_range
  if (constraints.result_range) {
    const [low, high] = constraints.result_range;
    const final = parseFloat(computed.finalSum ?? computed.finalProduct ?? computed.y ?? '0');
    if (final < low || final > high) return false;
  }
  // avoid_round
  if (constraints.avoid_round) {
    for (const value of Object.values(params)) {
      if (constraints.avoid_round.includes(parseFloat(value))) return false;
    }
  }
  return true;
}
