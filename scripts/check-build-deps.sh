#!/usr/bin/env bash
set -euo pipefail

# Resolve FFmpeg's declared source build dependencies using the TARGET Ubuntu
# release, not the GitHub runner's OS. This is not a full binary build.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERIES="${1:-}"
case "$SERIES" in
  jammy) RELEASE=22.04 ;;
  noble) RELEASE=24.04 ;;
  resolute) RELEASE=26.04 ;;
  *) echo "Usage: $0 jammy|noble|resolute" >&2; exit 2 ;;
esac
command -v docker >/dev/null || { echo "Docker is required" >&2; exit 2; }
SOURCE_DIR="$ROOT/dist/$SERIES"
shopt -s nullglob
dsc=("$SOURCE_DIR"/ffmpeg_*.dsc)
[[ "${#dsc[@]}" -eq 1 ]] || { echo "Expected one source .dsc in $SOURCE_DIR" >&2; exit 1; }

# No Debian binaries are introduced; only the target Ubuntu archive is used.
docker run --rm --volume "$SOURCE_DIR:/sources:ro" "ubuntu:$RELEASE" \
  bash -euo pipefail -c '
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y --no-install-recommends dpkg-dev
    apt-get -s build-dep /sources/ffmpeg_*.dsc
  '
