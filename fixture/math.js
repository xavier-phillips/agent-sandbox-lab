export function percent(value, rate) {
  if (!Number.isFinite(value) || !Number.isFinite(rate)) {
    throw new TypeError('percent() requires finite numeric value and rate');
  }
  return value * rate / 100;
}
