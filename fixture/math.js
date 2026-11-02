// Percentage helper used by the fixture tests.
// Throws TypeError for non-finite input.
export function percent(value, rate) {
  if (!Number.isFinite(value) || !Number.isFinite(rate)) {
    throw new TypeError('percent() requires finite numeric value and rate');
  }
  return value * rate / 100;
}
