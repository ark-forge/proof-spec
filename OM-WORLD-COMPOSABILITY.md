# OM World Execution Proof — Composability

[OM World's Execution Proof](https://github.com/omworldprotocol/om-world/blob/main/docs/execution-proof.md) defines a per-step record format that composes with this proof-spec and with [Compliance Receipts v0.1](https://github.com/corpollc/qntm/blob/main/specs/working-group/compliance-receipts.md). This document captures the mapping and the canonical step-hash JSON shape so implementations can interoperate without re-deriving the surface from scratch.

> Drafted by OM World for review against [`proof-spec/README.md` §Composability](README.md#composability). Per the dialogue in [#1](https://github.com/ark-forge/proof-spec/issues/1).

## Step record mapping

OM World's `Step record` (one per tool invocation) ↔ proof-spec / Compliance Receipts v0.1:

| proof-spec / CR v0.1 field | OM World Step record field | Notes |
|---|---|---|
| `previous_receipt_hash` (CR v0.1) | `prev_hash` | **Same role, same anchoring pattern.** Optional in OM World; required once any step in a proof carries it (partial chaining is invalid). First step's `prev_hash` anchors to the mandate's `plan_hash`. |
| `step.timestamp` (CR v0.1) / `timestamp` (proof-spec) | `timestamp` | ISO 8601 UTC. Direct mapping. |
| `hashes.request` (proof-spec) / `input_hash` (CR v0.1) | `input_hash` | SHA-256 of canonical input. |
| `hashes.response` (proof-spec) / `output_hash` (CR v0.1) | `output_hash` | SHA-256 of canonical output. |
| `signature` (CR v0.1) | *(envelope-level)* | OM World signs **at the envelope level** over all steps, not per step. Per-step `step_hash` values are recomputed by verifiers via JCS for `prev_hash` linkage. |
| *(no equivalent)* | `tool_id` | References the OM World Tool Registry entry. |
| *(no equivalent)* | `context_hash` | Optional snapshot hash for stateful tool calls — see [below](#worked-examples--stateless-vs-stateful-tools). |
| *(no equivalent)* | `attestation` | Tool-provided signature or TEE quote when available. |

**OM World's chained proof mode composes with the CR v0.1 pipeline format without additional fields.** A relying party that already consumes CR v0.1 can consume the chained subset of an OM World Execution Proof by reading the `prev_hash` chain directly.

## Canonical step hash

For `prev_hash` linkage, OM World defines:

```
step_hash = SHA-256(JCS(step_record_without_prev_hash))
```

Where:

- **JCS** is [RFC 8785 — JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785).
- `step_record_without_prev_hash` is the step record JSON object with the `prev_hash` field removed. (The field is excluded from its own step's hash input so it can *contain* the previous step's hash without circular dependency.)

### Absent-optional-fields rule

> Optional fields (`context_hash`, `attestation`) that are absent from a step **MUST be omitted** from the JCS input. They **MUST NOT** be serialized as `"<field>": null`.

This is load-bearing for interoperability. Two implementations that disagree on `null` vs. omit will produce divergent step hashes from identical step data, breaking interop before any signature is even checked. JCS itself is deterministic; the disagreement is upstream — at JSON-object construction time, not at canonicalization.

## Worked examples — stateless vs. stateful tools

These are the edge cases the canonicalization rule is designed to disambiguate. All three examples below share `tool_id`, `input_hash`, `output_hash`, and `timestamp`; they differ only in how `context_hash` is treated.

### Example 1 — stateless tool (`context_hash` absent)

A deterministic HTTP API call: the same input always yields the same output. `context_hash` is **absent** from the step record. It is **omitted** from the JCS input.

```json
{
  "tool_id": "http.get.v1",
  "input_hash": "9b74c9897bac770ffc029102a200c5de2c54f2d4ad6c2f8e2e8c4d3a8b7c6d5e",
  "output_hash": "fcde2b2edba56bf408601fb721fe9b5c0a3b7c8d9e0f1a2b3c4d5e6f7a8b9c0d",
  "timestamp": "2026-05-22T10:00:00Z"
}
```

`step_hash = SHA-256(JCS(<the above object>))`.

### Example 2 — stateful tool (`context_hash` present)

A memory-store query: the same query against different store states yields different results. `context_hash` carries the snapshot identity at call time. It is **present** in the canonical record.

```json
{
  "tool_id": "memory.query.v1",
  "input_hash": "9b74c9897bac770ffc029102a200c5de2c54f2d4ad6c2f8e2e8c4d3a8b7c6d5e",
  "output_hash": "fcde2b2edba56bf408601fb721fe9b5c0a3b7c8d9e0f1a2b3c4d5e6f7a8b9c0d",
  "context_hash": "a3b9c1d8e4f2a6b8c0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f0a2b4c6d8e0f2a4b6",
  "timestamp": "2026-05-22T10:00:00Z"
}
```

`step_hash = SHA-256(JCS(<the above object>))` — a **different** hash from Example 1. This is expected: the canonical inputs genuinely differ.

### Anti-pattern — `"context_hash": null` (NOT conformant)

A non-conformant implementation might serialize an absent `context_hash` as `null`:

```json
{
  "tool_id": "http.get.v1",
  "input_hash": "9b74c9897bac770ffc029102a200c5de2c54f2d4ad6c2f8e2e8c4d3a8b7c6d5e",
  "output_hash": "fcde2b2edba56bf408601fb721fe9b5c0a3b7c8d9e0f1a2b3c4d5e6f7a8b9c0d",
  "context_hash": null,
  "timestamp": "2026-05-22T10:00:00Z"
}
```

This object is **not equivalent** to Example 1 under JCS: the explicit `null` member is present in the canonical output, so its `step_hash` differs from Example 1's. Two implementations that diverge on this choice will silently reject each other's proofs. Hence the rule.

## `plan_hash` pre-commitment (first step in chained mode)

When chained proof mode is enabled, the **first** step in a proof anchors its `prev_hash` to the mandate's `plan_hash` — the value **pre-committed in the intent record before execution begins**, not a hash the agent computes at proof time. This binds the chain to what was authorized; a compromised agent that swapped the plan post-hoc cannot produce a valid-looking chain anchored to the original `plan_hash`.

## Cross-reference

- OM World Execution Proof spec: [`docs/execution-proof.md`](https://github.com/omworldprotocol/om-world/blob/main/docs/execution-proof.md)
- §Step record — field list: [`docs/execution-proof.md#step-record`](https://github.com/omworldprotocol/om-world/blob/main/docs/execution-proof.md#step-record)
- §Canonicalization — the `step_hash` formula and the absent-optional-fields rule: [`docs/execution-proof.md#canonicalization`](https://github.com/omworldprotocol/om-world/blob/main/docs/execution-proof.md#canonicalization)
- §`prev_hash` chained proof mode — including the `plan_hash` pre-commitment: [`docs/execution-proof.md#prev_hash--chained-proof-mode`](https://github.com/omworldprotocol/om-world/blob/main/docs/execution-proof.md#prev_hash--chained-proof-mode)
