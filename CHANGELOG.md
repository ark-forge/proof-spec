# Changelog

All notable changes to this specification will be documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

---

## [Unreleased]

---

## [2.1.3] — 2026-03-24

### Added
- `parties.did_resolution_status` optional string field. Values: `"bound"` (DID verified via Ed25519 challenge-response at registration time), `"unverified"` (caller-declared identity without cryptographic verification). Absent if no `agent_identity` is provided. Included in public unauthenticated proof responses.

---

## [2.1.2] — 2026-03-24

### Added
- `parties.agent_identity_verified` optional bool field — `true` when `agent_identity` is a cryptographically verified DID bound to the API key via Ed25519 challenge-response. Absent if self-declared.
- README: composability section documenting field mapping between proof-spec and Compliance Receipts v0.1 (qntm WG spec)

### Changed
- `parties.agent_identity` description clarified: documents DID binding override behaviour (verified DID takes precedence over caller-declared value)
- Section 9: `agent_identity_verified` included in public unauthenticated responses

---

## [2.1.1] — 2026-03-23

### Added
- Section 6: document `GET /.well-known/did.json` as a second canonical key distribution endpoint — W3C DID Document (`did:web:trust.arkforge.tech`) with `Ed25519VerificationKey2020` and `publicKeyJwk`

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

[Unreleased]: https://github.com/ark-forge/proof-spec/compare/v2.1.2...HEAD
[2.1.2]: https://github.com/ark-forge/proof-spec/compare/v2.1.1...v2.1.2
[2.1.1]: https://github.com/ark-forge/proof-spec/compare/v2.1.0...v2.1.1
[2.1.0]: https://github.com/ark-forge/proof-spec/compare/v1.2.0...v2.1.0
[1.2.0]: https://github.com/ark-forge/proof-spec/compare/v1.0.0...v1.2.0
[1.0.0]: https://github.com/ark-forge/proof-spec/releases/tag/v1.0.0
