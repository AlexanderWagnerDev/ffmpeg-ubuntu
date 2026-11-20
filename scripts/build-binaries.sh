#!/usr/bin/env bash
set -euo pipefail

# Build actual Ubuntu .deb files in a native-architecture target Ubuntu container.
# This process executes packaging scripts: do not inject signing credentials.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERIES="${1:-}"
ARCH="${2:-}"
case "$SERIES" in
  noble) RELEASE=24.04 ;;
  resolute) RELEASE=26.04 ;;
  stonking) RELEASE=26.10 ;;
  *) echo "Usage: $0 noble|resolute|stonking amd64|arm64" >&2; exit 2 ;;
esac
[[ "$ARCH" == "amd64" || "$ARCH" == "arm64" ]] || {
  echo "Architecture must be amd64 or arm64" >&2; exit 2;
}
case "$(uname -m):$ARCH" in
  x86_64:amd64|aarch64:arm64) ;;
  *) echo "Wrong host architecture: $(uname -m) for $ARCH (use a native GitHub runner)" >&2; exit 2 ;;
esac
command -v docker >/dev/null || { echo "Docker is required" >&2; exit 2; }
SOURCE_DIR="$ROOT/dist/$SERIES"
OUTPUT_DIR="$ROOT/binaries/$SERIES/$ARCH"
shopt -s nullglob
dsc=("$SOURCE_DIR"/ffmpeg_*.dsc)
[[ "${#dsc[@]}" -eq 1 ]] || { echo "Expected exactly one FFmpeg .dsc" >&2; exit 1; }
mkdir -p "$OUTPUT_DIR"
[[ -z "$(find "$OUTPUT_DIR" -mindepth 1 -print -quit)" ]] || {
  echo "Output directory must be empty" >&2; exit 1;
}

docker run --rm \
  --mount "type=bind,src=$SOURCE_DIR,dst=/sources,readonly" \
  --mount "type=bind,src=$OUTPUT_DIR,dst=/output" \
  --env DEBIAN_FRONTEND=noninteractive \
  "ubuntu:$RELEASE" bash -euo pipefail -c '
    apt-get update -qq
    apt-get install -y --no-install-recommends build-essential fakeroot dpkg-dev ca-certificates
    apt-get build-dep -y /sources/ffmpeg_*.dsc
    mkdir -p /work
    dpkg-source -x /sources/ffmpeg_*.dsc /work/ffmpeg
    cd /work/ffmpeg
    # Low parallelism avoids overwhelming constrained GitHub runners.
    dpkg-buildpackage --build=binary --unsigned-source --unsigned-changes -j2
    packages=(/work/*.deb)
    if [[ ${#packages[@]} -eq 0 ]]; then
      echo "FFmpeg produced no binary .deb packages" >&2
      exit 1
    fi
    cp -- "${packages[@]}" /output/
  '

packages=("$OUTPUT_DIR"/*.deb)
[[ "${#packages[@]}" -gt 0 ]] || { echo "No .deb files produced" >&2; exit 1; }
for deb in "${packages[@]}"; do
  pkgarch="$(dpkg-deb -f "$deb" Architecture)"
  [[ "$pkgarch" == "$ARCH" || "$pkgarch" == all ]] || {
    echo "Unexpected architecture $pkgarch in $deb" >&2; exit 1;
  }
done
echo "Created ${#packages[@]} FFmpeg binary packages for $SERIES/$ARCH"
