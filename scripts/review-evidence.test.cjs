const test = require('node:test');
const assert = require('node:assert/strict');
const {validateEvidence} = require('../.github/scripts/review-evidence.cjs');
const expected = {head: {sha: 'a'.repeat(40)}, base: {sha: 'b'.repeat(40)}};
const source = 'export function percent(value, rate) {\n  return value * rate / 100;\n}\n';
const reason = 'Multiplying by the signed value and decimal rate then dividing by one hundred preserves this exact expected percentage.';
const inspected = Object.entries({normal: [[80,25],20], zero: [[80,0],0], fractional: [[50,2.5],1.25], negative: [[-80,25],-20]}).map(([kind,[inputs,result]]) => ({case: kind, inputs, expected: result, file: 'fixture/math.js', line: 2, code: 'return value * rate / 100;', reason}));
const pass = {head_sha: expected.head.sha, base_sha: expected.base.sha, verdict: 'PASS', inspected, findings: []};
const wrap = body => ({items: [{type: 'publish_review', event: 'APPROVE', body: JSON.stringify(body)}]});
test('accept concrete immutable clean-case evidence and adverse file-line findings', () => {
  assert.equal(validateEvidence(wrap(pass), expected, source).verdict, 'PASS');
  const fail = {head_sha: expected.head.sha, base_sha: expected.base.sha, verdict: 'FAIL', inspected: [], findings: [{file: 'fixture/math.js', line: 2, code: 'return value * rate / 100;', reason}]};
  assert.equal(validateEvidence({items: [{type: 'publish_review', event: 'REQUEST_CHANGES', body: JSON.stringify(fail)}]}, expected, source).verdict, 'FAIL');
});
test('reject empty generic malformed absent stale or fabricated approvals', () => {
  for (const output of [{}, {items: []}, {items: [{type: 'publish_review', event: 'APPROVE', body: ''}]}, {items: [{type: 'publish_review', event: 'APPROVE', body: 'looks good'}]}, {items: [...wrap(pass).items, ...wrap(pass).items]}]) assert.throws(() => validateEvidence(output, expected, source));
  for (const edit of [{head_sha: 'c'.repeat(40)}, {base_sha: 'c'.repeat(40)}, {verdict: 'FAIL'}, {inspected: []}, {findings: [{}]}, {extra: true}, {inspected: inspected.map(x => ({...x, code: 'not actual code'}))}, {inspected: inspected.map(x => ({...x, reason: 'looks good'}))}, {inspected: inspected.map(x => ({...x, expected: 999}))}, {inspected: inspected.map(x => ({...x, case: 'normal'}))}]) assert.throws(() => validateEvidence(wrap({...pass, ...edit}), expected, source));
  assert.throws(() => validateEvidence(wrap(pass), expected, source.replace('/ 100', '/ 10')), /immutable code/);
});

