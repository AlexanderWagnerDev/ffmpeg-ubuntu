#!/usr/bin/env bash
set -euo pipefail

# Test apt dependency resolution and basic runtime behavior in a clean native
# target Ubuntu container, before any package is allowed into the public repo.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERIES="${1:-}"
ARCH="${2:-}"
case "$SERIES" in
  noble) RELEASE=24.04 ;;
  resolute) RELEASE=26.04 ;;
  stonking) RELEASE=26.10 ;;
  *) echo "Usage: $0 noble|resolute|stonking amd64|arm64" >&2; exit 2 ;;
esac
[[ "$ARCH" == amd64 || "$ARCH" == arm64 ]] || {
  echo "Architecture must be amd64 or arm64" >&2; exit 2;
}
BINARIES="$ROOT/binaries/$SERIES/$ARCH"
shopt -s nullglob
packages=("$BINARIES"/*.deb)
[[ "${#packages[@]}" -gt 0 ]] || { echo "No binary packages to test" >&2; exit 1; }

docker run --rm \
  --mount "type=bind,src=$BINARIES,dst=/packages,readonly" \
  --env DEBIAN_FRONTEND=noninteractive \
  "ubuntu:$RELEASE" bash -euo pipefail -c '
    apt-get update -qq
    apt-get install -y --no-install-recommends dpkg-dev
    mkdir -p /tmp/aptrepo
    cp /packages/*.deb /tmp/aptrepo/
    cd /tmp/aptrepo
    dpkg-scanpackages . /dev/null > Packages
    printf "deb [trusted=yes] file:/tmp/aptrepo ./\n" > /etc/apt/sources.list.d/ffmpeg-local.list
    apt-get update -qq
    apt-get install -y --no-install-recommends ffmpeg
    ffmpeg -hide_banner -version | grep -Eq "^ffmpeg version (n)?[0-9]+\."
    ffprobe -hide_banner -version | grep -Eq "^ffprobe version (n)?[0-9]+\."
    ffmpeg -hide_banner -loglevel error -f lavfi -i "sine=frequency=440:duration=0.1" \
      -ac 1 -ar 8000 -f wav -y /tmp/smoke.wav
    test -s /tmp/smoke.wav
  '
