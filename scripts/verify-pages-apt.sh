#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SITE="$ROOT/site"
[[ -s "$SITE/ffmpeg-ubuntu.gpg" ]] || { echo "Missing public APT signing key" >&2; exit 1; }

# Independently verify each signed release, then let APT parse both indexes
# with the target architecture selected; no package installation is needed.
for suite in noble resolute stonking; do
  gpgv --keyring "$SITE/ffmpeg-ubuntu.gpg" "$SITE/dists/$suite/InRelease"
  for arch in amd64 arm64; do
    index="$SITE/dists/$suite/main/binary-$arch/Packages"
    [[ -s "$index" && -s "$index.gz" ]] || {
      echo "Missing APT package index for $suite/$arch" >&2; exit 1;
    }
    grep -q '^Package: ffmpeg$' "$index" || {
      echo "No ffmpeg package in $suite/$arch" >&2; exit 1;
    }
    tmp="$(mktemp -d)"
    mkdir -p "$tmp/lists/partial"
    printf 'deb [signed-by=%s] file:%s %s main\n' \
      "$SITE/ffmpeg-ubuntu.gpg" "$SITE" "$suite" > "$tmp/sources.list"
    apt-get \
      -o "APT::Architecture=$arch" \
      -o "APT::Architectures=$arch" \
      -o "Dir::Etc::sourcelist=$tmp/sources.list" \
      -o Dir::Etc::sourceparts=- \
      -o "Dir::State::Lists=$tmp/lists" \
      -o APT::Get::List-Cleanup=0 \
      update
    rm -rf "$tmp"
  done
done
echo "Validated signed APT releases and six Ubuntu architecture indexes"
