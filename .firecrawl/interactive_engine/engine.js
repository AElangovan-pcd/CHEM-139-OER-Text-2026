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
  // Engineering threshold: route Avogadro-scale and sub-millimagnitude values
  // through decimalToSciNotation to bypass IEEE-754 noise in the integer branch
  // (Math.round on doubles like 5.7e+23 can leak "5.700000000000001e+23").
  if (abs >= 1e6 || abs < 1e-3) {
    const sci = decimalToSciNotation(value, n);
    const expSign = sci.exponent >= 0 ? '+' : '';
    return sci.coefficient + 'e' + expSign + sci.exponent;
  }
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
 * Convert a JS-stringified number to MathJax LaTeX form. JS sci-notation
 * (e.g. "6.022e+23") becomes "6.022 \\times 10^{23}". Plain decimals
 * pass through unchanged. No-op on already-formatted LaTeX strings.
 *
 * Used at every site where a numeric string flows into a \[...\] block
 * so MathJax never sees raw "e+N" plain text.
 */
export function formatNumberForLatex(s) {
  const str = String(s);
  const m = str.match(/^([+-]?\d+(?:\.\d+)?)[eE]([+-]?\d+)$/);
  if (!m) return str;
  const coefficient = m[1];
  const exponent = parseInt(m[2], 10);
  return coefficient + ' \\times 10^{' + exponent + '}';
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
  if (spec.generator === 'random_decimal_with_features') {
    const sigFigs = spec.sig_figs[Math.floor(rng() * spec.sig_figs.length)];
    const pattern = spec.patterns[Math.floor(rng() * spec.patterns.length)];
    return generateFeaturePattern(sigFigs, pattern, rng);
  }
  if (spec.range) {
    const [low, high] = spec.range;
    const raw = low + rng() * (high - low);
    if (spec.decimal_places !== undefined) {
      const formatted = raw.toFixed(spec.decimal_places);
      // Strip a leading '-' for negative zero (e.g. (-0.4).toFixed(0) → "-0")
      return parseFloat(formatted) === 0 ? formatted.replace(/^-/, '') : formatted;
    }
    if (spec.sig_figs !== undefined) return formatWithSigFigs(raw, spec.sig_figs);
    return raw.toString();
  }
  throw new Error('sampleValue: unsupported spec shape: ' + JSON.stringify(spec));
}

function generateFeaturePattern(sigFigs, pattern, rng) {
  const digits = () => Math.floor(rng() * 9) + 1;  // 1-9
  const captive = () => '0';
  switch (pattern) {
    case 'leading_zeros': {
      // "0.00<sig digits>"
      const leading = '0.' + '0'.repeat(2 + Math.floor(rng() * 3));
      let body = '';
      for (let i = 0; i < sigFigs; i++) body += i === 0 ? digits() : Math.floor(rng() * 10);
      return leading + body;
    }
    case 'captive_zero': {
      // "<d><0><d><d>..." with at least one captive zero
      let body = String(digits());
      for (let i = 1; i < sigFigs; i++) {
        body += (i === 1 || i === 2) ? captive() : digits();
      }
      // Add a decimal point partway through
      const dot = 1 + Math.floor(rng() * (sigFigs - 1));
      return body.slice(0, dot) + '.' + body.slice(dot);
    }
    case 'trailing_zero_with_decimal': {
      // "<digits>.<digits>0" where final 0 is significant
      let body = '';
      for (let i = 0; i < sigFigs - 1; i++) body += i === 0 ? digits() : Math.floor(rng() * 10);
      body += '0';
      // Insert a decimal point partway
      const dot = 1 + Math.floor(rng() * (body.length - 1));
      return body.slice(0, dot) + '.' + body.slice(dot);
    }
    case 'mixed':
    default: {
      // Random number with N sig figs and a decimal somewhere
      let body = String(digits());
      for (let i = 1; i < sigFigs; i++) body += Math.floor(rng() * 10);
      const dot = 1 + Math.floor(rng() * (sigFigs - 1));
      return body.slice(0, dot) + '.' + body.slice(dot);
    }
  }
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
    case 'factor_label': {
      const value = params[answerSpec.value_param];
      const valueSigFigs = countSigFigs(value).count;
      return factorLabelChain(value, valueSigFigs, answerSpec.input_unit, answerSpec.chain);
    }
    case 'mass_percent':
      return computeMassPercent(answerSpec, params);
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

/**
 * Mass-percent operation: (partial / total) * 100, rounded to N decimal places.
 * Sister to to_sci_notation in that the precision idiom (decimals, not sig figs)
 * is operation-specific. Author chooses decimal_places per the textbook
 * convention (2 for light-element compounds, 1 for any-heavy compound).
 */
export function computeMassPercent(answerSpec, params) {
  const partial = parseFloat(params[answerSpec.partial_mass_param]);
  const total = parseFloat(params[answerSpec.total_mass_param]);
  const decimals = answerSpec.decimal_places ?? 2;
  const rawPercent = (partial / total) * 100;
  const finalPercent = rawPercent.toFixed(decimals);
  return {
    rawPercent: rawPercent.toString(),
    finalPercent,
    finalPercentLatex: finalPercent,
  };
}

function passesGuardrails(constraints, params, computed) {
  // result_must_be_positive
  if (constraints.result_must_be_positive) {
    const final = parseFloat(
      computed.finalSum ?? computed.finalProduct ?? computed.y
      ?? computed.finalResult ?? computed.finalPercent ?? '0'
    );
    if (final <= 0) return false;
  }
  // result_range
  if (constraints.result_range) {
    const [low, high] = constraints.result_range;
    const final = parseFloat(
      computed.finalSum ?? computed.finalProduct ?? computed.y
      ?? computed.finalResult ?? computed.finalPercent ?? '0'
    );
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

/**
 * Substitute {token} placeholders in a string with values from a map.
 *
 * MathJax-aware: tokens inside `\(...\)` regions are formatted via
 * formatNumberForLatex so JS sci-notation values (e.g. "6.022e+23") render as
 * "6.022 \times 10^{23}". Tokens outside `\(...\)` are substituted raw.
 * This lets YAML authors opt a single token into LaTeX form by wrapping it,
 * without polluting plain-prose substitution elsewhere.
 */
export function substituteTemplate(template, tokens) {
  return template.replace(/(\\\([\s\S]*?\\\))|(\{(\w+)\})/g, (match, mathjax, _whole, key) => {
    if (mathjax !== undefined) {
      return mathjax.replace(/\{(\w+)\}/g, (_, k) =>
        k in tokens ? formatNumberForLatex(String(tokens[k])) : '{' + k + '}'
      );
    }
    return key in tokens ? String(tokens[key]) : match;
  });
}

/**
 * Render LaTeX for a given operation type. Returns a LaTeX string for MathJax.
 */
export function renderLatexForOperation(op, variant, answerSpec) {
  const u = answerSpec.unit ? '\\,\\text{' + answerSpec.unit + '}' : '';
  const p = variant.params;
  const c = variant.computed;
  switch (op) {
    case 'subtract':
      return p.a + u + ' - ' + p.b + u + ' = ' + c.finalSum + u;
    case 'add':
      return Object.values(p).join(u + ' + ') + u + ' = ' + c.finalSum + u;
    case 'multiply':
      return Object.values(p).join(u + ' \\times ') + u + ' = ' + c.finalProduct + u;
    case 'count_sig_figs':
      return p[Object.keys(p)[0]];
    case 'to_sci_notation':
      return p[Object.keys(p)[0]] + ' = ' + c.latex;
    case 'sci_notation_arithmetic': {
      const aLatex = p.a_coefficient + ' \\times 10^{' + p.a_exponent + '}';
      const bLatex = p.b_coefficient + ' \\times 10^{' + p.b_exponent + '}';
      return '(' + aLatex + ')(' + bLatex + ') = ' + c.latex;
    }
    case 'linear_function':
      return c.latex + u;
    case 'factor_label':
      return renderFactorLabelLatex(
        p[answerSpec.value_param],
        answerSpec.input_unit,
        answerSpec.chain,
        c.finalResult,
        c.finalUnit,
        c.finalResultLatex,
      );
    case 'mass_percent': {
      const partial = p[answerSpec.partial_mass_param];
      const total = p[answerSpec.total_mass_param];
      const elementLabel = p[answerSpec.element_label_param];
      const compoundLabel = p[answerSpec.compound_label_param];
      return '\\dfrac{' + partial + '\\,\\text{g ' + elementLabel + '}}'
           + '{' + total + '\\,\\text{g ' + compoundLabel + '}}'
           + ' \\times 100\\% = ' + c.finalPercent + '\\%';
    }
    default:
      throw new Error('renderLatexForOperation: unknown op ' + op);
  }
}

/**
 * Apply a chain of conversion factors to a starting value.
 * Validates that each step's denominator unit cancels with the previous numerator
 * (or with valueUnit for step 0). Tracks sig-fig propagation across exact and
 * inexact factors. Throws on cancellation mismatch or missing sig_figs.
 */
export function factorLabelChain(value, valueSigFigs, valueUnit, steps) {
  // Validate cancellation chain and sig-fig declarations
  let prevNumUnit = valueUnit;
  for (let i = 0; i < steps.length; i++) {
    const s = steps[i];
    if (s.den_unit !== prevNumUnit) {
      throw new Error(
        'factorLabelChain: cancellation mismatch at step ' + i +
        ': expected den_unit "' + prevNumUnit + '", got "' + s.den_unit + '"'
      );
    }
    if (!s.exact && (s.sig_figs === undefined || s.sig_figs === null)) {
      throw new Error(
        'factorLabelChain: step ' + i + ' must declare sig_figs or set exact: true'
      );
    }
    prevNumUnit = s.num_unit;
  }

  // Compute raw result
  let result = parseFloat(value);
  for (const s of steps) {
    result = result * (s.num_value / s.den_value);
  }

  // Sig-fig propagation: input value + each non-exact factor's sig_figs
  let limitingSigFigs = valueSigFigs;
  let limitingSource = 'value';
  for (let i = 0; i < steps.length; i++) {
    const s = steps[i];
    if (!s.exact && s.sig_figs !== undefined && s.sig_figs < limitingSigFigs) {
      limitingSigFigs = s.sig_figs;
      limitingSource = 'step[' + i + ']';
    }
  }

  // Engineering-threshold sci-notation: |result| >= 1e6 or < 1e-3 routes
  // through decimalToSciNotation so the displayed value is built from integer
  // coefficient/exponent arithmetic. formatWithSigFigs's integer branch can
  // leak IEEE-754 noise on Avogadro-scale doubles (e.g. 3.80e+24 → "3.7999...").
  const absResult = Math.abs(result);
  const useSci = absResult >= 1e6 || (absResult > 0 && absResult < 1e-3);
  let finalResult, finalResultLatex;
  if (useSci) {
    const sci = decimalToSciNotation(result, limitingSigFigs);
    const expSign = sci.exponent >= 0 ? '+' : '';
    finalResult = sci.coefficient + 'e' + expSign + sci.exponent;
    finalResultLatex = sci.latex;
  } else {
    finalResult = formatWithSigFigs(result, limitingSigFigs);
    finalResultLatex = finalResult;
  }

  return {
    rawResult: result.toString(),
    finalResult,
    finalResultLatex,
    finalUnit: prevNumUnit,
    limitingSigFigs,
    limitingSource,
  };
}

/**
 * Render a factor-label chain as MathJax LaTeX with \cancel{} on cancelled units.
 * Output format matches the textbook's Option-C convention exactly:
 *   value\,\cancel{\text{unit}} \times \frac{num\,\text{numUnit}}{den\,\cancel{\text{denUnit}}} ... = result\,\text{finalUnit}
 */
export function renderFactorLabelLatex(value, valueUnit, steps, finalResult, finalUnit, finalResultLatex) {
  let latex = formatNumberForLatex(value) + '\\,\\cancel{\\text{' + valueUnit + '}}';
  for (const s of steps) {
    latex += ' \\times \\frac{' + formatNumberForLatex(s.num_value) + '\\,\\text{' + s.num_unit + '}}'
           + '{' + formatNumberForLatex(s.den_value) + '\\,\\cancel{\\text{' + s.den_unit + '}}}';
  }
  // Prefer caller-supplied finalResultLatex (precision-safe sci-notation form);
  // fall back to formatting finalResult for backward compat.
  const resultLatex = finalResultLatex !== undefined
    ? finalResultLatex
    : formatNumberForLatex(finalResult);
  latex += ' = ' + resultLatex + '\\,\\text{' + finalUnit + '}';
  return latex;
}

// ---- Browser bootstrap (runs only when DOM is available) ----

const VARIANT_BUTTON_LABEL = 'Try a different version';

/**
 * Find all problems flagged with [data-variant-spec], wire up buttons, render initial variants.
 */
export function bootstrap() {
  const specsEl = document.getElementById('variant-specs');
  if (!specsEl) {
    console.warn('[interactive-engine] No #variant-specs JSON found on page; nothing to do.');
    return;
  }
  let specs;
  try {
    specs = JSON.parse(specsEl.textContent).problems || [];
  } catch (e) {
    console.error('[interactive-engine] Could not parse #variant-specs JSON:', e);
    return;
  }
  // ARIA-live region for variant-change announcements
  ensureAriaLiveRegion();
  for (const spec of specs) {
    const stem = document.querySelector('[data-variant-spec="' + spec.id + '"]');
    if (!stem) {
      console.warn('[interactive-engine] No DOM node for spec ' + spec.id);
      continue;
    }
    try {
      wireProblem(stem, spec);
    } catch (e) {
      console.error('[interactive-engine] Failed to wire spec ' + spec.id + ':', e);
      // Don't bail — keep wiring the remaining problems.
    }
  }
}

function ensureAriaLiveRegion() {
  if (document.getElementById('variant-aria-live')) return;
  const r = document.createElement('div');
  r.id = 'variant-aria-live';
  r.setAttribute('aria-live', 'polite');
  r.setAttribute('aria-atomic', 'true');
  r.style.position = 'absolute';
  r.style.left = '-9999px';
  r.style.width = '1px';
  r.style.height = '1px';
  r.style.overflow = 'hidden';
  document.body.appendChild(r);
}

function announce(msg) {
  const r = document.getElementById('variant-aria-live');
  if (r) r.textContent = msg;
}

function wireProblem(stemEl, spec) {
  const solutionEl = stemEl.nextElementSibling;
  if (!solutionEl || !solutionEl.classList.contains('solution')) {
    console.warn('[interactive-engine] No sibling .solution for spec ' + spec.id);
    return;
  }

  // Preserve <summary> as a direct child of <details> and wrap the rest of the
  // solution content in a stable body div, so we can re-render only the body
  // on each variant cycle without wiping the summary.
  const summary = solutionEl.querySelector(':scope > summary');
  let bodyEl = solutionEl.querySelector(':scope > .variant-solution-body');
  if (!bodyEl) {
    bodyEl = document.createElement('div');
    bodyEl.className = 'variant-solution-body';
    const childrenToMove = Array.from(solutionEl.childNodes).filter(n => n !== summary);
    for (const c of childrenToMove) bodyEl.appendChild(c);
    solutionEl.appendChild(bodyEl);
  }

  // Capture any leading <strong>NN.</strong> serial number prefix from the stem.
  // Re-prepended on each variant render so the problem numbering stays visible.
  let serialPrefix = '';
  const firstChild = stemEl.firstElementChild;
  if (firstChild && firstChild.tagName.toLowerCase() === 'strong') {
    serialPrefix = firstChild.outerHTML;
    const nextNode = firstChild.nextSibling;
    if (nextNode && nextNode.nodeType === Node.TEXT_NODE) {
      const m = nextNode.nodeValue.match(/^\s+/);
      if (m) serialPrefix += m[0];
    }
  }

  // Insert the variant button BETWEEN the stem and the pill (outside the pill,
  // matching the textbook author's preferred layout).
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'try-variant';
  btn.textContent = VARIANT_BUTTON_LABEL;
  btn.setAttribute('aria-label', VARIANT_BUTTON_LABEL + ' for this problem');
  stemEl.insertAdjacentElement('afterend', btn);

  // Capture originals for guardrail-cap-hit fallback
  const originalStemHTML = stemEl.innerHTML;
  const originalBodyHTML = bodyEl.innerHTML;

  const state = {
    rng: mulberry32(Date.now() & 0xffffffff),
    spec, stemEl, solutionEl, bodyEl,
    serialPrefix,
    originalStemHTML, originalBodyHTML,
  };

  cycleVariant(state, /*announceChange=*/ false);
  btn.addEventListener('click', (e) => {
    e.preventDefault();
    cycleVariant(state, /*announceChange=*/ true);
  });
}

function cycleVariant(state, announceChange) {
  let variant;
  try {
    variant = generateVariant(state.spec, state.rng);
  } catch (e) {
    console.warn('[interactive-engine] Falling back to original values for ' + state.spec.id, e);
    state.stemEl.innerHTML = state.originalStemHTML;
    state.bodyEl.innerHTML = state.originalBodyHTML;
    return;
  }

  // Update the question stem (re-prepend the captured serial prefix)
  state.stemEl.innerHTML = state.serialPrefix + substituteTemplate(state.spec.question, variant.params);

  // Update only the solution body — preserves <summary> and the variant button
  const op = state.spec.answer.operation;
  const latex = renderLatexForOperation(op, variant, state.spec.answer);
  const explanationTokens = { ...variant.params, ...flattenComputed(variant.computed) };
  const explanation = state.spec.explanation_template
    ? substituteTemplate(state.spec.explanation_template, explanationTokens)
    : '';
  state.bodyEl.innerHTML = '<div class="math-chain">\\[' + latex + '\\]</div><p><em>' + explanation + '</em></p>';

  // On user click, close the pill so the student must re-open to check the
  // recomputed solution — enforces "try first" before peeking. On initial
  // bootstrap, leave the pill in whatever state the page started in.
  if (announceChange) {
    if (state.solutionEl.tagName.toLowerCase() === 'details' && state.solutionEl.open) {
      state.solutionEl.open = false;
    }
  }

  // MathJax retypeset (works on hidden details content).
  // Guard against the async-load race: MathJax.startup may exist before
  // MathJax.startup.promise is created. Skip cleanly if MathJax isn't ready.
  maybeTypeset([state.bodyEl, state.stemEl]);

  if (announceChange) announce('Problem updated with new values. Open the solution pill to check your work.');
}

function flattenComputed(computed) {
  // Spread computed result fields as tokens; rename ambiguous keys for templates.
  const out = {};
  for (const [k, v] of Object.entries(computed)) {
    out[k] = v;
  }
  return out;
}

/**
 * Defensively call MathJax.typesetPromise on the given elements.
 * Handles three cases without throwing:
 *   1. MathJax not loaded yet — skip (the initial typeset pass will handle).
 *   2. MathJax loaded but startup.promise not yet created — typeset immediately.
 *   3. MathJax fully ready — wait for startup, then typeset.
 */
function maybeTypeset(elements) {
  if (typeof MathJax === 'undefined') return;
  if (typeof MathJax.typesetPromise !== 'function') return;
  const ready = (MathJax.startup && MathJax.startup.promise)
    ? MathJax.startup.promise
    : Promise.resolve();
  ready
    .then(() => MathJax.typesetPromise(elements))
    .catch((e) => console.error('[interactive-engine] MathJax typeset error:', e));
}

// Auto-bootstrap when running in a browser
if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap);
  } else {
    bootstrap();
  }
}
