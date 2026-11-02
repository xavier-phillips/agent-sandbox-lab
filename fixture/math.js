export function percent(value, rate) {
  if (!Number.isFinite(value) || !Number.isFinite(rate)) {
    throw new TypeError('percent(value, rate) needs two finite numbers');
  }
  return value * rate / 100;
}
