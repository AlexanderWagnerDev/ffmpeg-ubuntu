#!/usr/bin/env bash
set -euo pipefail

# Build one independently signed APT suite per Ubuntu version. The input must
# contain the six tested GitHub Actions build artifacts, never mixed together.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INPUT_DIR="${1:-}"
SERIES=(noble resolute stonking)
ARCHES=(amd64 arm64)
[[ -n "$INPUT_DIR" && -d "$INPUT_DIR" ]] || {
  echo "Usage: $0 <downloaded-binary-artifact-directory>" >&2; exit 2;
}
for cmd in dpkg-deb dpkg-scanpackages apt-ftparchive gpg gpgv gzip; do
  command -v "$cmd" >/dev/null || { echo "Missing $cmd" >&2; exit 2; }
done
[[ -n "${PAGES_APT_GPG_PRIVATE_KEY_B64:-}" && -n "${PAGES_APT_GPG_FINGERPRINT:-}" ]] || {
  echo "Missing repository signing secrets" >&2; exit 1;
}
SITE="$ROOT/site"
[[ ! -e "$SITE" ]] || { echo "Refusing to overwrite existing site directory" >&2; exit 1; }
mkdir -p "$SITE"

shopt -s nullglob
for suite in "${SERIES[@]}"; do
  mkdir -p "$SITE/pool/$suite/main/f/ffmpeg"
  target_version=""
  ffmpeg_count=0
  for arch in "${ARCHES[@]}"; do
    INPUT="$INPUT_DIR/ffmpeg-bin-$suite-$arch"
    [[ -d "$INPUT" ]] || { echo "Missing artifact $INPUT" >&2; exit 1; }
    debs=("$INPUT"/*.deb)
    [[ "${#debs[@]}" -gt 0 ]] || { echo "No .deb files in $INPUT" >&2; exit 1; }
    mkdir -p "$SITE/dists/$suite/main/binary-$arch"
    for deb in "${debs[@]}"; do
      package="$(dpkg-deb -f "$deb" Package)"
      package_arch="$(dpkg-deb -f "$deb" Architecture)"
      [[ "$package_arch" == "$arch" || "$package_arch" == all ]] || {
        echo "Wrong architecture $package_arch: $deb" >&2; exit 1;
      }
      source="$(dpkg-deb -f "$deb" Source 2>/dev/null || true)"
      source="${source%% *}"
      [[ "$source" == ffmpeg || ( -z "$source" && "$package" == ffmpeg ) ]] || {
        echo "Unexpected source package $source ($package)" >&2; exit 1;
      }
      if [[ "$package" == ffmpeg && "$package_arch" == "$arch" ]]; then
        version="$(dpkg-deb -f "$deb" Version)"
        if [[ -n "$target_version" && "$target_version" != "$version" ]]; then
          echo "$suite has inconsistent versions: $target_version vs $version" >&2
          exit 1
        fi
        target_version="$version"
        ffmpeg_count=$((ffmpeg_count + 1))
      fi
      destination="$SITE/pool/$suite/main/f/ffmpeg/$(basename "$deb")"
      if [[ -e "$destination" ]]; then
        if [[ "$package_arch" == "all" ]]; then
          # Architecture-independent packages are rebuilt for both native
          # architectures and can differ in build metadata. Publish a single
          # copy, but never mix package versions.
          existing_version="$(dpkg-deb -f "$destination" Version)"
          new_version="$(dpkg-deb -f "$deb" Version)"
          [[ "$existing_version" == "$new_version" ]] || {
            echo "Conflicting architecture-independent versions for $destination: $existing_version vs $new_version" >&2
            exit 1
          }
        else
          cmp -s "$deb" "$destination" || {
            echo "Conflicting architecture-dependent package $destination" >&2; exit 1;
          }
        fi
      else
        cp -- "$deb" "$destination"
      fi
    done
  done
  [[ "$ffmpeg_count" -eq 2 ]] || { echo "Expected AMD64 and ARM64 ffmpeg for $suite" >&2; exit 1; }
  for arch in "${ARCHES[@]}"; do
    index="$SITE/dists/$suite/main/binary-$arch/Packages"
    (cd "$SITE" && dpkg-scanpackages --arch "$arch" "pool/$suite" /dev/null) > "$index"
    grep -q '^Package: ffmpeg$' "$index" || {
      echo "No ffmpeg package in $suite/$arch package index" >&2; exit 1;
    }
    gzip -n -9 -c "$index" > "$index.gz"
  done
done

cd "$SITE"
touch .nojekyll
umask 077
mkdir -p "$HOME/.gnupg"
printf '%s' "$PAGES_APT_GPG_PRIVATE_KEY_B64" | base64 --decode | gpg --batch --import
gpg --batch --list-secret-keys "$PAGES_APT_GPG_FINGERPRINT" >/dev/null
gpg --batch --export "$PAGES_APT_GPG_FINGERPRINT" > ffmpeg-ubuntu.gpg
gpg --armor --batch --export "$PAGES_APT_GPG_FINGERPRINT" > ffmpeg-ubuntu.asc
test -s ffmpeg-ubuntu.gpg
test -s ffmpeg-ubuntu.asc

for suite in "${SERIES[@]}"; do
  case "$suite" in
    noble) version=24.04 ;;
    resolute) version=26.04 ;;
    stonking) version=26.10 ;;
    *) exit 2 ;;
  esac
  config="$(mktemp)"
  cat > "$config" <<CONF
APT::FTPArchive::Release {
  Origin "AlexanderWagnerDev";
  Label "FFmpeg for Ubuntu";
  Suite "$suite";
  Codename "$suite";
  Version "$version";
  Architectures "amd64 arm64";
  Components "main";
  Description "FFmpeg for Ubuntu $version AMD64 and ARM64";
};
CONF
  apt-ftparchive -c "$config" release "dists/$suite" > "dists/$suite/Release"
  rm -f "$config"
  gpg --batch --yes --pinentry-mode loopback --default-key "$PAGES_APT_GPG_FINGERPRINT" \
    --clearsign -o "dists/$suite/InRelease" "dists/$suite/Release"
  gpg --batch --yes --pinentry-mode loopback --default-key "$PAGES_APT_GPG_FINGERPRINT" \
    --armor --detach-sign -o "dists/$suite/Release.gpg" "dists/$suite/Release"
  gpgv --keyring ./ffmpeg-ubuntu.gpg "dists/$suite/InRelease"
done

cat > index.html <<'HTML'
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>FFmpeg for Ubuntu — Signed APT packages</title></head><body><main>
<h1>FFmpeg for Ubuntu</h1>
<p>Latest stable FFmpeg community packages for Ubuntu 24.04 LTS, 26.04 LTS and 26.10 (AMD64 and ARM64).</p>
<p><a href="ffmpeg-ubuntu.gpg">APT signing public key</a> ·
<a href="https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/blob/main/docs/INSTALLATION.md">Installation instructions</a></p>
</main></body></html>
HTML

# APT downloads the index as an unprivileged user.
find "$SITE" -type d -exec chmod 0755 {} +
find "$SITE" -type f -exec chmod 0644 {} +
bytes="$(du -sb "$SITE" | cut -f1)"
if (( bytes > 900 * 1024 * 1024 )); then
  echo "APT repository exceeds GitHub Pages artifact size budget: $bytes bytes" >&2
  exit 1
fi
printf 'Signed all three Ubuntu suites for AMD64 and ARM64 (%s bytes)\n' "$bytes"
