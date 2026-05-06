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
 */
export function formatWithSigFigs(value, n) {
  if (value === 0) return n === 1 ? '0' : '0.' + '0'.repeat(n - 1);
  const sign = value < 0 ? '-' : '';
  const abs = Math.abs(value);
  const magnitude = Math.floor(Math.log10(abs));
  const factor = Math.pow(10, n - 1 - magnitude);
  const rounded = Math.round(abs * factor) / factor;
  // Determine decimals to keep
  const decimals = Math.max(0, n - 1 - magnitude);
  if (decimals === 0) {
    // Integer-style — may need trailing zeros via scaling
    return sign + Math.round(rounded).toString();
  }
  return sign + rounded.toFixed(decimals);
}
