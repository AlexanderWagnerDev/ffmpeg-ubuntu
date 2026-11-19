# FFmpeg for Ubuntu

[![CI](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/ci.yml/badge.svg)](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/ci.yml)
[![Build source](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/build-source.yml/badge.svg)](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/build-source.yml)

Ubuntu/Launchpad PPA source packaging for **FFmpeg 9**, maintained by AlexanderWagnerDev.

**Status:** FFmpeg 9.0.2 source-package generation and verification work on GitHub CI. **No Launchpad binary PPA publication has been verified yet.** This repository does not itself host downloadable \`.deb\` files. Refer to the [Actions runs](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions) for live status.

| Link | Purpose |
|---|---|
| [Launchpad project](https://launchpad.net/awdev-ffmpeg) | Project identity and information |
| [Planned public PPA](https://launchpad.net/~alexanderwagnerdev/+archive/ubuntu/ffmpeg) | Actual APT package publishing, once created and populated |
| [FFmpeg upstream](https://ffmpeg.org/) | Original multimedia software |
| [Debian FFmpeg source](https://tracker.debian.org/pkg/ffmpeg) | Source package definitions used by the build |

## Architecture

1. Obtain the FFmpeg 9.x source package from the **signed Debian testing source repository** (only \`deb-src\`, not binary sources).
2. Keep Debian's packaging and patches. Add a unique Ubuntu-series-specific changelog version.
3. Produce a Debian/Ubuntu **source upload**, validate it by extracting the newly generated \`.dsc\`, and store it as a GitHub Actions artifact.
4. In a separate, protected workflow, check Launchpad for earlier uploads, sign the source package with a registered OpenPGP identity and submit it over SFTP.
5. **Launchpad**, not GitHub, builds and hosts the final apt-installable amd64/arm64 packages.

The two-job publication workflow keeps signing/SSH secrets away from the
build process that executes upstream/Debian source scripts.

## Ubuntu support

| Ubuntu | Architecture target | Status |
|---|---|---|
| **26.04 LTS (resolute)** | amd64, arm64 | Primary; source package validated; Launchpad binaries pending |
| 24.04 LTS (noble) | amd64, arm64 | Experimental; dependency backports may be needed |
| 22.04 LTS (jammy) | amd64, arm64 | Experimental; dependency backports may be needed |

The Launchpad PPA must have \`arm64\` enabled explicitly. Do not assume a source package validated on GitHub can be built against every Ubuntu release or architecture.

## Local checks

\`\`\`bash
python3 -m unittest discover -s tests -v
bash -n scripts/*.sh
shellcheck scripts/*.sh
\`\`\`

Generate a source upload (on Ubuntu; adds a **source-only** Debian APT entry):

\`\`\`bash
sudo bash scripts/setup-build-env.sh
bash scripts/build-source.sh resolute 1
bash scripts/verify-source.sh resolute
\`\`\`

Artifacts are written to \`dist/resolute/\`. Remove \`work/resolute/\` and
\`dist/resolute/\` before repeating the local build to avoid stale files.

## CI and maintenance

| Workflow | Operation |
|---|---|
| [CI](.github/workflows/ci.yml) | Python unit tests, ShellCheck, bash syntax |
| [Build Ubuntu source package](.github/workflows/build-source.yml) | Builds and validates unsigned source packages on push/manual runs and weekly; stores artifacts |
| [Publish to Launchpad PPA](.github/workflows/publish-ppa.yml) | Environment-protected SFTP source upload; manual or **opt-in** scheduled publishing |
| [Dependabot](.github/dependabot.yml) | GitHub Actions dependency maintenance |

All external GitHub Actions are pinned to commit hashes.

**Publication is disabled by default** until the [Launchpad setup](docs/LAUNCHPAD.md) is complete. The \`PPA_AUTO_PUBLISH\` repository variable can enable optional weekly release checks after first successful manual publication and Ubuntu installation checks.

## Installation (only after the PPA builds successfully)

\`\`\`bash
sudo add-apt-repository ppa:alexanderwagnerdev/ffmpeg
sudo apt update
apt-cache policy ffmpeg
sudo apt -s install ffmpeg
\`\`\`

After inspecting the dry run:

\`\`\`bash
sudo apt install ffmpeg
ffmpeg -version
\`\`\`

When Ubuntu Pro/ESM or another package source takes precedence, compare the
versions and APT priority with \`apt-cache policy ffmpeg\`. Avoid global pinning
or disabling security updates.

## Licensing

Automation and supporting repository materials follow [LICENSE](LICENSE).
FFmpeg and Debian packaging have their **own licenses and copyright notices**;
the license in this repository does not supersede them. Rebuilding and
redistributing multimedia codecs can have additional legal/technical
requirements depending on build configuration and jurisdiction.

Issues and PRs are welcome.
