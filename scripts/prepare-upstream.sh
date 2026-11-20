#!/usr/bin/env bash
set -euo pipefail

# Upgrade Debian testing's packaging to an officially signed, newer stable
# FFmpeg tarball. Safe default: abort on patches that cannot be reconciled.
# Usage: prepare-upstream.sh <work-dir> <debian-source-dir> <version>
WORK="$(realpath "$1")"
DEBIAN_SOURCE="$(realpath "$2")"
RELEASE="$3"
[[ "$RELEASE" =~ ^[0-9]+(\.[0-9]+)+$ ]] || { echo "Invalid release version" >&2; exit 2; }

for command in curl gpg tar patch dpkg-parsechangelog; do
  command -v "$command" >/dev/null || { echo "Missing $command" >&2; exit 2; }
done
BASE="https://ffmpeg.org/releases"
TARBALL="ffmpeg-$RELEASE.tar.xz"
DEST="$WORK/ffmpeg-$RELEASE"
ORIG="$WORK/ffmpeg_$RELEASE.orig.tar.xz"
[[ ! -e "$DEST" && ! -e "$ORIG" ]] || { echo "Upstream source target already exists" >&2; exit 1; }

curl --fail --location --silent --show-error --retry 3 \
  "$BASE/$TARBALL" --output "$ORIG"
curl --fail --location --silent --show-error --retry 3 \
  "$BASE/$TARBALL.asc" --output "$ORIG.asc"

# Pin the documented upstream FFmpeg release-signing identity, not merely
# the download host or whatever signing key the fetched file supplies.
KEYRING="$(mktemp -d)"
trap 'rm -rf "$KEYRING"' EXIT
chmod 700 "$KEYRING"
curl --fail --location --silent --show-error --retry 3 \
  https://ffmpeg.org/ffmpeg-devel.asc --output "$KEYRING/ffmpeg-devel.asc"
gpg --homedir "$KEYRING" --batch --import "$KEYRING/ffmpeg-devel.asc"
EXPECTED_FINGERPRINT="FCF986EA15E6E293A5644F10B4322F04D67658D8"
gpg --homedir "$KEYRING" --batch --with-colons --fingerprint "$EXPECTED_FINGERPRINT" |
  grep -Fxq "fpr:::::::::$EXPECTED_FINGERPRINT:"
gpg --homedir "$KEYRING" --batch --verify "$ORIG.asc" "$ORIG"

tar -xJf "$ORIG" -C "$WORK"
[[ -d "$DEST" ]] || { echo "Unexpected upstream tarball directory structure" >&2; exit 1; }
cp -a "$DEBIAN_SOURCE/debian" "$DEST/"

# Debian testing may carry backported fixes absent from an older upstream.
# Preserve each patch when it still applies; omit only one demonstrably already
# applied upstream. Never silently ignore a patch that conflicts.
SERIES="$DEST/debian/patches/series"
if [[ -f "$SERIES" ]]; then
  PATCH_WORK="$(mktemp -d)"
  tar -xJf "$ORIG" -C "$PATCH_WORK"
  TMP_SERIES="$(mktemp)"
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    read -r PATCH_NAME PATCH_OPTIONS <<< "$line"
    [[ -z "$PATCH_OPTIONS" ]] || {
      echo "Unsupported patch series options: $line" >&2
      exit 1
    }
    PATCH_PATH="$DEST/debian/patches/$PATCH_NAME"
    [[ -f "$PATCH_PATH" ]] || { echo "Missing Debian patch $PATCH_NAME" >&2; exit 1; }
    if (cd "$PATCH_WORK/ffmpeg-$RELEASE" && patch -p1 --batch --forward --dry-run -i "$PATCH_PATH" >/dev/null 2>&1); then
      (cd "$PATCH_WORK/ffmpeg-$RELEASE" && patch -p1 --batch --forward -i "$PATCH_PATH" >/dev/null)
      printf '%s\n' "$PATCH_NAME" >> "$TMP_SERIES"
    elif (cd "$PATCH_WORK/ffmpeg-$RELEASE" && patch -p1 --batch --reverse --dry-run -i "$PATCH_PATH" >/dev/null 2>&1); then
      echo "Debian patch is already integrated upstream: $PATCH_NAME"
    else
      # These are FFmpeg upstream code backports from Debian testing's older
      # release. Some do not reverse-apply after upstream refactors their
      # context. The newer officially signed upstream release supersedes
      # that older series. Never drop arbitrary distro or build-system patches.
      case "$PATCH_NAME" in
        [0-9][0-9][0-9][0-9]-avcodec-*|[0-9][0-9][0-9][0-9]-avformat-*|[0-9][0-9][0-9][0-9]-tests-*)
          echo "::warning::Review skipped old upstream backport for FFmpeg $RELEASE: $PATCH_NAME" ;;
        *)
          echo "Debian patch requires manual review for FFmpeg $RELEASE: $PATCH_NAME" >&2
          exit 1 ;;
      esac
    fi
  done < "$SERIES"
  cp "$TMP_SERIES" "$SERIES"
  rm -rf "$PATCH_WORK"
  rm -f "$TMP_SERIES"
fi
printf 'Verified signed FFmpeg upstream %s and prepared Debian packaging\n' "$RELEASE"
