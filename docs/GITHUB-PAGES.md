# GitHub Pages APT repository — Ubuntu 26.04 AMD64 and ARM64

This is a **standalone APT repository**, not a Launchpad PPA. It is generated
by GitHub Actions after native FFmpeg 9 binary builds pass installation tests.

**The expected URL only works after an actual successful Pages deployment:**

https://alexanderwagnerdev.github.io/ffmpeg-ubuntu/

The repository must include:
- `dists/resolute/InRelease` and `dists/resolute/Release`
- `dists/resolute/main/binary-amd64/Packages.gz`
- `dists/resolute/main/binary-arm64/Packages.gz`
- The matching binaries in `pool/main/f/ffmpeg/`
- Public key `ffmpeg-ubuntu.gpg`

## One-time configuration by repository owner

1. Open [Settings → Pages](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/settings/pages)
   and set **Build and deployment → Source: GitHub Actions**.
2. Open [Settings → Secrets and variables → Actions](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/settings/secrets/actions). No extra signing Environment is required.
3. On a trusted Linux machine, create a **dedicated APT signing key** (not your
   normal personal Git or Launchpad signing key). For unattended CI signing,
   this example creates a key with no interactive passphrase:

   ```bash
   umask 077
   gpg --batch --pinentry-mode loopback --passphrase '' \
     --quick-generate-key \
     'FFmpeg for Ubuntu APT <info@alexanderwagnerdev.com>' \
     rsa4096 sign 2y
   gpg --list-secret-keys --with-colons
   ```

   Copy the newly generated fingerprint from the `fpr` line. Keep a safe
   offline backup and never post private key content in chats, issues, or Git.
4. Add these two **repository secrets**:

   | Secret | Value |
   |---|---|
   | `PAGES_APT_GPG_FINGERPRINT` | Full fingerprint of the dedicated new key |
   | `PAGES_APT_GPG_PRIVATE_KEY_B64` | Base64-encoded secret-key export |

   Create the encoded export locally:

   ```bash
   gpg --batch --armor --export-secret-keys YOUR_FULL_FINGERPRINT | base64 -w0
   ```

   Paste the result **only** into the GitHub secret input. Do not share it.
5. Go to [Actions → Publish FFmpeg APT via GitHub Pages](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/pages-apt.yml)
   and run it manually on `main` with revision `1`.
   Both AMD64 and ARM64 builds must pass before signing or deployment begins.
6. Verify that both package indexes and the detached public key are served by
   the live URL. Compare the downloaded public key's fingerprint against the
   fingerprint recorded on your trusted machine when creating the signing key; GitHub does not let you reveal saved secret values.

## Installing on Ubuntu 26.04 LTS

These instructions work on **AMD64 and ARM64** after publication.

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gpg
sudo install -d -m 0755 /etc/apt/keyrings

curl -fsSL https://alexanderwagnerdev.github.io/ffmpeg-ubuntu/ffmpeg-ubuntu.gpg |
  sudo tee /etc/apt/keyrings/ffmpeg-ubuntu.gpg >/dev/null

gpg --show-keys --with-fingerprint /etc/apt/keyrings/ffmpeg-ubuntu.gpg

sudo tee /etc/apt/sources.list.d/ffmpeg-ubuntu.sources >/dev/null <<'SOURCES'
Types: deb
URIs: https://alexanderwagnerdev.github.io/ffmpeg-ubuntu/
Suites: resolute
Components: main
Architectures: amd64 arm64
Signed-By: /etc/apt/keyrings/ffmpeg-ubuntu.gpg
SOURCES

sudo apt-get update
apt-cache policy ffmpeg
sudo apt-get -s install ffmpeg
```

**Stop and verify the key's fingerprint before trusting it.** A key served at
the same address as the packages is convenient for bootstrapping, but doesn't
independently prove ownership of that key. Confirm it using a trusted channel.

After reviewing APT's proposed transaction:

```bash
sudo apt-get install ffmpeg
ffmpeg -version
ffprobe -version
```

APT automatically selects the correct index based on host architecture. This
source supports only `resolute`; do **not** reuse it on Ubuntu 22.04 or 24.04.

If Ubuntu Pro/ESM or another APT source overrides this repository's
candidate, inspect `apt-cache policy ffmpeg` before applying **targeted**
pinning. Don't disable security updates globally.

## Automation

The workflow is intentionally **manual by default**. To opt into weekly
rebuilds after the first successful publication and real-machine test,
create an Actions repository **variable** named
`PAGES_APT_AUTO_PUBLISH` set to `true`.

Only the complete tested amd64+arm64 snapshot is published. A failed job
leaves the previous GitHub Pages deployment unchanged. Use higher revision
numbers if the same FFmpeg upstream version is repackaged with changes.

## Limitations

- FFmpeg and Debian's package definitions may evolve and require Ubuntu
  backport patches. A passing source build or dependency simulation is not
  proof of an actual binary build.
- This project uses native GitHub-hosted ARM64 runners
  (`ubuntu-26.04-arm`) and native AMD64 runners, both with Ubuntu 26.04
  build containers. Cross-emulation is **not** used.
- Large FFmpeg binary-package sets can exceed the approximately 1 GB GitHub
  Pages deployment limit. The signing job refuses sites above 900 MiB.
- GitHub Pages is not designed to be a large, indefinitely versioned APT CDN.
  The workflow publishes a **single latest snapshot**; it doesn't preserve
  every earlier binary version. Keep a backup of old releases elsewhere.
- Rebuilding FFmpeg for distribution requires careful attention to codec
  licensing and relevant third-party patents, where applicable.

References:
- [GitHub Pages workflow configuration](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [GitHub-hosted ARM64 runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
- [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)

> The workflow intentionally separates compiling FFmpeg from the signing job; only the latter reads the secret values. The normal **`github-pages`** Environment in the deployment job stays, because GitHub Pages uses it to associate deployments with the Pages site. It is not where you need to store the signing secrets.

If the signing secrets were previously stored only under `apt-pages-signing`, re-add them as repository secrets. GitHub does not expose existing secret values for copying.
