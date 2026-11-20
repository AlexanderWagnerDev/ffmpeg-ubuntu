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
DEBIAN_EPOCH="${DEBIAN_VERSION%%:*}"
DEBIAN_UPSTREAM="${DEBIAN_VERSION#*:}"
DEBIAN_UPSTREAM="${DEBIAN_UPSTREAM%-*}"
UPSTREAM_RELEASE="$(python3 "$ROOT/scripts/latest_release.py")"
echo "Debian testing: $DEBIAN_UPSTREAM; upstream stable: $UPSTREAM_RELEASE"
if dpkg --compare-versions "$DEBIAN_UPSTREAM" gt "$UPSTREAM_RELEASE"; then
  echo "Debian source is ahead of the latest official stable FFmpeg; refusing prerelease packaging" >&2
  exit 1
fi
if dpkg --compare-versions "$UPSTREAM_RELEASE" gt "$DEBIAN_UPSTREAM"; then
  bash "$ROOT/scripts/prepare-upstream.sh" "$WORK" "$SOURCE_DIR" "$UPSTREAM_RELEASE"
  SOURCE_DIR="$WORK/ffmpeg-$UPSTREAM_RELEASE"
  # A revision of 0 keeps a later official Debian package revision newer.
  DEBIAN_VERSION="$DEBIAN_EPOCH:$UPSTREAM_RELEASE-0"
fi
NEW_VERSION="$(python3 "$ROOT/scripts/package_version.py" "$DEBIAN_VERSION" "$SERIES" "$REVISION")"
# Debian testing may require newer debhelper than Ubuntu 26.04 provides.
# Apply the limited Ubuntu compatibility patch and validate by full builds.
if [[ "$SERIES" == "resolute" ]]; then
  if grep -Fq 'debhelper-compat (= 14)' "$SOURCE_DIR/debian/control"; then
    sed -i 's/debhelper-compat (= 14)/debhelper-compat (= 13)/g' "$SOURCE_DIR/debian/control"
    echo "Using Ubuntu-compatible debhelper level 13"
    python3 "$ROOT/scripts/patch_ubuntu_control.py" "$SOURCE_DIR/debian/control"
  else
    echo "Debian debhelper requirement changed; recheck Ubuntu compatibility" >&2
    exit 1
  fi
fi
export DEBFULLNAME="Alexander Wagner"
export DEBEMAIL="info@alexanderwagnerdev.com"
cd "$SOURCE_DIR"
dch --newversion "$NEW_VERSION" --distribution "$SERIES" --force-distribution \
  "Rebuild stable FFmpeg $UPSTREAM_RELEASE for Ubuntu $SERIES (revision $REVISION)."
# -d skips build-dependency checks for SOURCE generation only.
# Binary builds and runtime dependency tests run separately (Pages or Launchpad).
dpkg-buildpackage -S -sa -us -uc -d

# Only stage files from the newly generated Ubuntu package. apt-get source
# also leaves the ORIGINAL Debian .dsc in WORK; including it would make the
# artifact ambiguous and cause source validation to fail.
shopt -s nullglob
VERSION_NO_EPOCH="${NEW_VERSION#*:}"
DEBIAN_NO_EPOCH="${DEBIAN_VERSION#*:}"
UPSTREAM_VERSION="${DEBIAN_NO_EPOCH%-*}"
ubuntu_dsc="$WORK/ffmpeg_${VERSION_NO_EPOCH}.dsc"
ubuntu_changes="$WORK/ffmpeg_${VERSION_NO_EPOCH}_source.changes"
ubuntu_delta=("$WORK"/ffmpeg_"${VERSION_NO_EPOCH}".debian.tar.*)
orig_archive=("$WORK"/ffmpeg_"${UPSTREAM_VERSION}".orig.tar.*)
if [[ ! -f "$ubuntu_dsc" || ! -f "$ubuntu_changes" ||
      "${#ubuntu_delta[@]}" -ne 1 || "${#orig_archive[@]}" -lt 1 ]]; then
  echo "Missing expected Ubuntu source package artifacts" >&2
  exit 1
fi
artifacts=("$ubuntu_dsc" "$ubuntu_changes" "${ubuntu_delta[@]}" "${orig_archive[@]}")
ubuntu_buildinfo="$WORK/ffmpeg_${VERSION_NO_EPOCH}_source.buildinfo"
if [[ -f "$ubuntu_buildinfo" ]]; then
  artifacts+=("$ubuntu_buildinfo")
fi
cp -- "${artifacts[@]}" "$OUT/"
changes=("$OUT/$(basename "$ubuntu_changes")")
echo "Source package: $NEW_VERSION ($SERIES)"
echo "Unsigned artifacts: $OUT"
if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  {
    echo "version=$NEW_VERSION"
    echo "series=$SERIES"
    echo "changes=${changes[0]}"
  } >> "$GITHUB_OUTPUT"
fi
