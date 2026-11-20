#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SITE="$ROOT/site"
[[ -f "$SITE/ffmpeg-ubuntu.gpg" ]] || { echo "Missing signed APT site" >&2; exit 1; }
gpgv --keyring "$SITE/ffmpeg-ubuntu.gpg" "$SITE/dists/resolute/InRelease"

# Check both architectures with APT itself, but do not install packages.
for arch in amd64 arm64; do
  TMP="$(mktemp -d)"
  mkdir -p "$TMP/lists/partial"
  printf 'deb [signed-by=%s] file:%s resolute main\n' \
    "$SITE/ffmpeg-ubuntu.gpg" "$SITE" > "$TMP/sources.list"
  apt-get \
    -o APT::Architecture="$arch" \
    -o APT::Architectures="$arch" \
    -o Dir::Etc::sourcelist="$TMP/sources.list" \
    -o Dir::Etc::sourceparts=- \
    -o Dir::State::Lists="$TMP/lists" \
    -o APT::Get::List-Cleanup=0 \
    update
  rm -rf "$TMP"
done
echo "APT verified Release metadata and package indexes for amd64 and arm64"
