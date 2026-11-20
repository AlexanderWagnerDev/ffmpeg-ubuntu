# FFmpeg for Ubuntu

[![CI](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/ci.yml/badge.svg)](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/ci.yml)
[![Build source](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/build-source.yml/badge.svg)](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/build-source.yml)

Ubuntu source and binary packaging for **FFmpeg 9**, with two independent distribution methods: **signed GitHub Pages APT repository** (without Launchpad) and an optional **Launchpad PPA**.

**Status:** FFmpeg 9.0.2 source-package generation and Ubuntu 26.04 build-dependency resolution have passed CI. Native AMD64 and ARM64 binary builds and signed GitHub Pages APT publication are now implemented but **not yet confirmed successful end-to-end**. Do not use the Pages APT URL until the first deployment passes. Launchpad is optional; no Launchpad binary build is verified yet.

| Link | Purpose |
|---|---|
| [Launchpad project](https://launchpad.net/awdev-ffmpeg) | Project identity and information |
| [GitHub Pages APT](https://alexanderwagnerdev.github.io/ffmpeg-ubuntu/) | Independent signed APT repository, after deployment succeeds |
| [Optional PPA](https://launchpad.net/~alexanderwagnerdev/+archive/ubuntu/ffmpeg) | Alternative package publishing if separately set up |
| [FFmpeg upstream](https://ffmpeg.org/) | Original multimedia software |
| [Debian FFmpeg source](https://tracker.debian.org/pkg/ffmpeg) | Source package definitions used by the build |

## Architecture

1. Obtain the FFmpeg 9.x source package from the **signed Debian testing source repository** (only `deb-src`, not binary sources).
2. Keep Debian's packaging and patches. Add a unique Ubuntu-series-specific changelog version.
3. Produce a Debian/Ubuntu **source upload**, validate it by extracting the newly generated `.dsc`, check whether the target Ubuntu release can resolve its declared build dependencies, and store it as a GitHub Actions artifact.
4. For **GitHub Pages**, compile native AMD64 and ARM64 binary packages on separate GitHub runners using Ubuntu 26.04 containers; test their installation in clean containers.
5. In a credential-protected job, generate signed APT metadata for both architectures and publish the complete package repository to GitHub Pages.
6. Alternatively, upload a signed source package through the **optional Launchpad PPA** workflow; Launchpad then handles its own binary builds.

The GitHub Pages workflow uses separate binary-build, signing and deployment jobs, keeping signing secrets away from the source compilation stage. The optional Launchpad workflow similarly isolates its OpenPGP signing credentials and uploads with `dput ppa:…` (no SSH key required).

## Ubuntu support

| Ubuntu | Architecture target | Status |
|---|---|---|
| **26.04 LTS (resolute)** | amd64, arm64 | GitHub Pages native binary builds configured; end-to-end checks pending |
| 24.04 LTS (noble) | amd64, arm64 | Experimental; dependency backports may be needed |
| 22.04 LTS (jammy) | amd64, arm64 | Experimental; dependency backports may be needed |

Debian's `debhelper-compat (= 14)` requirement is adapted to level 13 for Resolute, where level 14 is unavailable. A full native binary build is still necessary to validate this backport.

The Launchpad PPA must have `arm64` enabled explicitly. Do not assume a source package validated on GitHub can be built against every Ubuntu release or architecture.

## Local checks

```bash
python3 -m unittest discover -s tests -v
bash -n scripts/*.sh
shellcheck scripts/*.sh
```

Generate a source upload (on Ubuntu; adds a **source-only** Debian APT entry):

```bash
sudo bash scripts/setup-build-env.sh
bash scripts/build-source.sh resolute 1
bash scripts/verify-source.sh resolute
```

Artifacts are written to `dist/resolute/`. Remove `work/resolute/` and
`dist/resolute/` before repeating the local build to avoid stale files.

## CI and maintenance

| Workflow | Operation |
|---|---|
| [CI](.github/workflows/ci.yml) | Python unit tests, ShellCheck, bash syntax |
| [Build Ubuntu source package](.github/workflows/build-source.yml) | Builds and validates unsigned source packages on push/manual runs and weekly; stores artifacts |
| [Publish FFmpeg APT via GitHub Pages](.github/workflows/pages-apt.yml) | Native AMD64 and ARM64 builds, installation smoke tests, signed APT indexes, Pages deployment |
| [Publish to Launchpad PPA](.github/workflows/publish-ppa.yml) | Optional OpenPGP-signed source upload via `dput ppa:…`; no SSH secrets; manual or **opt-in** scheduled publishing |
| [Dependabot](.github/dependabot.yml) | GitHub Actions dependency maintenance |

All external GitHub Actions are pinned to commit hashes.

**Both scheduled publishing paths are disabled by default.** First configure [GitHub Pages APT](docs/GITHUB-PAGES.md) and its dedicated key. Launchpad is a separate, optional [setup](docs/LAUNCHPAD.md), requiring only two dedicated OpenPGP environment secrets. Only enable scheduled publishing after an end-to-end install passes.

## Install through GitHub Pages (after the first successful deployment)

Use the public signing key from the deployed repository and a Deb822 `.sources` file. The full AMD64 and ARM64 instructions are in [GitHub Pages APT setup](docs/GITHUB-PAGES.md).

The expected source URI is `https://alexanderwagnerdev.github.io/ffmpeg-ubuntu/` for Ubuntu 26.04 `resolute`. Verify the signing-key fingerprint independently before trusting a new repository.

## Optional Launchpad installation (only after the PPA builds successfully)

```bash
sudo add-apt-repository ppa:alexanderwagnerdev/ffmpeg
sudo apt update
apt-cache policy ffmpeg
sudo apt -s install ffmpeg
```

After inspecting the dry run:

```bash
sudo apt install ffmpeg
ffmpeg -version
```

When Ubuntu Pro/ESM or another package source takes precedence, compare the
versions and APT priority with `apt-cache policy ffmpeg`. Avoid global pinning
or disabling security updates.

## Licensing

Automation and supporting repository materials follow [LICENSE](LICENSE).
FFmpeg and Debian packaging have their **own licenses and copyright notices**;
the license in this repository does not supersede them. Rebuilding and
redistributing multimedia codecs can have additional legal/technical
requirements depending on build configuration and jurisdiction.

Issues and PRs are welcome.
