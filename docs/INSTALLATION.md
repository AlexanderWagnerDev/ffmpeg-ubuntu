# Installing FFmpeg for Ubuntu

Packages target **Ubuntu 24.04 LTS (Noble), 26.04 LTS (Resolute), and 26.10 (Stonking)**, each on **AMD64 and ARM64**. Verify that binary packages are available for your system before installing.

## Option 1: Launchpad PPA

Launchpad supports building source uploads for `amd64`, `amd64v3`, `arm64`, `armhf`, `ppc64el`, `riscv64`, and `s390x`, if enabled for this PPA and supported for the Ubuntu release. `amd64v3` is not available on Ubuntu 24.04. These architectures are **not guaranteed to have successful FFmpeg builds**, so check [the PPA's published packages](https://launchpad.net/~alexanderwagnerdev/+archive/ubuntu/ffmpeg/+packages) for your particular Ubuntu version and hardware before installing.

Check the [FFmpeg PPA](https://launchpad.net/~alexanderwagnerdev/+archive/ubuntu/ffmpeg) for published packages matching your Ubuntu release.

```bash
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:alexanderwagnerdev/ffmpeg
sudo apt update
apt-cache policy ffmpeg
sudo apt -s install ffmpeg
```

Review APT's proposed transaction before running:

```bash
sudo apt install ffmpeg
ffmpeg -version
ffprobe -version
```

## Option 2: Independent GitHub Pages APT repository

**URL:** https://alexanderwagnerdev.github.io/ffmpeg-ubuntu/

The Pages channel is a separate, signed APT repository. **Do not add it until its first deployment has succeeded** and the signing public key is available.

Verify the public key's fingerprint against an independent trusted source before trusting the repository. Downloading a public key from the same site hosting the packages does not by itself establish its ownership.

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -d -m 0755 /etc/apt/keyrings

curl -fsSL https://alexanderwagnerdev.github.io/ffmpeg-ubuntu/ffmpeg-ubuntu.gpg |
  sudo tee /etc/apt/keyrings/ffmpeg-ubuntu.gpg >/dev/null

gpg --show-keys --with-fingerprint /etc/apt/keyrings/ffmpeg-ubuntu.gpg

source /etc/os-release
case "$VERSION_CODENAME" in
  noble|resolute|stonking) ;;
  *) echo "Unsupported Ubuntu release: $VERSION_CODENAME" >&2; exit 1 ;;
esac

sudo tee /etc/apt/sources.list.d/ffmpeg-ubuntu.sources >/dev/null <<SOURCES
Types: deb
URIs: https://alexanderwagnerdev.github.io/ffmpeg-ubuntu/
Suites: ${VERSION_CODENAME}
Components: main
Architectures: amd64 arm64
Signed-By: /etc/apt/keyrings/ffmpeg-ubuntu.gpg
SOURCES

sudo apt update
apt-cache policy ffmpeg
sudo apt -s install ffmpeg
```

After verifying the public key and reviewing APT's proposed changes:

```bash
sudo apt install ffmpeg
ffmpeg -version
ffprobe -version
```

APT chooses your native architecture and the configured source uses your installed Ubuntu codename.

## Troubleshooting

**No candidate:** Check `dpkg --print-architecture`, your Ubuntu codename (`. /etc/os-release && echo "$VERSION_CODENAME"`), and whether the repository has published matching packages.

**Unexpected versions:** Inspect `apt-cache policy ffmpeg`. Do not disable Ubuntu security repositories or use overly broad pinning rules.

**Missing dependencies or shared libraries:** Do not force-install random Debian packages or alter system-wide library paths. [Report the package version and complete error](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/issues).

## Remove a package source

Launchpad:

```bash
sudo add-apt-repository --remove ppa:alexanderwagnerdev/ffmpeg
sudo apt update
```

GitHub Pages:

```bash
sudo rm -f /etc/apt/sources.list.d/ffmpeg-ubuntu.sources
sudo rm -f /etc/apt/keyrings/ffmpeg-ubuntu.gpg
sudo apt update
```

Removing a repository does not automatically uninstall or downgrade already installed packages. Review installed versions before attempting a rollback.
