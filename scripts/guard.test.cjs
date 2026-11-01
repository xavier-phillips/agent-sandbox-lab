const test = require('node:test');
const assert = require('node:assert/strict');
const {assertEligible, guard} = require('../.github/scripts/guard.cjs');
const sha = 'a'.repeat(40), base = 'b'.repeat(40);
const pr = {number: 7, state: 'open', draft: false, title: '[lean-bot] arithmetic', labels: [{name: 'agent:approved'}], head: {sha, repo: {full_name: 'owner/repo'}}, base: {sha: base, ref: 'main', repo: {full_name: 'owner/repo'}}};
const files = [{filename: 'fixture/math.js', status: 'modified', changes: 4}];
const check = (actual, expected, changed) => assertEligible(actual, expected, 'owner/repo', changed, 'main', base);
test('accept exact approved immutable trial change', () => assert.equal(check(pr, pr, files), pr));
test('reject head/base races, forks, scope expansion, drafts and approval loss', () => {
  for (const change of [{head: {...pr.head, sha: 'c'.repeat(40)}}, {base: {sha: 'c'.repeat(40)}}, {head: {...pr.head, repo: {full_name: 'fork/repo'}}}, {draft: true}, {draft: null}, {state: 'closed'}, {labels: []}, {title: 'ordinary PR'}]) assert.throws(() => check({...pr, ...change}, pr, files));
  for (const changed of [[], [{filename: '.github/workflows/pwn.yml', changes: 1}], ...['renamed', 'added', 'unknown', null].map(status => [{...files[0], status}]), ...[101, NaN, null, '4', -1, 1.5, Infinity].map(changes => [{...files[0], changes}]), [...files, ...files]]) assert.throws(() => check(pr, pr, changed));
  assert.throws(() => assertEligible(pr, pr, 'owner/repo', files, 'main', 'c'.repeat(40)), /advanced/);
  assert.throws(() => check({...pr, head: {...pr.head, sha: 'bad'}}, pr, files), /Malformed/);
});
test('consume repair budget before inference and deny subsequent PR attempts', async () => {
  const current = structuredClone(pr);
  let writes = 0;
  const github = {rest: {repos: {get: async () => ({data: {default_branch: 'main'}}), getBranch: async () => ({data: {commit: {sha: base}}})}, pulls: {get: async () => ({data: current}), listFiles: () => {}}, issues: {addLabels: async ({labels}) => {writes++; current.labels.push(...labels.map(name => ({name})));}}}, paginate: async () => files};
  const context = {repo: {owner: 'owner', repo: 'repo'}, payload: {pull_request: pr}};
  await guard({github, context}, true);
  assert.equal(writes, 1);
  await assert.rejects(guard({github, context}, true), /budget consumed/);
  assert.equal(writes, 1);
  await guard({github, context}, false); // Independent review is still permitted.
  await assert.rejects(guard({github, context: {...context, payload: {...context.payload, review: {commit_id: 'c'.repeat(40)}}}}, false), /Stale review/);
});
