# Changelog

All notable changes to this specification will be documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

---

## [Unreleased]

---

## [2.1.0] — 2026-03-11

### Added
- `rekor` field — Sigstore Rekor immutable log anchor
- `timestamp_authority` field — RFC 3161 TSA reference
- `agent_identity` optional field — identifier for the calling system

### Changed
- `chain_hash` now covers request + response + timestamp bundle

## [1.2.0] — 2026-01-15

### Added
- `hashes.chain` field — tamper-evident combined hash
- `parties.seller` field — domain of the called API

## [1.0.0] — 2025-11-01

### Added
- Initial proof format specification
- `proof_id`, `hashes.request`, `hashes.response` fields
- Ed25519 signature by independent third party
- RFC 3161 timestamp

[Unreleased]: https://github.com/ark-forge/proof-spec/compare/v2.1.0...HEAD
[2.1.0]: https://github.com/ark-forge/proof-spec/compare/v1.2.0...v2.1.0
[1.2.0]: https://github.com/ark-forge/proof-spec/compare/v1.0.0...v1.2.0
[1.0.0]: https://github.com/ark-forge/proof-spec/releases/tag/v1.0.0
