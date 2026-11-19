#!/usr/bin/env bash
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root: sudo bash scripts/setup-build-env.sh" >&2
  exit 2
fi
. /etc/os-release
if [[ "$ID" != ubuntu ]]; then
  echo "This setup is intended for Ubuntu build runners only" >&2
  exit 2
fi

apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  debian-archive-keyring devscripts debhelper dpkg-dev build-essential ca-certificates
test -s /usr/share/keyrings/debian-archive-keyring.gpg

# Import only *source* package metadata, never binary Debian repositories.
cat > /etc/apt/sources.list.d/ffmpeg-debian-source.sources <<'SOURCES'
Types: deb-src
URIs: https://deb.debian.org/debian
Suites: testing
Components: main
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
SOURCES
apt-get update -qq
