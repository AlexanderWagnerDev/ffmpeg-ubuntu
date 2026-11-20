# Contributing

Thanks for your interest in improving FFmpeg packaging for Ubuntu.

## Reporting problems

Open a GitHub issue with your Ubuntu version, architecture, FFmpeg package version, the repository you installed from, and the relevant APT or runtime output. Link to a failed build if applicable.

Use [private security reporting](SECURITY.md) for vulnerabilities or sensitive information.

## Pull requests

- Keep each change focused on Ubuntu packaging, compatibility, CI, tests, or documentation.
- Preserve upstream FFmpeg and Debian packaging provenance and license notices.
- Add regression tests for changes to dependency generation or versioning.
- Do not commit generated binaries, signing keys, tokens, or private data.

Before submitting:

```bash
python3 -m unittest discover -s tests -v
bash -n scripts/*.sh
shellcheck scripts/*.sh
```

FFmpeg source-code defects belong in the upstream FFmpeg project; this repository focuses on distributing Ubuntu packages.
