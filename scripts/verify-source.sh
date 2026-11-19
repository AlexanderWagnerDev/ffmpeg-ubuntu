#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERIES="${1:-resolute}"
case "$SERIES" in jammy|noble|resolute) ;; *) echo "Unknown series: $SERIES" >&2; exit 2 ;; esac
OUT="$ROOT/dist/$SERIES"
shopt -s nullglob
dsc=("$OUT"/ffmpeg_*.dsc)
changes=("$OUT"/ffmpeg_*_source.changes)
if [[ "${#dsc[@]}" -ne 1 || "${#changes[@]}" -ne 1 ]]; then
  echo "Expected exactly one .dsc and one source .changes file" >&2
  exit 1
fi
dpkg-source --info "${dsc[0]}" >/dev/null
test "$(sed -n 's/^Distribution: //p' "${changes[0]}")" = "$SERIES" || {
  echo "Unexpected distribution in source .changes" >&2
  exit 1
}
echo "Source archive metadata OK for $SERIES"
