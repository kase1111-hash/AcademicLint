# Security Policy

## Supported Versions

The following versions of AcademicLint are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take the security of AcademicLint seriously. If you believe you have found a security vulnerability, please report it to us responsibly.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to:

**Email:** kase1111@gmail.com

Include the following information in your report:

1. **Description** - A clear description of the vulnerability
2. **Impact** - The potential impact of the vulnerability
3. **Reproduction Steps** - Step-by-step instructions to reproduce the issue
4. **Affected Versions** - Which versions are affected
5. **Potential Fix** - If you have suggestions for how to fix the issue (optional)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your report within 48 hours
- **Initial Assessment**: We will provide an initial assessment within 7 days
- **Resolution Timeline**: We aim to resolve critical vulnerabilities within 30 days
- **Credit**: If desired, we will credit you in our security advisories and CHANGELOG

### Security Considerations for AcademicLint

#### Local Mode (Default)

When running in local mode:
- All text processing occurs on your machine
- No data is transmitted to external servers
- Models are stored locally after initial download

#### API Mode

When using the REST API:
- Text is transmitted to the server for processing
- Data is not stored beyond the request lifetime
- Data is not used for training purposes
- See [PRIVACY.md](./PRIVACY.md) for full details

#### Self-Hosted Deployments

For self-hosted deployments:
- Follow the security guidelines in [docs/self-hosting.md](./docs/self-hosting.md)
- Keep dependencies updated
- Use TLS/HTTPS in production
- Implement appropriate access controls

### Known Security Considerations

- **Model Downloads**: Initial setup downloads models from external sources. Verify checksums if required for your security policy.
- **File System Access**: The CLI tool reads files from paths provided by users. Ensure appropriate file permissions.
- **API Authentication**: When using the REST API, always use HTTPS and protect API keys.

## Security Updates

Security updates are announced through:
- GitHub Security Advisories
- CHANGELOG.md
- Release notes

## Scope

This security policy applies to:
- The AcademicLint Python package
- The official CLI tool
- The official REST API server component
- Official documentation

Third-party integrations, plugins, or forks are not covered by this policy.

## Thank You

We appreciate your help in keeping AcademicLint and its users safe.
