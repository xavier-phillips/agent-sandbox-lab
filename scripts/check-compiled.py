"""Read-only security assertions for the generated workflows; requires PyYAML."""
from pathlib import Path
import json
import yaml

root = Path(__file__).resolve().parents[1]
tailscale_action = "tailscale/github-action@064b10558093f38325e838ddea35486bdc6b1d5c"
def check_tailnet(job):
    assert all(value != "write" for value in job["permissions"].values())
    assert "id-token" not in job["permissions"]
    connections = [step for step in job["steps"] if step.get("uses") == tailscale_action]
    assert len(connections) == 1
    assert connections[0]["env"] == {"XDG_RUNTIME_DIR": "${{ runner.temp }}/lean-tailscale"}
    assert connections[0]["with"] == {
        "oauth-client-id": "${{ secrets.TS_OAUTH_CLIENT_ID }}",
        "oauth-secret": "${{ secrets.TS_OAUTH_CLIENT_SECRET }}",
        "tags": "tag:github-bot", "version": "1.102.4",
        "use-cache": "false", "log-mode": "quiet",
    }
    assert not any(key in job.get("env", {}) for key in ("TS_OAUTH_CLIENT_ID", "TS_OAUTH_CLIENT_SECRET"))
    assert [step for step in job["steps"] if "secrets.TS_OAUTH_CLIENT_SECRET" in str(step)] == connections

canary = yaml.safe_load((root / ".github/workflows/lean-connectivity.yml").read_text(encoding="utf-8"))
assert canary.get("on", canary.get(True)) == {"workflow_dispatch": None}
assert canary["permissions"] == {} and set(canary["jobs"]) == {"connectivity"}
connectivity = canary["jobs"]["connectivity"]
assert connectivity["if"] == "github.actor_id == '141337987'"
assert connectivity["permissions"] == {}
check_tailnet(connectivity)
assert len(connectivity["steps"]) == 2
probe = connectivity["steps"][1]
assert probe["env"] == {"OMNIROUTE_API_KEY": "${{ secrets.OMNIROUTE_API_KEY }}"}
assert "check('/v1/models', 401)" in probe["run"]
assert "check('/v1/models', 200, authenticated=True, models=True)" in probe["run"]
assert "'/api/keys'" in probe["run"] and "check(path, 404, authenticated=True)" in probe["run"]
assert "chat/completions" not in probe["run"] and "/responses" not in probe["run"]
print("Connectivity: manual-only bounded HTTPS canary, key only in probe step, no inference")
policy = yaml.safe_load((root / ".github/workflows/path-policy.yml").read_text(encoding="utf-8"))
assert set(policy.get("on", policy.get(True))) == {"pull_request_target"}
assert policy["permissions"] == {"contents": "read", "pull-requests": "read"}
policy_steps = policy["jobs"]["path-policy"]["steps"]
assert len(policy_steps) == 1 and "checkout" not in str(policy) and "secrets." not in str(policy)
assert "new Set(['fixture/math.js'])" in policy_steps[0]["with"]["script"]
print("Path policy: base-branch pull_request_target check, no PR checkout, no secrets")
ci = yaml.safe_load((root / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
assert ci["permissions"] == {"contents": "read"}
assert "secrets." not in str(ci) and "OPENAI" not in str(ci)
assert all("opencode" not in step.get("run", "") and "gh aw" not in step.get("run", "") for job in ci["jobs"].values() for step in job.get("steps", []))
print("CI: read-only deterministic checks, no provider/publisher secrets or agent commands")
for name in ("work", "repair", "review"):
    workflow = yaml.safe_load((root / f".github/workflows/lean-{name}.lock.yml").read_text(encoding="utf-8"))
    jobs = workflow["jobs"]
    if name in ("repair", "review"):
        assert "vars.LEAN_BOT_TRIAL == 'true'" in jobs["pre_activation"]["if"], name
        def depends_on_pre_activation(job_name, seen=None):
            if job_name == "pre_activation":
                return True
            seen = set() if seen is None else seen
            assert job_name not in seen, (name, job_name, "cyclic job dependency")
            needs = jobs[job_name].get("needs", [])
            needs = [needs] if isinstance(needs, str) else needs
            return any(depends_on_pre_activation(parent, seen | {job_name}) for parent in needs)
        assert all(depends_on_pre_activation(job_name) for job_name in jobs), name
        assert "needs.pre_activation.outputs.activated == 'true'" in jobs["activation"]["if"], name
    gate = {"work": "activation", "repair": "reserve", "review": "policy"}[name]
    assert "vars.LEAN_BOT_TRIAL == 'true'" in jobs[gate]["if"], name
    if name != "work":
        assert f"needs.{gate}.result == 'success'" in jobs["agent"]["if"], name
    agent = jobs["agent"]
    assert not any(job.get("permissions", {}).get("id-token") == "write" for job in jobs.values()), name
    assert [key for key, job in jobs.items() if "secrets.TS_OAUTH_CLIENT_SECRET" in str(job)] == ["agent", "detection"], name
    assert [key for key, job in jobs.items() if tailscale_action in str(job)] == ["agent", "detection"], name
    for job_name in ("agent", "detection"):
        job = jobs[job_name]
        check_tailnet(job)
        execution_steps = [step for step in job["steps"] if step.get("name", "").startswith("Execute")]
        assert len(execution_steps) == 1, (name, job_name)
        run = execution_steps[0]["run"]
        assert all(f"--exclude-env {key}" in run for key in ("ACTIONS_ID_TOKEN_REQUEST_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_URL")), (name, job_name)
        assert "TS_OAUTH_CLIENT_ID" not in str(execution_steps[0]) and "TS_OAUTH_CLIENT_SECRET" not in str(execution_steps[0]), (name, job_name)
        connection_index = next(i for i, step in enumerate(job["steps"]) if step.get("uses") == tailscale_action)
        assert connection_index < job["steps"].index(execution_steps[0]), (name, job_name)
    assert "omniroute.example.invalid" not in str(workflow), name
    assert "https://ai-server.tail67b2d4.ts.net/v1" in str(workflow), name
    assert "QUALIFIED_" not in str(workflow) and "lean-qwen27b" in str(workflow), name
    execution = [step for step in agent["steps"] if step.get("name") == "Execute Pi CLI"]
    assert len(execution) == 1, name
    step = execution[0]
    assert "LEAN_BOT_CI_TRIGGER_TOKEN" not in str(step), name
    assert not any(key in step.get("env", {}) or key in agent.get("env", {}) for key in ("GITHUB_TOKEN", "GH_TOKEN", "GH_AW_GITHUB_TOKEN")), name
    assert all(f"--exclude-env {key}" in step["run"] for key in ("CODEX_API_KEY", "OPENAI_API_KEY")), name
    for job in jobs.values():
        for action in job.get("steps", []):
            if "uses" in action and not action["uses"].startswith("./"):
                assert len(action["uses"].rsplit("@", 1)[-1]) == 40, action["uses"]
    if name in ("repair", "review"):
        assert "recheck" in jobs["safe_outputs"]["needs"], name
        assert "detection" in jobs["recheck"]["needs"], name
        assert "needs.recheck.result == 'success'" in jobs["safe_outputs"]["if"], name
    if name == "repair":
        assert {"activation", "fixture-ci"} <= set(jobs["reserve"]["needs"]), name
        assert "needs.activation.result == 'success'" in jobs["reserve"]["if"], name
        assert "needs.activation.outputs.daily_ai_credits_exceeded != 'true'" in jobs["reserve"]["if"], name
        assert "!cancelled()" in jobs["reserve"]["if"], name
        assert "github.event.label.name == 'agent:review-changes'" in jobs["reserve"]["if"], name
        processor = next(step for step in jobs["safe_outputs"]["steps"] if step.get("id") == "process_safe_outputs")
        policy = json.loads(processor["env"]["GH_AW_SAFE_OUTPUTS_HANDLER_CONFIG"])["push_to_pull_request_branch"]
        assert policy["signed_commits"] is False and policy["fallback_as_pull_request"] is False, name
    if name in ("work", "repair"):
        processor = next(step for step in jobs["safe_outputs"]["steps"] if step.get("id") == "process_safe_outputs")
        handler = "create_pull_request" if name == "work" else "push_to_pull_request_branch"
        policy = json.loads(processor["env"]["GH_AW_SAFE_OUTPUTS_HANDLER_CONFIG"])[handler]
        assert policy["github-token"] == "${{ secrets.LEAN_BOT_CI_TRIGGER_TOKEN }}", name
        assert [key for key, job in jobs.items() if "secrets.LEAN_BOT_CI_TRIGGER_TOKEN" in str(job)] == ["agent", "safe_outputs"], name
        bindings = [step for step in agent["steps"] if "secrets.LEAN_BOT_CI_TRIGGER_TOKEN" in str(step)]
        assert {step["name"] for step in bindings} == {"Generate Safe Outputs Config", "Redact secrets in logs"}, name
        assert all("LEAN_BOT_CI_TRIGGER_TOKEN" not in str(step.get("with", {}).get("github-token", "")) for step in agent["steps"]), name
    if name == "review":
        assert [key for key, job in jobs.items() if "secrets.LEAN_BOT_CI_TRIGGER_TOKEN" in str(job)] == ["publish_review"], name
        publisher = jobs["publish_review"]
        assert publisher["permissions"] == {"contents": "read", "pull-requests": "write"}, name
        assert publisher["steps"][-1]["with"]["github-token"] == "${{ secrets.GITHUB_TOKEN }}", name
        assert publisher["steps"][-1]["env"]["REVIEW_REPAIR_TRIGGER_TOKEN"] == "${{ secrets.LEAN_BOT_CI_TRIGGER_TOKEN }}", name
        assert "detection" in publisher["needs"] and "needs.detection.result == 'success'" in publisher["if"], name
        script = publisher["steps"][-1]["with"]["script"]
        assert "validateEvidence" in script and "commit_id: expected.head.sha" in script and "await guard" in script, name
        assert "if (review.event === 'REQUEST_CHANGES')" in script and "labels: ['agent:review-changes']" in script, name
    print(f"{name}: compiled credential separation, immutable action refs and publication gates pass")
