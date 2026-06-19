# Security policy

We take the security of `jina-reranker-api` seriously. Thanks for helping
us keep it safe.

## Supported versions

Security fixes are issued for the latest published `0.x` release.
Older `0.x` releases receive only critical-severity fixes on a
best-effort basis.

| Version | Status |
|---|---|
| `0.x` (latest) | ✅ supported |
| Older `0.x` | 🟡 critical fixes only |

A separate policy will be added once a stable `1.0` ships.

## Reporting a vulnerability

**Do not open a public issue for security problems.**

Please report vulnerabilities through GitHub's
[Private Vulnerability Reporting](https://github.com/Fidonis/jina-reranker-api/security/advisories/new).
This routes the report directly to the maintainers in a private
advisory.

If for some reason you cannot use the private reporting flow, contact
the maintainers at `security@fidonis.de` and we will open the private
advisory on your behalf.

Please include:

- A clear description of the vulnerability and its impact
- Steps to reproduce (a minimal proof of concept is ideal)
- The version / commit affected
- Any suggested mitigation or fix, if you have one

## What to expect

- **Acknowledgement** within 3 working days of your report.
- **Initial triage** (severity assessment, confirmation, scope) within
  10 working days.
- **Coordinated disclosure**: once a fix is ready, we publish a GitHub
  Security Advisory and a patched release. Embargo periods are agreed
  with the reporter on a case-by-case basis; 90 days is the default
  upper bound.
- **Credit**: with your permission, your name (or handle) is listed in
  the advisory and the release notes.

## Out of scope

- Vulnerabilities in third-party software listed under
  [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md) — please report
  those to the respective upstream project. We will, of course, ship an
  updated dependency as soon as a fix is available.
- Issues that require attacker-controlled LiteLLM configuration
  (configuring the server to point at a malicious LiteLLM instance is
  equivalent to compromising the infrastructure layer; this is outside
  the scope of this project).

Anything else, including subtle authentication and authorization bugs,
is in scope and we want to hear about it.
