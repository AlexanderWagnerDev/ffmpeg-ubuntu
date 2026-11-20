# Optional Launchpad PPA publishing

This is an **alternative** to the standalone [GitHub Pages APT repository](GITHUB-PAGES.md).
The [Launchpad project](https://launchpad.net/awdev-ffmpeg) is not itself a PPA.

Like [OpenRTMP/librtmp2](https://github.com/OpenRTMP/librtmp2/blob/main/.github/workflows/publish-ppa.yml),
this repository publishes a signed **source package** with:

```bash
dput "ppa:alexanderwagnerdev/ffmpeg" <SIGNED_SOURCE_CHANGES_FILE>
```

**No SSH private key, known_hosts secret, or Launchpad API token is needed.**
Launchpad identifies authorized uploaders by the OpenPGP signature on the source upload.
Launchpad builds final binary packages after accepting the source.

## One-time steps

1. Sign in to the Launchpad profile controlling `alexanderwagnerdev`. Create a
   **public PPA** with URL name `ffmpeg`, separate from the project
   `awdev-ffmpeg`. The expected address is
   https://launchpad.net/~alexanderwagnerdev/+archive/ubuntu/ffmpeg .
   Enable amd64 and (if available/authorized for the PPA) arm64 processors.
2. Register the **public part of your CI upload OpenPGP signing key** in
   Launchpad and complete the confirmation/verification steps. You can
   generate a dedicated key and upload its public portion to the Ubuntu
   keyserver, then import its fingerprint in Launchpad's OpenPGP key settings.
   Do not register a GitHub SSH key; this workflow does not use SSH.
3. In [GitHub Environments](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/settings/environments),
   create an Environment named **`launchpad-ppa`** and add only these two
   **Environment secrets**:

   | Secret | Content |
   |---|---|
   | `PPA_GPG_FINGERPRINT` | Full fingerprint of the OpenPGP upload key registered with Launchpad |
   | `PPA_GPG_PRIVATE_KEY_B64` | Base64-encoded ASCII-armored export of its private key |

   On your trusted Ubuntu machine, for a dedicated unattended key already
   installed at `~/.gnupg-ffmpeg-ppa`, you can retrieve both values:

   ```bash
   GPG_HOME="$HOME/.gnupg-ffmpeg-ppa"
   GPG_FPR="$(gpg --homedir "$GPG_HOME" --batch --with-colons --list-secret-keys | awk -F: '$1 == "fpr" { print $10; exit }')"
   printf 'PPA_GPG_FINGERPRINT=%s\n' "$GPG_FPR"
   gpg --homedir "$GPG_HOME" --batch --armor --export-secret-keys "$GPG_FPR" | base64 -w0
   echo
   ```

   **Never paste private keys into chat, commits, workflow logs, or issues.**
   The workflow assumes an unencrypted unattended CI key; if the private key
   is passphrase-protected, the signing command must be adapted with secure
   loopback passphrase handling. Prefer a dedicated revocable CI signing key.
4. Run [Publish to Launchpad PPA](https://github.com/AlexanderWagnerDev/ffmpeg-ubuntu/actions/workflows/publish-ppa.yml)
   on `main` using `series=resolute` and `revision=1`.
   The source package is built and validated in an unprivileged job; a
   separate Environment-gated job imports the GPG key, runs `debsign`, then
   `dput ppa:alexanderwagnerdev/ffmpeg`.

## After upload

An accepted source upload **does not guarantee a successful binary build**.
Review Launchpad's acceptance and per-architecture build logs and test an
installation in a disposable Ubuntu 26.04 system. If an already accepted
version needs to be re-uploaded after a packaging fix, increase `revision`.
The `noble` and `jammy` targets are experimental; they require separate
successful compatibility tests.

Once successful, a client can use:

```bash
sudo add-apt-repository ppa:alexanderwagnerdev/ffmpeg
sudo apt update
apt-cache policy ffmpeg
sudo apt -s install ffmpeg
```

Only after confirming package publication and installation should you enable
`PPA_AUTO_PUBLISH=true` in GitHub Actions repository **variables** for
scheduled uploads. Without that variable, the scheduled job does not publish.

## Packaging details

The source build obtains FFmpeg 9's Debian source package from the signed
Debian testing source index. For Ubuntu 26.04, it currently adjusts
`debhelper-compat (= 14)` to level 13 before creating the package.
A source build and an APT build-dependency simulation are **not** a substitute
for a successful Launchpad binary build.

This PPA upload method intentionally matches the one already used in
OpenRTMP/librtmp2. It uses only OpenPGP signing; GitHub Pages uses a separate
key for signing APT repository metadata.

- [Ubuntu Launchpad PPA upload documentation](https://ubuntu.com/docs/launchpad/user/how-to/packaging/ppa-package-upload/)
- [OpenRTMP's existing PPA workflow](https://github.com/OpenRTMP/librtmp2/blob/main/.github/workflows/publish-ppa.yml)
