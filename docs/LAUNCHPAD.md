# Launchpad FFmpeg PPA: first-time setup and maintenance

The [Launchpad project](https://launchpad.net/awdev-ffmpeg) is **not** an APT archive.
You must create a **separate public PPA** under the Launchpad user
`alexanderwagnerdev` with **PPA URL name `ffmpeg`**. This is a one-time account action.

PPA (after it has been created):
https://launchpad.net/~alexanderwagnerdev/+archive/ubuntu/ffmpeg

## One-time setup

1. Sign in to Launchpad; from your **user profile**, activate/create the new PPA `ffmpeg`.
   Leave it public. Enable `amd64` and `arm64` in **Change details → Processors**;
   amd64 is normally enabled by default but arm64 is not.
2. Register a **dedicated CI OpenPGP public key** in your Launchpad account.
   The public key must be accepted by Launchpad before publishing. Register a
   **dedicated SSH public key** there too.
3. Verify the **authentic server host key** for `ppa.launchpad.net` from a trusted
   source before creating your `known_hosts` entry. Do not blindly trust a
   fingerprint copied from an unauthenticated SSH scan.
4. In GitHub, create an **Environment named `launchpad-ppa`** and add
   the following **environment secrets**, not files committed to this repo:

   | Secret | Value |
   |---|---|
   | `PPA_GPG_PRIVATE_KEY_B64` | Base64 of the CI OpenPGP private-key export |
   | `PPA_GPG_FINGERPRINT` | Full fingerprint registered with Launchpad |
   | `PPA_SSH_PRIVATE_KEY` | Dedicated unencrypted CI Ed25519 private key (multiline) |
   | `PPA_SSH_KNOWN_HOSTS` | Independently verified SSH host-key line for ppa.launchpad.net |

   **Never paste or commit private keys.** A dedicated short-lived CI signing key
   without an interactive passphrase is assumed; keep the key tightly scoped and
   rotate/revoke it if compromised. Protect the GitHub Environment and
   require human approval where appropriate.

5. Run the **Publish to Launchpad PPA** workflow manually on `main` for
   `resolute`. It first builds an **unsigned** source archive in a job without
   credentials; a separate Environment-gated job checks Launchpad, signs the
   artifact, and submits via SFTP.

## Important upload behavior

- `awdev-ffmpeg-ppa` is an explicit `dput` SFTP profile created by the
  workflow (username `alexanderwagnerdev`, incoming directory
  `~alexanderwagnerdev/ubuntu/ffmpeg/`).
- CI now also checks whether the target Ubuntu archive can resolve declared source build dependencies using an isolated Ubuntu Docker container. This is **not** a complete binary-build or ABI test. A failed dependency check blocks publication until compatibility is addressed.
- Launchpad accepts source uploads only. It builds and publishes the final
  `.deb` files; an accepted upload is **not** proof that a binary build succeeds.
- A public API check prevents attempting to reupload an identical or older
  version in the same Ubuntu suite. If Launchpad cannot be reached or the PPA
  does not exist, the check **fails closed**.
- For an existing source version with a failed binary build, increase the
  workflow's `revision` parameter from `1` to `2`, etc. A unique source
  version is required for every new upload.
- `jammy` and `noble` are **experimental** until their build-dependency and
  ABI compatibility is established; do not assume Debian testing packages will
  compile on these older releases.
- Once the first `resolute` upload has been accepted, the packages compile,
  and installation has been tested, you can opt into automatic weekly
  publication: GitHub **Settings → Secrets and variables → Actions → Variables**
  → create repository variable **`PPA_AUTO_PUBLISH=true`**. Keep it disabled
  until that first successful end-to-end validation. The schedule is guarded
  and does **not** attempt a publishing run when the variable is missing.
  Required Environment reviewers (if configured) still apply.

## Verify end-to-end after publication

Use Launchpad's PPA package page to verify the **amd64** and **arm64** build
statuses; they can fail independently.

On a clean disposable Ubuntu 26.04 machine:

```bash
sudo add-apt-repository ppa:alexanderwagnerdev/ffmpeg
sudo apt update
apt-cache policy ffmpeg
sudo apt -s install ffmpeg
sudo apt install ffmpeg
ffmpeg -version
ffprobe -version
```

If Ubuntu ESM or another repository has a higher APT priority, inspect
`apt-cache policy ffmpeg` and implement narrowly scoped pinning. Do **not**
disable Ubuntu security updates globally.

## Provenance and limitations

The source build uses the **signed Debian testing `deb-src` index** and
inherits Debian's `debian/` package definitions, patches, and build flags.
No Debian binary archive is added to the build runner. The upstream FFmpeg
tarball may carry a separate detached signature; the Debian archive signature
provides the trusted source-index provenance, **not an independent upstream
signature verification**.

The CI builds and validates source packages. It does not guarantee that every
binary, library dependency, codec feature, or target architecture will build.
Review Debian copyright/licensing before publishing FFmpeg binaries.

Documentation:
- https://ubuntu.com/docs/launchpad/user/how-to/packaging/ppa-package-upload/
- https://ubuntu.com/docs/launchpad/user/reference/packaging/ppas/ppa/
- https://ubuntu.com/docs/launchpad/user/explanation/packaging/package-upload-errors/
