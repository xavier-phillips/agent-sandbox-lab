#!/usr/bin/env bash
set -euo pipefail
config="$GITHUB_WORKSPACE/.github/awf-boundary-probe.json"
workspace=$(mktemp -d "$RUNNER_TEMP/awf-boundary-workspace.XXXXXX")
private=$(mktemp -d /var/tmp/awf-boundary-private.XXXXXX)
export HOST_PRIVATE_FILE="$private/host-only"
export HOST_HOME_CANARY="$HOME/.awf-boundary-home-$RANDOM-$RANDOM"
export AWF_PROBE_VISIBLE=synthetic-visible-control
export AWF_PROBE_SECRET=synthetic-excluded-value
printf 'synthetic host-only file\n' > "$HOST_PRIVATE_FILE"
printf 'synthetic host-home file\n' > "$HOST_HOME_CANARY"
chmod 755 "$private"
chmod 644 "$HOST_PRIVATE_FILE" "$HOST_HOME_CANARY"
test -r "$HOST_PRIVATE_FILE" && test -r "$HOST_HOME_CANARY"
cp "$config" "$workspace/awf-config.json"
cat > "$workspace/assert-boundaries.sh" <<'PROBE'
#!/usr/bin/env bash
set -euo pipefail
test "$AWF_PROBE_VISIBLE" = synthetic-visible-control
test -z "${AWF_PROBE_SECRET+x}"
echo 'PASS: env-all positive control and excluded synthetic variable'
for path in "$HOST_PRIVATE_FILE" "/host$HOST_PRIVATE_FILE" "$HOST_HOME_CANARY" "/host$HOST_HOME_CANARY"; do
  test ! -r "$path"
done
echo 'PASS: synthetic private file and unlisted host-home canary are unreadable'
for socket in /var/run/docker.sock /run/docker.sock /host/var/run/docker.sock /host/run/docker.sock; do
  test ! -S "$socket"
done
echo 'PASS: known host Docker socket paths are absent'
printf 'written\n' > probe-write
test "$(cat probe-write)" = written
echo 'PASS: disposable workspace is writable'
curl --fail --silent --show-error --max-time 20 https://api.github.com/zen >/dev/null
echo 'PASS: explicitly allowed documented GitHub API endpoint responds'
curl_status=0
curl_codes=$(curl --fail --silent --show-error --max-time 15 --output /dev/null --write-out 'http=%{http_code} connect=%{http_connect}' https://blocked-awf-probe.invalid/ 2>denied.err) || curl_status=$?
printf 'Denied request: curl_exit=%s %s\n' "$curl_status" "$curl_codes"
head -c 2048 denied.err >&2
printf '\n' >&2
if [ "$curl_status" -eq 0 ]; then
  echo 'FAIL: denied reserved hostname unexpectedly succeeded' >&2
  exit 1
fi
printf '%s\n' "$curl_codes" | grep -Eq '(^http=403 | connect=403$)'
echo 'PASS: reserved denied hostname returns proxy 403; DNS failure alone is insufficient'
PROBE
export GITHUB_WORKSPACE="$workspace"
cd "$workspace"
"$HOME/.local/bin/awf" --config "$workspace/awf-config.json" --container-workdir "$workspace" -- /bin/bash "$workspace/assert-boundaries.sh"
test "$(cat "$workspace/probe-write")" = written
echo 'PASS: host observes the disposable workspace write; AWF command exited successfully'
