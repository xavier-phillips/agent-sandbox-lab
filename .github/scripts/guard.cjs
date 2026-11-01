// Trusted platform glue only: gh-aw supplies per-run quotas, not a cumulative PR budget.
function assertEligible(pr, expected, repository, files, defaultBranch, latestBaseSha) {
  const sha = value => typeof value === 'string' && /^[a-f0-9]{40}$/.test(value);
  if (![pr.head?.sha, pr.base?.sha, expected.head?.sha, expected.base?.sha, latestBaseSha].every(sha)) throw Error('Malformed revision');
  if (pr.head?.sha !== expected.head?.sha || pr.base?.sha !== expected.base?.sha) throw Error('Stale head/base');
  if (typeof defaultBranch !== 'string' || !defaultBranch || pr.base.ref !== defaultBranch || latestBaseSha !== pr.base.sha) throw Error('Default/base branch advanced');
  if (pr.state !== 'open' || pr.draft !== false || pr.head?.repo?.full_name !== repository || pr.base?.repo?.full_name !== repository) throw Error('Ineligible PR');
  if (typeof pr.title !== 'string' || !Array.isArray(pr.labels) || pr.labels.some(x => typeof x.name !== 'string') || !pr.title.startsWith('[lean-bot] ') || !pr.labels.some(x => x.name === 'agent:approved')) throw Error('Not approved bot work');
  if (!Array.isArray(files) || files.length !== 1 || files.some(x => x.filename !== 'fixture/math.js' || x.status !== 'modified')) throw Error('Outside trial file policy');
  if (files.some(f => !Number.isSafeInteger(f.changes) || f.changes < 1 || f.changes > 100)) throw Error('Malformed or oversize patch');
  return pr;
}
async function guard({github, context}, reserve = false) {
  const {owner, repo} = context.repo;
  const expected = context.payload.pull_request;
  if (context.payload.review && context.payload.review.commit_id !== expected.head.sha) throw Error('Stale review revision');
  const pull_number = expected.number;
  const {data: repository} = await github.rest.repos.get({owner, repo});
  const {data: branch} = await github.rest.repos.getBranch({owner, repo, branch: repository.default_branch});
  const files = await github.paginate(github.rest.pulls.listFiles, {owner, repo, pull_number, per_page: 100});
  const {data: pr} = await github.rest.pulls.get({owner, repo, pull_number});
  assertEligible(pr, expected, `${owner}/${repo}`, files, repository.default_branch, branch.commit?.sha);
  if (context.payload.action === 'labeled' && context.payload.label?.name === 'agent:review-changes') {
    const reviews = await github.paginate(github.rest.pulls.listReviews, {owner, repo, pull_number, per_page: 100});
    const latest = reviews.filter(review => review.user?.login === 'github-actions[bot]' && review.commit_id === expected.head.sha && Number.isSafeInteger(review.id)).sort((a, b) => b.id - a.id)[0];
    if (latest?.state?.toLowerCase() !== 'changes_requested') throw Error('Missing current-head Actions change request');
  }
  if (reserve) {
    if (pr.labels.some(x => x.name === 'agent:repair-used')) throw Error('Repair budget consumed');
    await github.rest.issues.addLabels({owner, repo, issue_number: pull_number, labels: ['agent:repair-used']});
  }
}
module.exports = {assertEligible, guard};
