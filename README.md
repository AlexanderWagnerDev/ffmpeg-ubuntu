# FFmpeg for Ubuntu

[![CI](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/ci.yml/badge.svg)](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/ci.yml)
[![Binary builds](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/binary-ci.yml/badge.svg)](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/binary-ci.yml)
[![GitHub Pages](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/pages-apt.yml/badge.svg)](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/pages-apt.yml)

**Community-maintained FFmpeg 9 packages for Ubuntu.**

FFmpeg for Ubuntu rebuilds the multimedia toolkit and its libraries from Debian's FFmpeg source packaging for Ubuntu. Packages are distributed independently through a [Launchpad PPA](https://launchpad.net/~alexanderwagnerdev/+archive/ubuntu/ffmpeg) and a [signed GitHub Pages APT repository](https://alexanderwagnerdev.github.io/ffmpeg-ubuntu/).

This is an independent project, not an official FFmpeg or Ubuntu distribution.

## Installation

Before installing, confirm that binaries have been **successfully published** for your Ubuntu release and architecture. Source builds alone do not prove package availability.

### Launchpad PPA

Once packages are available for your Ubuntu release:

```bash
sudo add-apt-repository ppa:alexanderwagnerdev/ffmpeg
sudo apt update
apt-cache policy ffmpeg
sudo apt install ffmpeg
ffmpeg -version
```

### GitHub Pages APT

A standalone signed APT repository that does not depend on Launchpad:

**https://alexanderwagnerdev.github.io/ffmpeg-ubuntu/**

See the [installation guide](docs/INSTALLATION.md) for the public keyring, APT source file, verification, and removal instructions. Use the Pages repository **only after a successful deployment**.

## Supported platforms

| Ubuntu | AMD64 | ARM64 |
|---|---|---|
| **26.04 LTS (Resolute)** | Build target | Build target |
| 24.04 LTS (Noble) | Not yet supported | Not yet supported |
| 22.04 LTS (Jammy) | Not yet supported | Not yet supported |

A **build target is not a guarantee that installable packages have been published**. Check the [workflow results](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions) and [PPA package status](https://launchpad.net/~alexanderwagnerdev/+archive/ubuntu/ffmpeg).

## Packages and features

The Debian FFmpeg source package produces the `ffmpeg` and `ffplay` tools, `ffprobe`, FFmpeg shared libraries, and development packages, subject to successful native builds and packaging options.

- FFmpeg 9 audio/video encoding, decoding, transcoding and streaming.
- APT-native dependency management and cryptographically signed repository metadata.
- Native Ubuntu 26.04 AMD64 and ARM64 binary builds and installation tests.
- Public source packaging automation and transparent build results.

## Build provenance

The source package comes from the **signed Debian testing source index**. Ubuntu-specific packaging adjustments are applied during source preparation. Native binary builds, dependency checks, and clean-container installation tests are performed before the GitHub Pages channel can publish.

Launchpad runs a separate binary build after accepting a signed source upload. Availability and results may differ across distribution channels.

**Upstream:** [FFmpeg](https://ffmpeg.org/) · **Debian source:** [Debian FFmpeg](https://tracker.debian.org/pkg/ffmpeg) · **Automation:** [GitHub Actions](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions)

## Contributions and support

For a package installation or compatibility issue, [open an issue](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/issues) and include the Ubuntu version, architecture, package version, and full error message. See [CONTRIBUTING.md](CONTRIBUTING.md) for development contributions and [SECURITY.md](SECURITY.md) for private security reporting.

## License and attribution

The automation in this repository uses the [MIT License](LICENSE). FFmpeg, its included components, and Debian packaging retain their own licenses and copyright notices; availability and permitted redistribution of some codecs may vary by configuration and jurisdiction.

**This community-maintained package repository is not affiliated with or endorsed by FFmpeg, Debian, Canonical, or Ubuntu.**
