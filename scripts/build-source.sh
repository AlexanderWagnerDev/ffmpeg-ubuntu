#!/usr/bin/env bash
set -euo pipefail

# Build an *unsigned* FFmpeg source package. No binary .debs are built here.
# Usage: scripts/build-source.sh <jammy|noble|resolute> [ppa-revision]
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERIES="${1:-}"
REVISION="${2:-1}"
case "$SERIES" in
  jammy|noble|resolute) ;;
  *) echo "Usage: $0 <jammy|noble|resolute> [ppa-revision]" >&2; exit 2 ;;
esac
if [[ ! "$REVISION" =~ ^[1-9][0-9]*$ ]]; then
  echo "PPA revision must be a positive integer" >&2
  exit 2
fi
for tool in apt-get dpkg-parsechangelog dpkg-buildpackage dch python3; do
  command -v "$tool" >/dev/null || { echo "Missing required tool: $tool" >&2; exit 2; }
done

WORK="$ROOT/work/$SERIES"
OUT="$ROOT/dist/$SERIES"
mkdir -p "$WORK" "$OUT"
# Refuse to accidentally mix previously extracted sources or stale artifacts.
if find "$WORK" -mindepth 1 -print -quit | grep -q .; then
  echo "Work directory is not empty: $WORK (remove it explicitly)" >&2
  exit 2
fi
if find "$OUT" -mindepth 1 -print -quit | grep -q .; then
  echo "Output directory is not empty: $OUT (remove it explicitly)" >&2
  exit 2
fi

cd "$WORK"
# This uses ONLY the Debian *source* index configured by setup-build-env.sh.
# It does NOT add any Debian binary repositories to Ubuntu.
apt-get source ffmpeg

mapfile -t source_dirs < <(find "$WORK" -maxdepth 1 -mindepth 1 -type d -name 'ffmpeg-*' | sort)
if [[ "${#source_dirs[@]}" -ne 1 ]]; then
  echo "Expected exactly one extracted ffmpeg source directory" >&2
  exit 1
fi
SOURCE_DIR="${source_dirs[0]}"
DEBIAN_VERSION="$(dpkg-parsechangelog --file "$SOURCE_DIR/debian/changelog" --show-field Version)"
NEW_VERSION="$(python3 "$ROOT/scripts/package_version.py" "$DEBIAN_VERSION" "$SERIES" "$REVISION")"
export DEBFULLNAME="Alexander Wagner"
export DEBEMAIL="info@alexanderwagnerdev.com"
cd "$SOURCE_DIR"
dch --newversion "$NEW_VERSION" --distribution "$SERIES" --force-distribution \
  "Rebuild Debian FFmpeg 9 source for Ubuntu $SERIES (PPA revision $REVISION)."
# -d skips build-dependency checks for SOURCE generation only.
# Actual dependency resolution/builds are the job of Launchpad.
dpkg-buildpackage -S -sa -us -uc -d

shopt -s nullglob
artifacts=("$WORK"/ffmpeg_*.dsc "$WORK"/ffmpeg_*.tar.* "$WORK"/ffmpeg_*_source.changes)
if [[ "${#artifacts[@]}" -lt 3 ]]; then
  echo "Missing expected .dsc, source tarballs, or _source.changes" >&2
  exit 1
fi
cp -- "${artifacts[@]}" "$OUT/"
changes=("$OUT"/ffmpeg_*_source.changes)
if [[ "${#changes[@]}" -ne 1 ]]; then
  echo "Expected exactly one source .changes file" >&2
  exit 1
fi
echo "Source package: $NEW_VERSION ($SERIES)"
echo "Unsigned artifacts: $OUT"
if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  {
    echo "version=$NEW_VERSION"
    echo "series=$SERIES"
    echo "changes=${changes[0]}"
  } >> "$GITHUB_OUTPUT"
fi
