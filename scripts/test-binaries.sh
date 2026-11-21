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
    apt-get install -y --no-install-recommends dpkg-dev binutils
    mkdir -p /tmp/aptrepo
    cp /packages/*.deb /tmp/aptrepo/
    cd /tmp/aptrepo
    dpkg-scanpackages . /dev/null > Packages
    printf "deb [trusted=yes] file:/tmp/aptrepo ./\n" > /etc/apt/sources.list.d/ffmpeg-local.list
    apt-get update -qq
    apt-get install -y --no-install-recommends ffmpeg ffplay
    ffmpeg -hide_banner -version | grep -Eq "^ffmpeg version (n)?[0-9]+\."
    ffprobe -hide_banner -version | grep -Eq "^ffprobe version (n)?[0-9]+\."
    ffmpeg -hide_banner -loglevel error -f lavfi -i "sine=frequency=440:duration=0.1" \
      -ac 1 -ar 8000 -f wav -y /tmp/smoke.wav
    test -s /tmp/smoke.wav
    # Check all installed ELF files belonging to the locally built packages,
    # not only binaries whose startup tests happen to exercise their libraries.
    checked=0
    for deb in /packages/*.deb; do
      package="$(dpkg-deb -f "$deb" Package)"
      if [[ "$(dpkg-query -W -f="\\${db:Status-Status}" "$package" 2>/dev/null || true)" != "installed" ]]; then
        continue
      fi
      while IFS= read -r path; do
        [[ -f "$path" ]] || continue
        readelf -h "$path" >/dev/null 2>&1 || continue
        if [[ "$(readelf -d "$path" 2>/dev/null)" != *"(NEEDED)"* ]]; then
          continue
        fi
        if ! libraries="$(ldd "$path" 2>&1)"; then
          echo "Unable to resolve shared libraries for $package: $path" >&2
          echo "$libraries" >&2
          exit 1
        fi
        if [[ "$libraries" == *"not found"* ]]; then
          echo "Missing shared libraries in $package: $path" >&2
          echo "$libraries" >&2
          exit 1
        fi
        checked=$((checked + 1))
      done < <(dpkg -L "$package")
    done
    [[ "$checked" -gt 0 ]] || { echo "No installed ELF files were checked" >&2; exit 1; }
    echo "Verified shared libraries for $checked installed ELF files"
  '
