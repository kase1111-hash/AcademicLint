# AcademicLint Privacy Policy

**Last Updated:** January 2026

This privacy policy explains how AcademicLint handles your data in both local and API modes.

---

## Overview

AcademicLint is designed with privacy as a core principle. By default, **all processing happens locally on your machine**, and no data is transmitted to external servers.

---

## Local Mode (Default)

### What Data Is Processed

When you run AcademicLint locally:
- Your text files are read from disk
- Text is analyzed by locally-running models
- Results are output to your terminal or saved locally

### What Data Is Stored

- **Configuration files** (`.academiclint.yml`) you create
- **Cache files** for performance optimization (stored in `~/.cache/academiclint/`)
- **Downloaded models** (stored in `~/.local/share/academiclint/models/`)

### What Data Is Transmitted

In local mode, **no data is transmitted** to AcademicLint servers or any third party.

### Network Requests

Local mode may make network requests only for:
- **Model downloads** (first run only, from our CDN)
- **Update checks** (optional, can be disabled)

To disable all network access:
```bash
academiclint --offline check paper.md
```

Or in configuration:
```yaml
# .academiclint.yml
network:
  offline_mode: true
  check_updates: false
```

---

## API Mode (Opt-In)

If you choose to use the cloud API service, additional terms apply.

### What Data Is Transmitted

When using the API:
- The text you submit for analysis
- Your API key for authentication
- Basic request metadata (timestamp, request ID)

### What Data Is NOT Collected

- Your IP address (not logged)
- Personal identifying information
- Usage patterns or analytics
- File names or paths

### Data Retention

| Data Type | Retention Period |
|-----------|------------------|
| Submitted text | Not stored (processed in memory only) |
| API logs | 7 days (for debugging, no text content) |
| Error reports | 30 days (sanitized, no user text) |
| Billing records | As required by law |

### Data Processing

- Text is processed in memory and **immediately discarded** after response
- We do **not** store your submitted text
- We do **not** use your text for model training
- We do **not** share your data with third parties

### Security Measures

- All API traffic encrypted via TLS 1.3
- API keys hashed and salted in storage
- Infrastructure hosted on SOC 2 compliant providers
- Regular security audits and penetration testing

---

## Self-Hosted Deployment

For organizations with strict data requirements, AcademicLint can be self-hosted:

```bash
docker run -p 8080:8080 academiclint/server:latest
```

When self-hosting:
- All data remains within your infrastructure
- No data is transmitted to AcademicLint
- You control all logging and retention policies

See our [Self-Hosting Guide](./docs/self-hosting.md) for deployment instructions.

---

## Editor Extensions

### VS Code Extension

- Processes text locally using bundled analysis engine
- No data transmitted unless you explicitly enable cloud features
- Extension settings stored in VS Code's standard settings location

### Obsidian Plugin

- All processing happens locally within Obsidian
- No network requests made
- Plugin data stored in your vault's `.obsidian/` folder

---

## Telemetry

### Default: Off

AcademicLint does **not** collect telemetry by default.

### Optional Telemetry

You may opt-in to anonymous usage statistics to help improve the product:

```yaml
# .academiclint.yml
telemetry:
  enabled: true  # Default: false
```

If enabled, we collect only:
- AcademicLint version
- Operating system type (not version)
- Aggregate feature usage counts
- Error types (not content)

We never collect:
- Your text content
- File names or paths
- Personal information
- IP addresses

---

## Third-Party Services

AcademicLint may interact with these third-party services:

| Service | Purpose | Data Shared |
|---------|---------|-------------|
| GitHub | Update checks, issue reporting | Version number only |
| CDN (Cloudflare) | Model downloads | IP address (standard CDN logs) |
| Sentry (optional) | Error reporting | Stack traces (no user data) |

You can disable all third-party connections with offline mode.

---

## Children's Privacy

AcademicLint does not knowingly collect information from children under 13. The service is intended for academic and professional use.

---

## International Users

### GDPR Compliance (EU Users)

If you are in the European Union:
- **Data Controller:** AcademicLint project maintainers
- **Legal Basis:** Legitimate interest (providing the service)
- **Your Rights:** Access, rectification, erasure, portability, objection

To exercise your rights, contact: kase1111@gmail.com

### Data Location

- Local mode: Data never leaves your machine
- API mode: Processing occurs in US-based data centers
- Self-hosted: Data location determined by your deployment

---

## Data Deletion

### Local Mode

Delete all AcademicLint data:
```bash
rm -rf ~/.cache/academiclint/
rm -rf ~/.local/share/academiclint/
rm ~/.config/academiclint/
```

### API Mode

To delete your API account and associated data:
1. Email kase1111@gmail.com with your request
2. Include the email associated with your API key
3. Deletion completed within 30 days

---

## Changes to This Policy

We may update this privacy policy from time to time. Changes will be posted to this repository with an updated "Last Updated" date.

For significant changes, we will:
- Update the version number
- Note changes in the CHANGELOG
- Announce via GitHub releases

---

## Contact

For privacy-related questions or concerns:

- **Email:** kase1111@gmail.com
- **GitHub Issues:** [Privacy-related issues](https://github.com/kase1111-hash/academiclint/issues)

---

## Summary

| Mode | Data Transmitted | Data Stored Remotely |
|------|------------------|---------------------|
| Local (default) | None | None |
| API (opt-in) | Submitted text | None (processed in memory) |
| Self-hosted | None | Your infrastructure |

**Bottom line:** In default local mode, your data never leaves your machine. We built AcademicLint for people who care about privacy—including ourselves.
