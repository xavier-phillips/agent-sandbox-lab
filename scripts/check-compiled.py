"""Read-only security assertions for the generated workflows; requires PyYAML."""
from pathlib import Path
import json
import yaml

root = Path(__file__).resolve().parents[1]
ci = yaml.safe_load((root / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
assert ci["permissions"] == {"contents": "read"}
assert "secrets." not in str(ci) and "OPENAI" not in str(ci)
assert all("opencode" not in step.get("run", "") and "gh aw" not in step.get("run", "") for job in ci["jobs"].values() for step in job.get("steps", []))
print("CI: read-only deterministic checks, no provider/publisher secrets or agent commands")
for name in ("work", "repair", "review"):
    workflow = yaml.safe_load((root / f".github/workflows/lean-{name}.lock.yml").read_text(encoding="utf-8"))
    jobs = workflow["jobs"]
    gate = {"work": "activation", "repair": "reserve", "review": "policy"}[name]
    assert "vars.LEAN_BOT_TRIAL == 'true'" in jobs[gate]["if"], name
    if name != "work":
        assert f"needs.{gate}.result == 'success'" in jobs["agent"]["if"], name
    agent = jobs["agent"]
    assert all(value != "write" for value in agent.get("permissions", {}).values()), name
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
