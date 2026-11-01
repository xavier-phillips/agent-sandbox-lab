---
description: One native PR-event CI repair with a deterministic cumulative budget
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review, labeled]
  pull_request_review:
    types: [submitted]
permissions:
  contents: read
  pull-requests: read
engine:
  id: pi
  version: '1.4.0'
  bare: true
  model: openai/QUALIFIED_ROUTE_ID
  model-provider: openai
  env:
    OPENAI_BASE_URL: https://omniroute.example.invalid/v1
    CODEX_API_KEY: ${{ secrets.OMNIROUTE_API_KEY }}
    OPENAI_API_KEY: ${{ secrets.OMNIROUTE_API_KEY }}
network:
  allowed: [defaults, omniroute.example.invalid]
tools:
  bash: true
  github:
    toolsets: [pull_requests, repos]
safe-outputs:
  steps:
    - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
      with:
        ref: ${{ github.event.pull_request.base.sha }}
        persist-credentials: false
    - name: Fence live PR and default-base revision inside native publisher job
      uses: actions/github-script@3a2844b7e9c422d3c10d287c895573f7108da1b3
      with:
        script: |
          const {guard} = require('./.github/scripts/guard.cjs');
          await guard({github, context}, false);
  threat-detection:
    continue-on-error: false
    engine:
      id: codex
      model: openai/QUALIFIED_REVIEW_ROUTE_ID
      model-provider: openai
      env:
        OPENAI_BASE_URL: https://omniroute.example.invalid/v1
        CODEX_API_KEY: ${{ secrets.OMNIROUTE_API_KEY }}
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
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
        with:
          ref: ${{ github.event.pull_request.head.sha }}
          persist-credentials: false
      - uses: actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1
        with:
          node-version: '24'
      - run: npm test
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
            await guard({github, context}, true);
  agent:
    needs: [fixture-ci, reserve]
    if: always() && needs.reserve.result == 'success'
  recheck:
    needs: [agent, detection]
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
    if: needs.recheck.result == 'success'
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
If tests still fail, stop. The worker receives no GitHub publisher token.
