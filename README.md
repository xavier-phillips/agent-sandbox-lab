# Lean GitHub bot

**Status, 2 November 2026: canonical repository established; workflows remain disabled.**
Repository: `xavier-phillips/agent-sandbox-lab` (private; repository ID 1441786552).
Root's live protocol probe has verified Chat Completions and Responses tool-call/result
continuation through the existing OmniRoute `agent-implement` pool. That pool currently
contains only the local `ai-server-fast` route; no Colab provider was started or qualified.
Pi/AWF, detector, review and GitHub publication have not yet passed end-to-end deployment.
The initial setup commit is `42120df`; hosted `Deterministic CI` has passed without inference.
Private-repository branch-protection configuration returned HTTP 403 for this account's
entitlement. Any public synthetic-lab switch and protected-merge test remain pending.
The maintained candidate uses GitHub Agentic Workflows (gh-aw), built-in Pi, the existing
OmniRoute endpoint and trusted safe-output publication. No daemon, poller, scheduler,
database, new router or custom agent supervisor is introduced.

## Accepted source to review/copy

- `.github/workflows/lean-work.md`: an explicitly applied `agent:approved` issue label starts bounded Pi work. Maintained create-pull-request safe output uses Xavier's repository-scoped publication PAT, allows only `fixture/math.js`, applies bot/approval metadata, and requests GitHub-native squash auto-merge.
- `.github/workflows/lean-repair.md`: ordinary PR events run deterministic fixture CI. A failure, a submitted human changes-requested review or the exact `agent:review-changes` label may reserve the PR's **one cumulative automatic repair**. Label triggers require the latest GitHub Actions review on that exact head to request changes. Activation must succeed without exhausted daily credits before reservation. Pi repairs the immutable triggering revision; maintained push-to-pull-request-branch publishes it. This avoids unsupported `workflow_run` remapping entirely.
- `.github/workflows/lean-review.md`: a fresh Pi context has Bash, CLI proxy and editing disabled. A maintained custom-safe-output job publishes the independent review as GitHub Actions, pinned to the event head. Its small trusted publisher first validates strict evidence and rechecks current head/base. Native submit-review was insufficient because empty APPROVE is accepted. Only `publish_review` receives `pull-requests: write`; it uses the job's `GITHUB_TOKEN`, with no extra account or review credential.
- `.github/scripts/guard.cjs`: the finite eligibility/budget glue. It validates well-formed immutable head/base, current repository default-branch tip, same-repository open/non-draft status, approved bot metadata, known file status and a safe integer change count for the permitted file. A separate trusted job consumes `agent:repair-used` before repair; worker safe outputs cannot alter labels. Same-PR reservations serialize. Repair/review recheck after inference/detection and inside the publisher.
- `.github/scripts/review-evidence.cjs`: rejects absent/multiple/empty/generic/malformed/stale review output. PASS needs exactly four concrete arithmetic cases, correct expected values and exact source-line evidence fetched at the immutable head; FAIL needs actual file/line findings. Structured evidence cannot prove model reasoning is correct: mutation and adversarial model trials remain required.
- `fixture/math.js`, `fixture/math.test.js`, `package.json`: dependency-free arithmetic fixture; no private project data. CI runs with read-only permissions and no provider/publisher secrets.
- `.github/workflows/ci.yml`: ordinary GitHub-hosted deterministic CI on main/PR/manual events. It uses no provider or publisher secrets and makes no inference calls. Its required-check name is `Deterministic CI`, distinct from the repair workflow's internal `fixture-ci` job.
- `.github/workflows/awf-boundary-probe.yml`: manual-only AWF 0.29.0 synthetic boundary check with explicit network isolation and no inference or publisher credential. Hosted run [41337054782](https://github.com/xavier-phillips/agent-sandbox-lab/actions/runs/41337054782) passed environment, host-file/home, socket, workspace, proxy-denial and direct-egress checks. This is a bounded canary test, not a proof against every escape.
- `scripts/guard.test.cjs`, `scripts/review-evidence.test.cjs`, `scripts/publication-race.test.cjs`, `scripts/check-compiled.py`: development validation, not an orchestration service. Fresh local Git race repositories go under the operating-system temporary directory; copied historical `validation/` is disposable test evidence, not repository source.
- `*.lock.yml`: generated, fully action-SHA-pinned lock workflows, not hand-maintained code.

Every inference-triggering path is disabled until repository variable `LEAN_BOT_TRIAL=true`
is deliberately set. Compiled YAML still contains invalid endpoint/model placeholders.

`.github/CODEOWNERS` requires Xavier for workflow, guard and test changes when native
code-owner review is enabled. Ordinary fixture changes use the independent Actions
review. The structured review validator can accept a false claim about faulty source;
an adversarial probe demonstrated this. It checks evidence shape and revision binding,
so current deterministic CI remains essential to merge eligibility.

## Exact tested versions and regeneration

gh-aw **v1.0.1**, source tag SHA `0627fdbe4beb5f3b71aa569f8d97150b87f2111a`.
Downloaded Windows compiler SHA256:
`1998b3443f0f7c85604ba8cdee897834033484d77daad9ff4e56d386c6e06d07`.
Actions source: `github/gh-aw-actions@221ba4f4319de6b8e809d1a15528b3ae6a818aa5`.
Compiler output pins Pi **1.4.0**, AWF **0.29.0**, and a maintained Codex threat detector.
The website's Pi page still said 1.3.0; the actual released compiler is the evidence here.

From this directory:

```powershell
gh aw compile lean-work lean-repair lean-review --no-check-update --json --action-mode action --action-tag 221ba4f4319de6b8e809d1a15528b3ae6a818aa5 --approve
node --test fixture/math.test.js scripts/guard.test.cjs scripts/review-evidence.test.cjs scripts/publication-race.test.cjs
python scripts/check-compiled.py
```

`--approve` records local generated-workflow secret-policy approval; it does not install,
authenticate or mutate GitHub. Review the frontmatter before approving regeneration.

Recorded candidate validation: all **3 agent workflows compile valid, 0 errors/warnings**; **10 Node tests pass**;
compiled security assertions pass. The guard tests cover stale head/base/review, forks,
draft/closed/unapproved PRs, malformed status/NaN counts, current default-base movement,
out-of-lane/oversize edits and cumulative budget consumption. Review tests reject generic,
fabricated, stale and missing evidence. Label removal by an authorised human can reset the
budget; this is mutable platform state, not an immutable ledger. The agent cannot reset it.
A separate mutant fixture changing divisor 100 to 10 failed (`200 != 20`) as expected;
the original fixture passes. Four focused local Git tests reproduce the pinned upstream
ancestry/explicit-lease sequence: unchanged target publishes, divergent advance refuses,
post-ls-remote race refuses, and independent default-base advance blocks eligibility.
These are local Git semantics tests, not execution of the whole upstream handler.
Those tests did not call inference or GitHub. Root's separate live protocol probe is
recorded above; protocol success does not establish whole-agent or merge-loop success.

## Provider and publication setup still unproven

Replace `omniroute.example.invalid` and the two qualified route IDs with verified existing
OmniRoute values. Pi uses **Responses API**, so chat/completions success alone is insufficient.
Qualify tool calls, continuation, context, timeout and model availability on Colab Qwen and
each explicitly eligible fallback. The workflow maps both provider-key environment aliases
to `OMNIROUTE_API_KEY`; generated AWF execution excludes these keys from the worker sandbox.

The separate maintained **Codex threat detector** uses the same Responses endpoint/key and
has `continue-on-error: false`. This does not require an OpenAI subscription by definition,
but its compatibility with the actual Qwen/OmniRoute route is **not demonstrated**. Declaring
Pi as detector compiled but silently generated a Copilot CLI fallback; the candidate instead
names Codex explicitly. Do not disable detection or silently add a paid fallback to make it pass.

`LEAN_BOT_CI_TRIGGER_TOKEN` is Xavier's repository-scoped publication PAT. Both native PR
creation and repair pushing use the supported per-handler `github-token` field; their
documented extra empty commit uses the same PAT. This makes Xavier the author/pusher and
starts ordinary CI without adding another account. Never set global `GH_AW_GITHUB_TOKEN`
to this write credential: worker GitHub/MCP access must remain read-only.

The generated work/repair jobs bind this PAT in trusted `Generate Safe Outputs Config`
and log-redaction steps, as well as the trusted publisher job. These host-framework bindings
are real credentials, not just placeholders. They are absent from Pi execution, the worker
GitHub/MCP token and detection jobs. AWF must keep their environment/files outside the actual
worker; a runtime credential/socket canary still needs to prove that isolation. The static
checker enforces the exact expected bindings and does not claim sandbox isolation is tested.

The independent reviewer uses `GITHUB_TOKEN` only in the trusted `publish_review` job with
`pull-requests: write`. The repository's Actions setting permitting PR review approval must
be enabled by the deployment owner. Whether GitHub counts that approval, dismisses it on a
new push and enforces the last-push rule needs an actual protected-repository trial.
GitHub does not start another workflow from a `GITHUB_TOKEN` review event. After a validated
REQUEST_CHANGES review succeeds, the trusted publisher uses the existing scoped PAT solely
to add fixed label `agent:review-changes`. That ordinary labeled PR event starts repair with
full revision context; the receiving guard checks the latest Actions review and exact head
before spending budget. An APPROVE never emits this label. In the review workflow, the PAT
is bound only in `publish_review`; the worker and detector receive no such binding.

Before enabling, root must verify required `Deterministic CI` success, required independent approval,
stale-approval dismissal, up-to-date branch or merge queue, native auto-merge availability,
no bot/admin bypass, and actual Actions-review acceptance. The internal repair `fixture-ci`
job can skip and must not be selected as the required check. A successful workflow process alone
is **not** a clean review; absent/failed/malformed review produces no GitHub approval and must
block merge. A model can still make an incorrect clean assessment; deterministic CI/policy
remain required. Policy/CI/config changes are outside this lane.

**Publisher fencing limits:** inside-publisher guards recheck immediately before the handlers.
Repair uses maintained unsigned bundle transport: the helper requires the freshly read live
head to be an ancestor of the immutable worker bundle, then pushes with a lease against that
live head. A concurrent divergent advance therefore fails rather than rebasing or overwriting
it; fallback publication is disabled. This was source-inspected, not exercised on GitHub.
Unlike exact event-head equality, a head already contained in the worker bundle is acceptable
to the helper. Source: [push_signed_commits.cjs lines 310–321](https://github.com/github/gh-aw/blob/v1.0.1/actions/setup/js/push_signed_commits.cjs#L310-L321);
the pinned PR handler passes `requireExistingBranch: true`. The four local race tests
exercise that same order and Git arguments. Upstream exposes no event-head/base equality option; its internal signed-helper
`requireBaseRefMatch` is not exposed by the PR handler. Base ref checks are not atomic with
head publication. Exact-commit approvals, stale-approval dismissal and up-to-date/merge-queue
rules remain the final merge gate. Full
same-head/base behaviour, CI retriggering, repair push, independent review and final auto-merge
must be demonstrated end to end before claiming this loop works unattended.

## Maintained runner setup (not installed by this document)

The pinned [v1.0.1 self-hosted runner reference](https://github.com/github/gh-aw/blob/v1.0.1/docs/src/content/docs/reference/self-hosted-runners.md)
requires Linux with a working Docker daemon. Podman compatibility is not documented or
verified; a Docker-compatible command name is not sufficient evidence. The supported
[default runtime](https://github.com/github/gh-aw/blob/v1.0.1/docs/src/content/docs/reference/sandbox.md#runtime-profiles)
is Docker with rootless AWF and network isolation. Trusted framework/MCP components need
the Docker socket; the agent's filesystem explicitly hides that socket. Do not bind a
host Docker or production Podman socket into the worker.

The smallest supported self-hosted topology is an isolated Linux VM dedicated to the
runner, with Docker inside it. Keep production ai-server container state and credentials
outside that VM. Keep deterministic CI and trusted publisher jobs GitHub-hosted; only
agent and detection jobs need access to the private inference endpoint. A hosted runner
is simpler if an already-authorised secure route to OmniRoute exists; do not expose the
private endpoint merely to avoid a runner VM.

Installation order for the deployment owner:

1. Provision the disposable Linux runner environment and a dedicated unprivileged account.
   Install Docker Engine and grant only that runner account/socket group access. No
   world-writable socket, ambient SSH/cloud/Git credentials, or production-host mounts.
2. Install the official GitHub Actions runner for this repository, Git, curl, tar and a
   writable runner toolcache. Node 24 is emitted by gh-aw for nonstandard runners; verify
   Node/npm PATH and writable job-scoped install locations before the first run.
3. Register the intended runner labels, then set top-level `runs-on` in each agentic
   frontmatter to those labels. Detection inherits the agent runner unless overridden.
   Keep `runs-on-slim`, safe outputs and explicit trusted custom jobs hosted; top-level
   `runs-on` alone does not move all generated jobs. Recompile and inspect the lock files.
4. Keep default AWF network isolation and narrowly allow the actual OmniRoute hostname.
   Use an endpoint reachable from the VM/API proxy, not a `localhost` URL that accidentally
   refers to a container. Verify provider continuation and credential/socket canaries in
   the sandbox before enabling the trial variable.
5. Verify cleanup after success, failure and cancellation. An ephemeral registration
   does not erase reused disks, Docker volumes, caches or HOME. Dispose the writable job
   environment before another trust domain or untrusted workload is admitted.

`docker-sudo-iptables` grants broader host/service access and is unnecessary for this lane.
ARC DinD is supported but adds Kubernetes and a privileged Docker sidecar; do not introduce
it for this single-runner trial. AWF's rootless default does not itself require runner sudo
or NET_ADMIN; daemon access remains a privileged capability of the trusted runner host.
No self-hosted runner, Docker installation or server change is claimed as completed here.

## Rejected and retained investigation material

OpenCode's GitHub Action was explicitly removed on 25 October: [upstream PR #59032](https://github.com/anomalyco/opencode/pull/59032).
Its frozen tags and stale website instructions must not be treated as maintained integration.
The native handler also persists its publisher token in local Git auth readable by agent Bash.
The investigation, frozen source, rejected workflow/config sketches, V1-only JSONL review
prototype and legacy validation binary remain in the dated external scratch investigation
folder. They were deliberately excluded from this repository's accepted source.

Primary references: [gh-aw v1.0.1](https://github.com/github/gh-aw/releases/tag/v1.0.1),
[Pi endpoint/credential isolation](https://github.github.com/gh-aw/reference/engines/pi/),
[revision-bound checkout](https://github.github.com/gh-aw/reference/checkout/),
[maintained PR safe outputs](https://github.github.com/gh-aw/reference/safe-outputs-pull-requests/),
[CI retriggering](https://github.github.com/gh-aw/reference/triggering-ci/).
