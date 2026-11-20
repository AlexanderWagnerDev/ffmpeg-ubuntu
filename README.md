# FFmpeg for Ubuntu

[![CI](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/ci.yml/badge.svg)](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/ci.yml)
[![Binary builds](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/binary-ci.yml/badge.svg)](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/binary-ci.yml)
[![Release pipeline](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/release-pipeline.yml/badge.svg)](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/release-pipeline.yml)

**Automatically updated community-maintained FFmpeg packages for Ubuntu.**

FFmpeg for Ubuntu builds the latest stable releases from officially signed FFmpeg source tarballs, using Debian's FFmpeg packaging as an Ubuntu starting point. New stable releases, including future major versions, are discovered automatically. Packages are distributed independently through a [Launchpad PPA](https://launchpad.net/~alexanderwagnerdev/+archive/ubuntu/ffmpeg) and a [signed GitHub Pages APT repository](https://alexanderwagnerdev.github.io/ffmpeg-ubuntu/).

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
| **24.04 LTS (Noble)** | Build target | Build target |
| **26.04 LTS (Resolute)** | Build target | Build target |
| **26.10 (Stonking)** | Build target | Build target |

A **build target is not a guarantee that installable packages have been published**. Check the [workflow results](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions) and [PPA package status](https://launchpad.net/~alexanderwagnerdev/+archive/ubuntu/ffmpeg).

## Packages and features

The Debian FFmpeg source package produces the `ffmpeg` and `ffplay` tools, `ffprobe`, FFmpeg shared libraries, and development packages, subject to successful native builds and packaging options.

- Current stable FFmpeg audio/video encoding, decoding, transcoding and streaming.
- APT-native dependency management and cryptographically signed repository metadata.
- AMD64 and ARM64 binary builds and installation tests for Ubuntu 24.04, 26.04 and 26.10.
- Public source packaging automation and transparent build results.

## Automated release pipeline

The [FFmpeg release pipeline](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/release-pipeline.yml) is the **only scheduled publishing entry point**. It runs a daily upstream check (GitHub Actions schedules runs using cron and may delay the actual start) and is also available through **Actions → FFmpeg release pipeline → Run workflow** on the `main` branch.

1. **Check:** Compare the latest official stable FFmpeg release against the published versions in both channels.
2. **Build and test:** If either channel needs an update, prepare source packages for Noble, Resolute, and Stonking; then build and smoke-test all six native Ubuntu/architecture combinations. All builds must pass.
3. **Publish:** Only after all tests pass, sign and deploy the GitHub Pages APT repository and/or sign and upload sources to the Launchpad PPA, depending on which channel needs updating.

The stages use [reusable GitHub Actions workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows). Source and binary artifacts stay in the **same pipeline run**, rather than rebuilding separately for each publication channel. If neither channel needs updating, the pipeline exits without building.

Manual runs accept a positive `revision` (default `1`) and a `force` toggle (default `false`). Set `force=true` to rebuild even if the stable version is already published; the Launchpad publisher still refuses to upload a duplicate or older package version. Increase `revision` when deliberately rebuilding an already published upstream version.

The source-package and binary validation workflows remain available for development CI, but have **no independent release schedule**. The signing secrets must be configured before publishing; Launchpad's subsequent builds are asynchronous and may still fail or require time to become available.

### Release changelog

Every Ubuntu source package now includes the **official FFmpeg release notes** for its exact upstream version in `debian/changelog`, in addition to the Ubuntu packaging/rebuild entry. The notes are read directly from the source tree's upstream `Changelog` (the official signed FFmpeg tarball when updated, or the signed Debian source when already current), not a separately scraped web summary. The PPA package's **Changelog** shows the release-specific features and fixes for each Ubuntu version, rather than just a generic rebuild line. If the exact release section cannot be found, the build fails rather than publishing misleading notes.

## Build provenance

Debian packaging comes from the **signed Debian testing source index**. When the official FFmpeg stable release is newer, its upstream-signed source tarball replaces Debian's older upstream source. Ubuntu-specific packaging and library ABI adjustments are applied during source preparation. A single daily GitHub Actions cron checks both publication channels for new stable versions. Native binary builds, dependency checks, and clean-container installation tests must pass before the GitHub Pages channel can publish.

Launchpad runs a separate binary build after accepting a signed source upload. Availability and results may differ across distribution channels.

Major FFmpeg upgrades can require packaging changes; failed builds block publication rather than falling back to an older version.

**Upstream:** [FFmpeg](https://ffmpeg.org/) · **Debian source:** [Debian FFmpeg](https://tracker.debian.org/pkg/ffmpeg) · **Automation:** [GitHub Actions](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions)

## Contributions and support

For a package installation or compatibility issue, [open an issue](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/issues) and include the Ubuntu version, architecture, package version, and full error message. See [CONTRIBUTING.md](CONTRIBUTING.md) for development contributions and [SECURITY.md](SECURITY.md) for private security reporting.

## License and attribution

The automation in this repository uses the [MIT License](LICENSE). FFmpeg, its included components, and Debian packaging retain their own licenses and copyright notices; availability and permitted redistribution of some codecs may vary by configuration and jurisdiction.

**This community-maintained package repository is not affiliated with or endorsed by FFmpeg, Debian, Canonical, or Ubuntu.**
