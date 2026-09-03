# ArkForge Proof Specification

Open standard for verifiable agent-to-agent execution proofs.

**[Read the spec](SPEC.md)** | **[Test vectors](test-vectors.json)**

## What is this?

A deterministic proof format that binds a request, response, payment, and timestamp into a single SHA-256 chain hash. Anyone can verify a proof without ArkForge's code or infrastructure.

## Quick verification

Given a proof JSON, verify it in one line:

```bash
printf '%s' "${REQUEST_HASH}${RESPONSE_HASH}${PAYMENT_ID}${TIMESTAMP}${BUYER}${SELLER}${UPSTREAM}${RECEIPT_HASH}" \
  | sha256sum | cut -d' ' -f1
```

`UPSTREAM` and `RECEIPT_HASH` are empty strings when absent from the proof.

If the result matches `proof.hashes.chain`, the proof is intact.

## Implementations

| Implementation | Language | Status |
|---------------|----------|--------|
| [ArkForge Trust Layer](https://github.com/ark-forge/trust-layer) | Python | Reference implementation |

Want to add yours? Open a PR.

## Test vectors

[`test-vectors.json`](test-vectors.json) contains 9 test cases (7 legacy string-concatenation vectors + 2 canonical-JSON vectors for spec_version 1.2/2.1). Any conformant implementation MUST pass all vectors.

## Composability

The proof-spec is the cryptographic foundation for the [Compliance Receipts v0.1](https://github.com/corpollc/qntm/blob/main/specs/working-group/compliance-receipts.md) spec drafted by the [qntm Working Group](https://github.com/corpollc/qntm/tree/main/specs).

Field mapping:

| proof-spec field | Compliance Receipts v0.1 field | Notes |
|-----------------|-------------------------------|-------|
| `proof_id` | `receipt_id` | Same role: unique receipt identifier |
| `hashes.request` | `input_hash` | SHA-256 of canonical JSON (identical algorithm) |
| `hashes.response` | `output_hash` | SHA-256 of canonical JSON (identical algorithm) |
| `timestamp` | `step.timestamp` | ISO 8601 UTC |
| `parties.agent_identity` + `parties.agent_identity_verified` + DID endpoint | `step.agent_did` | `agent_identity` carries the verified DID when `agent_identity_verified: true`; `did:web:trust.arkforge.tech` resolves to the Ed25519 signing key |
| `arkforge_signature` | `signature` | Ed25519 — signs the chain hash (proof-spec) vs. canonical receipt (CR v0.1) |
| `hashes.chain` | no equivalent | Additional witness: binds payment + identity + request + response into one sealed hash |

Fields in Compliance Receipts v0.1 with no proof-spec equivalent (`pipeline_id`, `step.index`, `step.role`, `previous_receipt_hash`, `policy`) are pipeline context provided by the calling agent, not derived by the proxy.

### OM World Execution Proof

[OM World's per-step Execution Proof](https://github.com/omworldprotocol/om-world/blob/main/docs/execution-proof.md) composes with proof-spec and CR v0.1 via the chained `prev_hash` mechanism: `previous_receipt_hash` (CR v0.1) is structurally equivalent to OM World's `prev_hash`, and `step.timestamp` maps directly. See [`OM-WORLD-COMPOSABILITY.md`](OM-WORLD-COMPOSABILITY.md) for the full field mapping, the canonical `step_hash` formula, and the JSON examples for the stateless vs. stateful `context_hash` edge case.

## Roadmap

The proof format will evolve to support third-party provider attestations and multi-PSP payment verification. See the [Trust Layer roadmap](https://github.com/ark-forge/trust-layer/blob/main/ROADMAP.md) for the full architecture.

## License

[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
