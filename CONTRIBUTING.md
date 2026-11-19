# Contributing

Thank you for helping maintain FFmpeg Ubuntu packaging.

- Open an issue with the Ubuntu release, architecture, upstream FFmpeg version,
  APT dependency error, and relevant Launchpad build log link.
- Keep upstream FFmpeg source and Debian packaging provenance intact unless a
  narrowly scoped, reviewed Ubuntu patch is required.
- Run `python3 -m unittest discover -s tests -v`, `bash -n scripts/*.sh`,
  and `shellcheck scripts/*.sh` before submitting a pull request.
- Never include private keys, tokens, personal credentials, or private build logs.
- Changes to release or publishing automation require careful review because
  only signed source uploads are accepted by Launchpad.
