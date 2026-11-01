import test from 'node:test';
import assert from 'node:assert/strict';
import { percent } from './math.js';

test('percentage arithmetic covers zero, fractional and negative values', () => {
  assert.equal(percent(80, 25), 20);
  assert.equal(percent(80, 0), 0);
  assert.equal(percent(50, 2.5), 1.25);
  assert.equal(percent(-80, 25), -20);
});
