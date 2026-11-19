# FFmpeg for Ubuntu

[![CI](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/ci.yml/badge.svg)](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/ci.yml)
[![Build source](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/build-source.yml/badge.svg)](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/build-source.yml)

Ubuntu source-package build and Launchpad PPA automation for **FFmpeg 9**, maintained by AlexanderWagnerDev.

- GitHub repository: https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu
- Launchpad **project**: https://launchpad.net/awdev-ffmpeg
- Planned Launchpad **PPA**: https://launchpad.net/~alexanderwagnerdev/+archive/ubuntu/ffmpeg
- Upstream FFmpeg: https://ffmpeg.org/
- Debian FFmpeg source packaging: https://tracker.debian.org/pkg/ffmpeg

> **Status: packaging infrastructure / not a published FFmpeg 9 PPA yet.**
> Creating a Launchpad project does not create a PPA. No binaries are published by this repository until the separate PPA is created, credentials configured, and builds succeed.

## How it works

The build retrieves a verified **Debian testing source package** for FFmpeg, checks that its upstream version is **9.x**, adds a series-specific Ubuntu version/changelog entry and produces an **unsigned** `.dsc` source upload. GitHub Actions can store it for inspection. A **separate, manually triggered protected workflow** signs and uploads it to Launchpad via SFTP. Launchpad, not GitHub, builds amd64/arm64 `.deb` packages.

The Debian packaging is intentionally **not copied** into this repository: the Debian Multimedia Maintainers provide `debian/control`, `debian/rules`, patches and binary package definitions as part of the Debian source package. This reduces the chance of silently breaking ABI/package relations by inventing incomplete packaging.

### Target series

| Ubuntu | Series | Status |
|---|---|---|
| 26.04 LTS | resolute | Primary target; launchpad binary-build validation still required |
| 24.04 LTS | noble | Experimental; dependencies/patches may be needed |
| 22.04 LTS | jammy | Experimental; dependencies/patches may be needed |

Architecture support depends on the PPA's enabled processors and the source's build dependencies.

## Development and checks

```bash
python3 -m unittest discover -s tests -v
bash -n scripts/*.sh
shellcheck scripts/*.sh
```

On an Ubuntu build host (requires sudo; **source-only Debian metadata** is added):

```bash
sudo bash scripts/setup-build-env.sh
bash scripts/build-source.sh resolute 1
bash scripts/verify-source.sh resolute
```

Build files are written to `dist/resolute/`; no binary package is built locally. To repeat a local build, remove `work/resolute` and `dist/resolute` first.

## GitHub Actions

- **CI:** shell syntax, ShellCheck, Python unit tests.
- **Build Ubuntu source package:** manual for any target or a weekly unsigned source build for `resolute`. Uploads artifacts for review; **never publishes automatically**.
- **Publish to Launchpad PPA:** manually invoked; runs under the `launchpad-ppa` GitHub Environment, imports separately configured secrets, signs and uploads a source package.

See [Launchpad setup and publication](docs/LAUNCHPAD.md) before the first PPA upload.

## APT installation (after successful PPA publication)

```bash
sudo add-apt-repository ppa:alexanderwagnerdev/ffmpeg
sudo apt update
apt-cache policy ffmpeg
sudo apt -s install ffmpeg
```

**Do not assume an FFmpeg 9 package exists in this PPA yet.** Launchpad builds may fail because Debian 9.x build dependencies are newer than those provided by a particular Ubuntu series. The generated source artifact is only the starting point for testing and backport fixes.

## Maintenance and licensing

The automation is maintained here. FFmpeg itself and the Debian source package retain their respective upstream copyrights and license requirements. Inspect package licensing and build configuration before distributing codec-enabled binaries. See [LICENSE](LICENSE) for this repository's own license; that license does **not** replace upstream FFmpeg licensing.

Contributions and pull requests are welcome.
