// Trusted evidence gate for the gh-aw custom safe-output publisher, never from PR head.
function validateEvidence(output, expected, source) {
  if (!output || !Array.isArray(output.items)) throw Error('Missing safe outputs');
  const reviews = output.items.filter(x => x.type === 'publish_review');
  if (reviews.length !== 1) throw Error('Exactly one review required');
  const review = reviews[0];
  if (!['APPROVE', 'REQUEST_CHANGES'].includes(review.event)) throw Error('Invalid review event');
  if (typeof review.body !== 'string' || review.body.length > 20000) throw Error('Missing or oversize evidence');
  const body = JSON.parse(review.body);
  if (Object.keys(body).sort().join(',') !== 'base_sha,findings,head_sha,inspected,verdict') throw Error('Invalid evidence schema');
  if (body.head_sha !== expected.head.sha || body.base_sha !== expected.base.sha) throw Error('Stale review evidence');
  if (!['PASS', 'FAIL'].includes(body.verdict) || (body.verdict === 'PASS') !== (review.event === 'APPROVE')) throw Error('Verdict/event mismatch');
  if (!Array.isArray(body.findings) || !Array.isArray(body.inspected) || body.inspected.length > 12 || body.findings.length > 12) throw Error('Invalid evidence arrays');
  const lineEvidence = value => {
    if (value.file !== 'fixture/math.js' || !Number.isSafeInteger(value.line) || value.line < 1) throw Error('Invalid evidence location');
    const actual = source.split(/\r?\n/)[value.line - 1];
    if (!actual?.trim() || value.code !== actual.trim()) throw Error('Evidence does not quote actual immutable code');
    if (typeof value.reason !== 'string' || value.reason.trim().length < 40 || value.reason.length > 2000) throw Error('Missing concrete reasoning');
  };
  body.inspected.forEach(lineEvidence);
  body.findings.forEach(lineEvidence);
  if (body.verdict === 'PASS') {
    if (body.findings.length || body.inspected.length !== 4) throw Error('Unresolved or missing cases');
    const cases = {normal: [[80, 25], 20], zero: [[80, 0], 0], fractional: [[50, 2.5], 1.25], negative: [[-80, 25], -20]};
    const seen = new Set();
    for (const item of body.inspected) {
      if (!Object.hasOwn(cases, item.case) || seen.has(item.case) || JSON.stringify(item.inputs) !== JSON.stringify(cases[item.case][0]) || item.expected !== cases[item.case][1]) throw Error('Missing or wrong inspected edge case');
      seen.add(item.case);
    }
  } else if (body.findings.length < 1) throw Error('FAIL requires file/line findings');
  return body;
}
module.exports = {validateEvidence};
