#!/usr/bin/env bash
set -euo pipefail
config="$GITHUB_WORKSPACE/.github/awf-boundary-probe.json"
workspace=$(mktemp -d "$RUNNER_TEMP/awf-boundary-workspace.XXXXXX")
private=$(mktemp -d /var/tmp/awf-boundary-private.XXXXXX)
export HOST_PRIVATE_FILE="$private/host-only"
export HOST_HOME_CANARY="$HOME/.awf-boundary-home-$RANDOM-$RANDOM"
export AWF_PROBE_VISIBLE=synthetic-visible-control
export AWF_PROBE_SECRET=synthetic-excluded-value
HOST_ALLOWED_IP=$(getent ahostsv4 api.github.com | awk 'NR == 1 {print $1}')
[[ "$HOST_ALLOWED_IP" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]
export HOST_ALLOWED_IP
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
direct_status=0
curl --fail --silent --show-error --noproxy '*' --resolve "api.github.com:443:$HOST_ALLOWED_IP" --connect-timeout 3 --max-time 5 https://api.github.com/zen >/dev/null 2>direct.err || direct_status=$?
printf 'Direct route: curl_exit=%s\n' "$direct_status"
head -c 2048 direct.err >&2
printf '\n' >&2
case "$direct_status" in
  7|28) echo 'PASS: direct route to the allowed endpoint is blocked at the network layer' ;;
  *) echo 'FAIL: direct route must fail with connection refusal or timeout' >&2; exit 1 ;;
esac
curl_status=0
curl_codes=$(curl --fail --silent --show-error --proxy "$HTTP_PROXY" --max-time 15 --output /dev/null --write-out 'http=%{http_code} connect=%{http_connect}' http://blocked-awf-probe.invalid/ 2>denied.err) || curl_status=$?
printf 'Denied request: curl_exit=%s %s\n' "$curl_status" "$curl_codes"
head -c 2048 denied.err >&2
printf '\n' >&2
if [ "$curl_status" -eq 0 ]; then
  echo 'FAIL: denied reserved hostname unexpectedly succeeded' >&2
  exit 1
fi
printf '%s\n' "$curl_codes" | grep -Eq '^http=403 connect=000$'
echo 'PASS: reserved denied hostname returns proxy 403; DNS failure alone is insufficient'
PROBE
export GITHUB_WORKSPACE="$workspace"
cd "$workspace"
"$HOME/.local/bin/awf" --config "$workspace/awf-config.json" --container-workdir "$workspace" -- /bin/bash "$workspace/assert-boundaries.sh"
test "$(cat "$workspace/probe-write")" = written
echo 'PASS: host observes the disposable workspace write; AWF command exited successfully'
