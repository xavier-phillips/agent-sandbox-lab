---
description: One native PR-event CI repair with a deterministic cumulative budget
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review, labeled]
  pull_request_review:
    types: [submitted]
if: vars.LEAN_BOT_TRIAL == 'true'
permissions:
  contents: read
  issues: read
  pull-requests: read
engine:
  id: pi
  version: '1.4.0'
  bare: true
  model: openai/lean-qwen27b
  model-provider: openai
  env:
    OPENAI_BASE_URL: https://ai-server.tail67b2d4.ts.net/v1
    CODEX_API_KEY: ${{ secrets.OMNIROUTE_API_KEY }}
    OPENAI_API_KEY: ${{ secrets.OMNIROUTE_API_KEY }}
models:
  # Self-hosted Qwen: AWF needs a rate to meter ai-credits; turns and timeouts are the real bounds.
  default-ai-credits-pricing:
    input: 0.000001
    output: 0.000001
network:
  allowed: [defaults, ai-server.tail67b2d4.ts.net]
tools:
  bash: true
  github:
    toolsets: [issues, pull_requests, repos]
safe-outputs:
  steps:
    # Own directory: checking out over the workspace would drop the publisher's push credentials.
    - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
      with:
        ref: ${{ github.event.pull_request.base.sha }}
        path: fence
        persist-credentials: false
    - name: Fence live PR and default-base revision inside native publisher job
      uses: actions/github-script@3a2844b7e9c422d3c10d287c895573f7108da1b3
      with:
        script: |
          const {guard} = require('./fence/.github/scripts/guard.cjs');
          await guard({github, context}, false);
  threat-detection:
    continue-on-error: false
    engine-timeout: 15m  # dense Qwen at ~16 tok/s; a timeout still fails closed
    engine:
      id: codex
      model: openai/lean-qwen27b
      model-provider: openai
      env:
        OPENAI_BASE_URL: https://ai-server.tail67b2d4.ts.net/v1
        CODEX_API_KEY: ${{ secrets.OMNIROUTE_API_KEY }}
        OPENAI_API_KEY: ${{ secrets.OMNIROUTE_API_KEY }}
  push-to-pull-request-branch:
    github-token: ${{ secrets.LEAN_BOT_CI_TRIGGER_TOKEN }}
    target: triggering
    required-title-prefix: '[lean-bot] '
    required-labels: [agent:approved]
    allowed-files: [fixture/math.js]
    max: 1
    patch-format: bundle
    signed-commits: false
    fallback-as-pull-request: false
    github-token-for-extra-empty-commit: ${{ secrets.LEAN_BOT_CI_TRIGGER_TOKEN }}
jobs:
  fixture-ci:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: read
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
        with:
          ref: ${{ github.event.pull_request.base.sha }}
          path: base
          persist-credentials: false
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
        with:
          ref: ${{ github.event.pull_request.head.sha }}
          path: head
          persist-credentials: false
      - uses: actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1
        with:
          node-version: '24'
      - run: npm test
        working-directory: head
      - uses: actions/github-script@3a2844b7e9c422d3c10d287c895573f7108da1b3
        with:
          script: |
            const {loadAcceptance} = require('./base/.github/scripts/acceptance.cjs');
            require('fs').writeFileSync('head/qa-acceptance.test.mjs', await loadAcceptance({github, context}));
      - run: node --test qa-acceptance.test.mjs
        working-directory: head
  reserve:
    needs: [activation, fixture-ci]
    if: >-
      always() && !cancelled() && needs.activation.result == 'success' &&
      needs.activation.outputs.daily_ai_credits_exceeded != 'true' &&
      (needs.fixture-ci.result == 'failure' || github.event.review.state == 'changes_requested' ||
       (github.event.action == 'labeled' && github.event.label.name == 'agent:review-changes')) &&
      vars.LEAN_BOT_TRIAL == 'true' &&
      github.event.pull_request.head.repo.full_name == github.repository &&
      contains(github.event.pull_request.labels.*.name, 'agent:approved')
    runs-on: ubuntu-latest
    concurrency:
      group: lean-bot-budget-${{ github.event.pull_request.number }}
      cancel-in-progress: false
    permissions:
      contents: read
      issues: write
      pull-requests: write  # labelling a PR needs this as well as issues: write
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
        with:
          ref: ${{ github.event.pull_request.base.sha }}
          persist-credentials: false
      - uses: actions/github-script@3a2844b7e9c422d3c10d287c895573f7108da1b3
        with:
          script: |
            const {guard} = require('./.github/scripts/guard.cjs');
            await guard({github, context}, true);
  agent:
    permissions:
      contents: read
      issues: read
      pull-requests: read
    pre-steps:
      - name: Connect private inference tailnet
        uses: tailscale/github-action@064b10558093f38325e838ddea35486bdc6b1d5c # v4.4.0
        env:
          XDG_RUNTIME_DIR: ${{ runner.temp }}/lean-tailscale
        with:
          oauth-client-id: ${{ secrets.TS_OAUTH_CLIENT_ID }}
          oauth-secret: ${{ secrets.TS_OAUTH_CLIENT_SECRET }}
          tags: tag:github-bot
          version: '1.102.4'
          use-cache: 'false'
          log-mode: quiet
      - name: Resolve tailnet names inside the AWF sandbox
        # AWF's proxy uses the runner's upstream DNS, which cannot see MagicDNS. PREROUTING only
        # sees container traffic, so send container DNS to Tailscale's resolver (it forwards public
        # names upstream). The domain allowlist and tailnet ACL still decide reachability.
        run: |
          for p in udp tcp; do
            sudo iptables -t nat -I PREROUTING -p "$p" --dport 53 -j DNAT --to-destination 100.100.100.100:53
          done
      - name: Wait for dense Qwen (cold start up to 600 s)
        env:
          OMNIROUTE_API_KEY: ${{ secrets.OMNIROUTE_API_KEY }}
        run: |
          code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 600             -H "Authorization: Bearer $OMNIROUTE_API_KEY" -H 'Content-Type: application/json'             -d '{"model":"lean-qwen27b","max_tokens":1,"messages":[{"role":"user","content":"ok"}]}'             https://ai-server.tail67b2d4.ts.net/v1/chat/completions)
          echo "warm-up HTTP $code"
          test "$code" = 200
    needs: [fixture-ci, reserve]
    if: always() && needs.reserve.result == 'success'
  recheck:
    needs: [agent, detection]
    # always(): fixture-ci failing is what starts a repair, so default success() would skip this.
    if: always() && needs.agent.result == 'success' && needs.detection.result == 'success'
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: read
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
        with:
          ref: ${{ github.event.pull_request.base.sha }}
          persist-credentials: false
      - uses: actions/github-script@3a2844b7e9c422d3c10d287c895573f7108da1b3
        with:
          script: |
            const {guard} = require('./.github/scripts/guard.cjs');
            await guard({github, context}, false);
  safe_outputs:
    needs: [recheck]
    if: always() && needs.recheck.result == 'success'
  detection:
    permissions:
      contents: read
    pre-steps:
      - name: Connect private inference tailnet
        uses: tailscale/github-action@064b10558093f38325e838ddea35486bdc6b1d5c # v4.4.0
        env:
          XDG_RUNTIME_DIR: ${{ runner.temp }}/lean-tailscale
        with:
          oauth-client-id: ${{ secrets.TS_OAUTH_CLIENT_ID }}
          oauth-secret: ${{ secrets.TS_OAUTH_CLIENT_SECRET }}
          tags: tag:github-bot
          version: '1.102.4'
          use-cache: 'false'
          log-mode: quiet
      - name: Resolve tailnet names inside the AWF sandbox
        # AWF's proxy uses the runner's upstream DNS, which cannot see MagicDNS. PREROUTING only
        # sees container traffic, so send container DNS to Tailscale's resolver (it forwards public
        # names upstream). The domain allowlist and tailnet ACL still decide reachability.
        run: |
          for p in udp tcp; do
            sudo iptables -t nat -I PREROUTING -p "$p" --dport 53 -j DNAT --to-destination 100.100.100.100:53
          done
      - name: Wait for dense Qwen (cold start up to 600 s)
        env:
          OMNIROUTE_API_KEY: ${{ secrets.OMNIROUTE_API_KEY }}
        run: |
          code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 600             -H "Authorization: Bearer $OMNIROUTE_API_KEY" -H 'Content-Type: application/json'             -d '{"model":"lean-qwen27b","max_tokens":1,"messages":[{"role":"user","content":"ok"}]}'             https://ai-server.tail67b2d4.ts.net/v1/chat/completions)
          echo "warm-up HTTP $code"
          test "$code" = 200

timeout-minutes: 20
max-turns: 20
---
Repair the failing disposable fixture or requested review changes for this revision-bound triggering PR.
Read the triggering review when present. The trusted CI/review trigger and deterministic reserve job consumed the PR's only
automatic repair attempt before inference. Run npm test to reproduce it. Only edit
fixture/math.js. Run npm test again and publish exactly one correction through
push-to-pull-request-branch. Do not modify tests, configuration, labels or protections.
For an agent:review-changes label event, fetch the latest github-actions[bot] change-request
review on this exact head and address its concrete findings even when current tests pass.
Also run the acceptance block from the issue the PR closes (the number after "Closes #" in
the PR body; read it with the GitHub issue tools): save it as qa-acceptance.test.mjs
in the repository root, run node --test qa-acceptance.test.mjs, then delete the file.
If tests or acceptance still fail, stop. The worker receives no GitHub publisher token.
