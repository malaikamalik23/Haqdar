# Security policy

Haqdar helps people understand official notices, so privacy and safety come first. It is a hackathon project looked after by two people, so reports are handled on a best-effort basis.

## Report a vulnerability

Please **do not open a public issue** for a security problem.

1. Open the repository's **Security** tab and choose **Report a vulnerability** (GitHub private vulnerability reporting).
2. Describe what you found, how to reproduce it, and what you think the impact is.
3. Use made-up data only. Never send real CNIC numbers, phone numbers or real notices.

We aim to acknowledge a report within 7 days and to say what we plan to do within 14 days.

## In scope

- The API (`backend/`), the web app (`web/`), the container setup and the CI workflows.
- Anything that could expose personal data, run code on the server, get past the upload checks, the size limits or the rate limits, or make the app show harmful content.
- A procedure pack that links to a site that is not official. (A pack with outdated or unclear steps is a content problem: please open a normal issue.)

## Out of scope

- Attacks that need a computer that is already compromised.
- Denial of service from many machines at once.
- Weak settings on a server you set up yourself.
- Reports that only say a header or setting is "missing" without showing a real effect.
- Testing with anyone's real personal data.

## Supported versions

Only the latest commit on `main`.

## Please

- Do not run automated scans against a server you do not own.
- Give us a reasonable time to fix a problem before you tell others about it.

## How Haqdar protects people

A summary is in the [README](README.md#privacy-and-security-by-design). The full list of threats, defences and known gaps is in the [threat model](docs/threat-model.md).
