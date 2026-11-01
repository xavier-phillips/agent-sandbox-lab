// Reproduce pinned upstream push_signed_commits.cjs:310-321 with local Git only.
// This tests Git ancestry/lease semantics, not the complete gh-aw handler or GitHub service.
const test = require('node:test');
const assert = require('node:assert/strict');
const {mkdtempSync, mkdirSync, writeFileSync} = require('node:fs');
const {join} = require('node:path');
const {tmpdir} = require('node:os');
const {spawnSync} = require('node:child_process');
const {assertEligible} = require('../.github/scripts/guard.cjs');
const validation = join(tmpdir(), 'lean-github-bot-publication-races');
mkdirSync(validation, {recursive: true});
function git(cwd, args, check = true) {
  const result = spawnSync('git', args, {cwd, encoding: 'utf8', env: {...process.env, GIT_TERMINAL_PROMPT: '0'}});
  if (check && result.status !== 0) throw Error(`git ${args[0]} failed: ${result.stderr}`);
  return result;
}
function commit(cwd, file, text) {
  writeFileSync(join(cwd, file), text);
  git(cwd, ['add', file]);
  git(cwd, ['-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', text]);
  return git(cwd, ['rev-parse', 'HEAD']).stdout.trim();
}
function setup() {
  const root = mkdtempSync(join(validation, 'publication-race-'));
  const remote = join(root, 'remote.git'), worker = join(root, 'worker'), other = join(root, 'other');
  git(root, ['init', '--bare', remote]);
  git(root, ['init', '-b', 'pr', worker]);
  const baseline = commit(worker, 'math.txt', 'baseline');
  git(worker, ['remote', 'add', 'origin', remote]);
  git(worker, ['push', 'origin', 'pr:pr', 'pr:main']);
  git(root, ['clone', '--branch', 'pr', remote, other]);
  const workerHead = commit(worker, 'math.txt', 'worker correction');
  const live = branch => git(worker, ['ls-remote', 'origin', `refs/heads/${branch}`]).stdout.split(/\s/)[0];
  const advance = (branch = 'pr') => {
    if (branch === 'main') git(other, ['checkout', '-B', 'main', baseline]);
    const sha = commit(other, 'concurrent.txt', `concurrent ${branch}`);
    git(other, ['push', 'origin', branch]);
    return sha;
  };
  // Same ordering and branch lease used by upstream, with an optional adversarial move.
  const publish = beforePush => {
    const expectedHead = live('pr');
    if (!expectedHead) throw Error('Missing branch');
    if (git(worker, ['merge-base', '--is-ancestor', expectedHead, 'HEAD'], false).status !== 0) throw Error('non-fast-forward refused');
    beforePush?.();
    git(worker, ['push', `--force-with-lease=refs/heads/pr:${expectedHead}`, 'origin', 'pr']);
  };
  return {baseline, workerHead, live, advance, publish};
}
test('upstream ancestry plus explicit lease publishes an unchanged target', () => {
  const fixture = setup();
  fixture.publish();
  assert.equal(fixture.live('pr'), fixture.workerHead);
});
test('upstream ancestry refuses a divergent remote advance and preserves it', () => {
  const fixture = setup(), concurrent = fixture.advance();
  assert.throws(() => fixture.publish(), /non-fast-forward refused/);
  assert.equal(fixture.live('pr'), concurrent);
});
test('upstream lease refuses a race after ls-remote/ancestry and preserves it', () => {
  const fixture = setup();
  let concurrent;
  assert.throws(() => fixture.publish(() => {concurrent = fixture.advance();}), /git push failed/);
  assert.equal(fixture.live('pr'), concurrent);
});
test('independent default-base advance blocks final eligibility', () => {
  const fixture = setup();
  const moved = fixture.advance('main');
  const pr = {state: 'open', draft: false, title: '[lean-bot] fixture', labels: [{name: 'agent:approved'}], head: {sha: fixture.baseline, repo: {full_name: 'owner/repo'}}, base: {sha: fixture.baseline, ref: 'main', repo: {full_name: 'owner/repo'}}};
  assert.equal(fixture.live('main'), moved);
  assert.throws(() => assertEligible(pr, pr, 'owner/repo', [{filename: 'fixture/math.js', status: 'modified', changes: 1}], 'main', moved), /Default\/base branch advanced/);
});
