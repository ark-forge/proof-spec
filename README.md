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

[`test-vectors.json`](test-vectors.json) contains 7 test cases (minimal, empty, unicode, with_upstream_timestamp, free_tier, with_receipt_content_hash, with_upstream_and_receipt). Any conformant implementation MUST pass all vectors.

## Roadmap

The proof format will evolve to support third-party provider attestations and multi-PSP payment verification. See the [Trust Layer roadmap](https://github.com/ark-forge/trust-layer/blob/main/ROADMAP.md) for the full architecture.

## License

[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
