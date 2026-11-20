#!/usr/bin/env bash
set -euo pipefail

# Assemble a single GitHub Pages deployment containing both amd64 and arm64.
# Runs only in the environment-protected signing job.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INPUT_DIR="${1:-}"
[[ -n "$INPUT_DIR" && -d "$INPUT_DIR/amd64" && -d "$INPUT_DIR/arm64" ]] || {
  echo "Usage: $0 <directory-containing-amd64-and-arm64-subdirectories>" >&2; exit 2;
}
for tool in dpkg-deb dpkg-scanpackages apt-ftparchive gpg gpgv gzip; do
  command -v "$tool" >/dev/null || { echo "Missing tool: $tool" >&2; exit 2; }
done
[[ -n "${PAGES_APT_GPG_PRIVATE_KEY_B64:-}" && -n "${PAGES_APT_GPG_FINGERPRINT:-}" ]] || {
  echo "Missing protected APT signing environment secrets" >&2; exit 1;
}
SITE="$ROOT/site"
[[ ! -e "$SITE" ]] || { echo "Site folder already exists" >&2; exit 1; }
mkdir -p "$SITE/pool/main/f/ffmpeg" "$SITE/dists/resolute/main/binary-amd64" \
  "$SITE/dists/resolute/main/binary-arm64"

shopt -s nullglob
expected_ffmpeg_version=""
ffmpeg_arch_count=0
for arch in amd64 arm64; do
  packages=("$INPUT_DIR/$arch"/*.deb)
  [[ "${#packages[@]}" -gt 0 ]] || { echo "No .deb files for $arch" >&2; exit 1; }
  for deb in "${packages[@]}"; do
    binary_arch="$(dpkg-deb -f "$deb" Architecture)"
    [[ "$binary_arch" == "$arch" || "$binary_arch" == all ]] || {
      echo "Wrong package architecture $binary_arch in $deb" >&2; exit 1;
    }
    source="$(dpkg-deb -f "$deb" Source 2>/dev/null || true)"
    source="${source%% *}"
    package="$(dpkg-deb -f "$deb" Package)"
    if [[ "$package" == ffmpeg && "$binary_arch" == "$arch" ]]; then
      version="$(dpkg-deb -f "$deb" Version)"
      if [[ -n "$expected_ffmpeg_version" && "$version" != "$expected_ffmpeg_version" ]]; then
        echo "FFmpeg package versions differ between amd64 and arm64" >&2; exit 1;
      fi
      expected_ffmpeg_version="$version"
      ffmpeg_arch_count=$((ffmpeg_arch_count + 1))
    fi
    [[ "$source" == ffmpeg || ( -z "$source" && "$package" == ffmpeg ) ]] || {
      echo "Unexpected upstream source for $package: $source" >&2; exit 1;
    }
    destination="$SITE/pool/main/f/ffmpeg/$(basename "$deb")"
    if [[ -f "$destination" ]]; then
      # Architecture-independent binaries may occur twice. Both must match.
      cmp -s "$deb" "$destination" || {
        echo "Conflicting architecture-independent binary: $destination" >&2; exit 1;
      }
    else
      cp -- "$deb" "$destination"
    fi
  done
done
[[ "$ffmpeg_arch_count" -eq 2 ]] || {
  echo "Exactly one ffmpeg binary per architecture is required" >&2; exit 1;
}

cd "$SITE"
touch .nojekyll
for arch in amd64 arm64; do
  index="dists/resolute/main/binary-$arch/Packages"
  dpkg-scanpackages --arch "$arch" pool /dev/null > "$index"
  grep -q '^Package: ffmpeg$' "$index" || {
    echo "Missing ffmpeg in $arch APT index" >&2; exit 1;
  }
  gzip -n -9 -c "$index" > "$index.gz"
done

cat > release-config.conf <<'CONF'
APT::FTPArchive::Release {
  Origin "AlexanderWagnerDev";
  Label "FFmpeg for Ubuntu";
  Suite "resolute";
  Codename "resolute";
  Version "26.04";
  Architectures "amd64 arm64";
  Components "main";
  Description "FFmpeg 9 Ubuntu 26.04 amd64/arm64 packages";
};
CONF
apt-ftparchive -c release-config.conf release dists/resolute > dists/resolute/Release
rm release-config.conf

umask 077
mkdir -p "$HOME/.gnupg"
printf '%s' "$PAGES_APT_GPG_PRIVATE_KEY_B64" | base64 --decode | gpg --batch --import
gpg --batch --list-secret-keys "$PAGES_APT_GPG_FINGERPRINT" >/dev/null
gpg --batch --export "$PAGES_APT_GPG_FINGERPRINT" > ffmpeg-ubuntu.gpg
gpg --armor --batch --export "$PAGES_APT_GPG_FINGERPRINT" > ffmpeg-ubuntu.asc
[[ -s ffmpeg-ubuntu.gpg && -s ffmpeg-ubuntu.asc ]] || {
  echo "Unable to export the public APT signing key" >&2; exit 1;
}
gpg --batch --yes --pinentry-mode loopback --default-key "$PAGES_APT_GPG_FINGERPRINT" \
  --clearsign -o dists/resolute/InRelease dists/resolute/Release
gpg --batch --yes --pinentry-mode loopback --default-key "$PAGES_APT_GPG_FINGERPRINT" \
  --armor --detach-sign -o dists/resolute/Release.gpg dists/resolute/Release
gpgv --keyring ./ffmpeg-ubuntu.gpg dists/resolute/InRelease

cat > index.html <<'HTML'
<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FFmpeg for Ubuntu — APT Packages</title>
</head>
<body>
<main>
<h1>FFmpeg for Ubuntu</h1>
<p>Signed FFmpeg 9 APT packages for Ubuntu 26.04 (resolute): AMD64 and ARM64.</p>
<p><a href="ffmpeg-ubuntu.gpg">Download APT repository public signing key</a></p>
<p><a href="https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu">Source, security guidance and installation instructions</a></p>
</main>
</body>
</html>
HTML

# APT verifies signatures as the unprivileged _apt user. In particular,
# signing keys and release metadata must be world-readable on the Pages site.
find "$SITE" -type d -exec chmod 0755 {} +
find "$SITE" -type f -exec chmod 0644 {} +

bytes="$(du -sb "$SITE" | cut -f1)"
if (( bytes > 900 * 1024 * 1024 )); then
  echo "Pages APT site too large: $bytes bytes (>900 MiB), use external hosting" >&2
  exit 1
fi
echo "Generated signed AMD64 + ARM64 APT repository ($bytes bytes)"
