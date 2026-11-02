// QA: the owner's acceptance test for a PR lives in its linked issue, in a ```js acceptance block.
// The bot cannot edit tests, so this is the only executable check of the issue's own criteria.
const LINK = /\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)\b/i;
const BLOCK = /```js acceptance\r?\n([\s\S]*?)```/;

function extractAcceptance(issue, owner) {
  if (issue?.user?.login !== owner) throw Error('Acceptance must come from an owner-authored issue');
  if (!issue.labels?.some(l => (l.name ?? l) === 'agent:approved')) throw Error('Linked issue is not approved');
  const match = BLOCK.exec(issue.body ?? '');
  if (!match || !match[1].trim()) throw Error('Linked issue has no js acceptance block');
  return match[1];
}

async function loadAcceptance({github, context}) {
  const {owner, repo} = context.repo;
  const pr = context.payload.pull_request;
  const number = Number(LINK.exec(pr.body ?? '')?.[1]);
  if (!Number.isSafeInteger(number)) throw Error('PR body does not close an issue');
  const {data: issue} = await github.rest.issues.get({owner, repo, issue_number: number});
  return extractAcceptance(issue, owner);
}

module.exports = {LINK, extractAcceptance, loadAcceptance};
