# Security Policy

Report vulnerabilities privately using GitHub's **Report a vulnerability**
feature in the repository's Security tab (if enabled), rather than publishing
credential details or proof-of-concept exploits in an issue.

CI signing credentials must be stored only as GitHub Environment secrets.
Do not commit personal OpenPGP private keys, SSH private keys, or access tokens.
Rotate affected credentials immediately if exposed.

FFmpeg and Debian source-package vulnerabilities should also be reported to
their relevant upstream security processes.
