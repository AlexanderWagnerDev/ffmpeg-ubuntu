# Launchpad PPA setup

**Important:** The project at https://launchpad.net/awdev-ffmpeg and a Personal Package Archive are **different Launchpad resources**. Publishing to the project page does not create an APT repository.

## 1. Create the PPA

Sign in as `alexanderwagnerdev` and create a PPA with URL name `ffmpeg`.

Expected PPA page (only after it has been created):

https://launchpad.net/~alexanderwagnerdev/+archive/ubuntu/ffmpeg

Enable the desired processors in the PPA settings (at least amd64; arm64 where available). Confirm that `resolute` is accepted by Launchpad before publishing. The first upload must be reviewed for compatibility and license/build-dependency constraints.

## 2. Register signing and SSH identities

Generate a **dedicated** OpenPGP signing key/subkey for CI and register its **public** key with Launchpad. Import a dedicated SSH **public** key into your Launchpad account, and validate the SSH server host key out of band before creating the known_hosts secret. Never paste private keys into issues, chats, commits or Actions logs.

Create the GitHub Environment `launchpad-ppa`. Prefer required reviewers. Add four **environment secrets**:

| Name | Value |
|---|---|
| PPA_GPG_PRIVATE_KEY_B64 | Base64 of the ASCII-armored CI OpenPGP private key |
| PPA_GPG_FINGERPRINT | Full public fingerprint registered with Launchpad |
| PPA_SSH_PRIVATE_KEY | Dedicated unencrypted CI Ed25519 private SSH key |
| PPA_SSH_KNOWN_HOSTS | Verified known_hosts entry for ppa.launchpad.net |

The example workflow assumes a dedicated unattended OpenPGP signing key that does **not** prompt for a passphrase. A passphrase-protected key needs a separately audited noninteractive signing configuration. Restrict repository/environment access appropriately and rotate keys if compromised.

Do not enable publication before the actual PPA exists and the keys are registered.

## 3. Build and publish

1. Run **Build Ubuntu source package** for `resolute`.
2. Download the unsigned `ffmpeg-source-resolute` artifact. Review changelog, Debian build dependencies and source archives.
3. Check that all required build dependencies are available in the target Ubuntu release. **Producing a .dsc does not prove that Launchpad can compile FFmpeg 9.**
4. Run **Publish to Launchpad PPA** after setting the Environment secrets.
5. Check Launchpad's build logs for both architectures and test installation/upgrade in a disposable Ubuntu VM.

For each repeat upload of an already accepted Debian source version, **increase the revision** (Launchpad rejects reusing a version). Building on `jammy` or `noble` is *experimental* until compatibility has been verified.

After the package is published, clients can install with:

```bash
sudo add-apt-repository ppa:alexanderwagnerdev/ffmpeg
sudo apt update
apt-cache policy ffmpeg
sudo apt -s install ffmpeg
```

If Ubuntu Pro/ESM or another repository wins APT's version/pinning comparison, inspect `apt-cache policy ffmpeg` and configure an explicit targeted policy rather than disabling security updates globally.

## Package provenance

Build scripts obtain the FFmpeg 9 **Debian source package** from the **signed Debian testing source index**, then add an Ubuntu changelog entry and create a source upload. The Debian packaging and upstream source are not committed here and can change independently. Review the inherited build flags, multimedia codec availability, copyright, and Debian patches before any publication. No Ubuntu-specific ABI compatibility is promised by this wrapper.

Helpful official documentation:
- https://ubuntu.com/docs/launchpad/user/PPA/
- https://ubuntu.com/docs/launchpad/user/how-to/packaging/ppa-package-upload/
- https://ubuntu.com/docs/launchpad/user/how-to/import-ssh-keys/
