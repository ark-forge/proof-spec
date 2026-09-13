# Changelog

All notable changes to this specification will be documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

---

## [Unreleased]

---

## [3.1.0] — 2026-09-13

### Added
- **`parties.agent_identity`, `parties.agent_identity_verified` and
  `parties.did_resolution_status` are now committed chain fields**, unconditionally: an
  absent identity is committed as `null`. Up to 3.0 the three were served in public proof
  responses (§9) but committed nowhere, so they sat outside the Merkle root, outside
  `hashes.chain`, outside the Ed25519 signature and therefore outside the RFC 3161 token
  and the Rekor entry. An attestor could restate an agent's identity after anchoring and
  every external witness still verified. Any party reading `agent_identity_verified` as
  evidence was reading the attestor's unbacked word.
- **`disclosed`**: the identity triple's `(nonce, value)` pairs, published in the proof
  itself. These three nonces are public so that anyone can open the triple and check the
  served values against the anchored commitments. Hiding is given up on these three
  fields and on no other; every remaining nonce stays secret.
- Test vectors 13 and 14 (`identity_verified_did`,
  `identity_absent_is_committed_as_null`), with their `published_nonces`.

### Changed
- `agent_identity_verified` is `true` or `null`, never `false`. One normalisation at the
  source, so the committed value and the served value cannot disagree.
- §9: for `spec_version` `"3.1"`, `disclosed` MUST be included in public responses.

### Notes
- `agent_version` is deliberately NOT committed: it carries no verifiable claim.
- Anchoring the triple makes the identity claim **non-repudiable**; it does not make the
  binding itself third-party verifiable. No public artefact proves the Ed25519
  challenge-response happened. A verifier needing more MUST resolve the DID itself.
- Proofs at `spec_version` `"3.0"` and below keep their algorithm and stay verifiable.
  Their identity fields carry no anchor and MUST NOT be treated as evidence.

---

## [3.0.0] — 2026-09-13

### Changed
- **BREAKING (new proofs only): `hashes.chain` is now the RFC 6962 Merkle root of one
  commitment per chain field**, `SHA256(field || 0x00 || nonce || canonical_json(value))`,
  with 32 fresh random bytes of nonce per field and per proof. Proofs published under
  spec_version `"1.1"`, `"1.2"`, `"2.0"` and `"2.1"` keep their own algorithm: nothing is
  recomputed or re-anchored retroactively.

  The reason is third-party verifiability. Up to 2.1 the chain hash was computed over the
  values, and a public proof redacts `transaction_id` and `buyer_fingerprint` — so a third
  party could not recompute the anchored hash, and the published procedure reported
  TAMPERED against an honest issuer. A proof now publishes every commitment and no value.
- `spec_version` is no longer informational: it selects the chain hash algorithm.

### Added
- `commitments`: one commitment per committed field, published in full.
- **Selective disclosure**: the owner opens any single field by handing over its
  `(nonce, value)` pair out of band; the counterparty checks it against the published
  commitment. Field name and per-field nonce are in the preimage, so a commitment cannot
  be moved between fields and disclosing one field reveals nothing about a low-entropy
  neighbour.
- **Section 2.2 — batch anchoring**: external anchors MAY cover the Merkle root of a batch
  of proofs, each proof carrying its own inclusion proof (`batch_anchor`). Verifiers MUST
  check the audit path length against the length `tree_size` requires — an overstated
  `tree_size` is otherwise accepted, the walk reaching the real root and stopping early.
- **Pending state**: a proof whose batch has not closed has no external anchor.
  `batch_anchor.status: "pending"` MUST be reported as waiting, never as tampering.
- Test vectors 10-12: two per-field commitment vectors with fixed nonces, one batch-anchor
  vector with the root and an inclusion path per leaf. `check_consistency.py` recomputes
  all three from an independent implementation of the primitives.

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
