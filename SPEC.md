# ArkForge Proof Specification v1.1.0

An open standard for verifiable agent-to-agent execution proofs.

## Status

**Draft** — seeking co-implementers. Feedback welcome via [GitHub Issues](https://github.com/ark-forge/proof-spec/issues).

## Goal

Define a deterministic, independently verifiable proof format for agent-to-agent transactions. Any party — buyer, seller, auditor, regulator — can recompute and verify a proof without ArkForge's code or infrastructure.

## Scope

This spec covers:
- Proof structure (JSON)
- Chain hash algorithm (SHA-256)
- Canonical JSON serialization
- Buyer fingerprint derivation
- Independent verification procedure
- Test vectors

This spec does NOT cover:
- Payment processing (Stripe, crypto, etc.)
- Transport protocol (HTTP, MCP, etc.)
- Timestamping backends (RFC 3161, etc.)
- Storage format or retention policy

## 1. Proof structure

A conformant proof is a JSON object with these required fields:

```json
{
  "proof_id": "prf_20260225_170950_fdec72",
  "spec_version": "1.0",
  "timestamp": "2026-02-25T17:09:47Z",
  "hashes": {
    "request": "sha256:<hex>",
    "response": "sha256:<hex>",
    "chain": "sha256:<hex>"
  },
  "parties": {
    "buyer_fingerprint": "<hex>",
    "seller": "example.com"
  },
  "payment": {
    "provider": "stripe",
    "transaction_id": "pi_...",
    "amount": 0.50,
    "currency": "eur",
    "status": "succeeded"
  },
  "arkforge_signature": "ed25519:<base64url>",
  "arkforge_pubkey": "ed25519:<base64url>",
  "verification_url": "https://..."
}
```

### Payment field variants

The `payment` object reflects how the proof was generated:

| Plan | `provider` | `transaction_id` | `amount` | `status` |
|------|-----------|-----------------|----------|----------|
| Pro | `"stripe"` | Stripe Payment Intent ID (`pi_...`) | `> 0` | `"succeeded"` |
| Free | `"none"` | `"free_tier"` | `0.0` | `"free_tier"` |

Both variants produce a valid chain hash. The `transaction_id` value (`pi_...` or `free_tier`) is used as-is in the chain hash computation.

### Optional fields

| Field | Type | Description |
|-------|------|-------------|
| `spec_version` | string | Proof format version (e.g. `"1.0"`). Informational for auditors |
| `upstream_timestamp` | string | Upstream service's HTTP `Date` header (RFC 7231 format). Included in chain hash when present |
| `arkforge_signature` | string | Ed25519 signature of the chain hash. Format: `ed25519:<base64url_without_padding>` |
| `arkforge_pubkey` | string | Ed25519 public key used for signing. Format: `ed25519:<base64url_without_padding>` |
| `parties.agent_identity` | string | Agent's self-declared name |
| `parties.agent_version` | string | Agent's version string |
| `identity_consistent` | bool/null | Whether identity matches previous calls with same key |
| `timestamp_authority` | object | TSA status, provider, download URL, and `tsr_base64` (base64-encoded .tsr file) |
| `archive_org` | object | Archive.org snapshot status and URL |
| `verification_algorithm` | string | URL to algorithm documentation |

## 2. Chain hash algorithm

The chain hash binds every element of a transaction into a single verifiable seal.

### Formula

```
chain_hash = SHA256(request_hash + response_hash + payment_intent_id + timestamp + buyer_fingerprint + seller [+ upstream_timestamp])
```

### Definitions

| Component | Derivation |
|-----------|-----------|
| `request_hash` | `SHA256(canonical_json(request_data))` |
| `response_hash` | `SHA256(canonical_json(response_data))` |
| `payment_intent_id` | Payment transaction ID: Stripe Payment Intent ID (e.g. `pi_3T4ovu...`) for Pro, or `free_tier` for Free plan |
| `timestamp` | ISO 8601 UTC string (e.g. `2026-02-25T17:09:47Z`) |
| `buyer_fingerprint` | `SHA256(api_key)` — the raw API key string, not the proof field |
| `seller` | Target domain (e.g. `arkforge.fr`) |
| `upstream_timestamp` | Upstream service's HTTP `Date` header (optional — only included when the field is present and non-null in the proof JSON) |

### Concatenation

All values are concatenated as raw UTF-8 strings with **no separator** before hashing.

```
# Without upstream_timestamp (legacy proofs, or when upstream didn't return a Date header):
input = request_hash + response_hash + payment_intent_id + timestamp + buyer_fingerprint + seller

# With upstream_timestamp (when the field is present and non-null in the proof JSON):
input = request_hash + response_hash + payment_intent_id + timestamp + buyer_fingerprint + seller + upstream_timestamp

chain_hash = sha256(input.encode("utf-8")).hexdigest()
```

### Backward compatibility

The discriminant is **presence of the `upstream_timestamp` field** in the proof JSON. If the field is absent or null, use the original 6-component formula. If present and non-null, append it as a 7th component. Do **not** use `spec_version` for this decision (avoids string comparison pitfalls like `"1.10" < "1.9"`).

## 3. Canonical JSON

Canonical JSON ensures deterministic hashing regardless of key order or whitespace.

### Rules

1. Keys sorted alphabetically (`sort_keys=True`)
2. No whitespace between elements (`separators=(",", ":")`)
3. Default JSON encoding for non-ASCII characters (Unicode escapes)
4. No trailing newline

### Reference implementation (Python)

```python
import json

def canonical_json(data: dict) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
```

### Examples

| Input | Canonical form |
|-------|---------------|
| `{"b": 1, "a": 2}` | `{"a":2,"b":1}` |
| `{"key": "value"}` | `{"key":"value"}` |
| `{}` | `{}` |
| `{"x": [1, 2]}` | `{"x":[1,2]}` |
| `{"café": true}` | `{"caf\u00e9":true}` |

## 4. Buyer fingerprint

The buyer fingerprint is a SHA-256 hash of the raw API key string. This allows verification without exposing the actual key.

```
buyer_fingerprint = SHA256("mcp_test_example_key")
                  = "7c8f263e06d5ce4681f750ad64ede882a4ebd87de60f9ae0e6b06f0300645a11"
```

## 5. Independent verification

Given a proof JSON, any party can verify integrity:

```bash
# 1. Extract components
REQUEST_HASH=$(echo "$PROOF" | jq -r '.hashes.request' | sed 's/sha256://')
RESPONSE_HASH=$(echo "$PROOF" | jq -r '.hashes.response' | sed 's/sha256://')
PAYMENT_ID=$(echo "$PROOF" | jq -r '.payment.transaction_id')
TIMESTAMP=$(echo "$PROOF" | jq -r '.timestamp')
BUYER=$(echo "$PROOF" | jq -r '.parties.buyer_fingerprint')
SELLER=$(echo "$PROOF" | jq -r '.parties.seller')

# 2. Recompute chain hash
COMPUTED=$(printf '%s' "${REQUEST_HASH}${RESPONSE_HASH}${PAYMENT_ID}${TIMESTAMP}${BUYER}${SELLER}" | sha256sum | cut -d' ' -f1)

# 3. Compare
EXPECTED=$(echo "$PROOF" | jq -r '.hashes.chain' | sed 's/sha256://')
[ "$COMPUTED" = "$EXPECTED" ] && echo "VERIFIED" || echo "TAMPERED"
```

If the chain hash matches, no field in the proof was altered after creation.

### What verification proves

- The request/response pair is authentic (hashes match)
- The payment ID is bound to this specific execution
- The timestamp is bound to this specific execution
- No field was modified after proof creation

### What verification does NOT prove

- That the payment actually occurred (verify via Stripe API for Pro proofs; Free proofs have `payment.provider = "none"`)
- That the timestamp is accurate (verify via RFC 3161 TSA)
- That the response content is correct (verify via the service)

## 6. Digital signature

The chain hash MAY be signed by the proof issuer using Ed25519. This proves **origin** (the proof was issued by ArkForge), not just **integrity** (the proof was not tampered with).

### Algorithm

- **Key type:** Ed25519
- **Signed message:** the chain hash hex string, UTF-8 encoded (e.g. `"2f8bf97e19c9..."`)
- **Encoding:** `ed25519:<base64url_without_padding>`
  - Public key: 32 bytes → 43 chars base64url
  - Signature: 64 bytes → 86 chars base64url

### Proof fields

| Field | Description |
|-------|-------------|
| `arkforge_signature` | Ed25519 signature of the chain hash. Format: `ed25519:<base64url>` |
| `arkforge_pubkey` | Public key used for signing. Format: `ed25519:<base64url>` |

### Verification

```python
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
import base64

# Decode base64url (add padding)
def b64url_decode(s):
    s += "=" * (4 - len(s) % 4) if len(s) % 4 else ""
    return base64.urlsafe_b64decode(s)

pubkey_b64 = proof["arkforge_pubkey"].removeprefix("ed25519:")
sig_b64 = proof["arkforge_signature"].removeprefix("ed25519:")
chain_hash = proof["hashes"]["chain"].removeprefix("sha256:")

pub = Ed25519PublicKey.from_public_bytes(b64url_decode(pubkey_b64))
pub.verify(b64url_decode(sig_b64), chain_hash.encode("utf-8"))
# Raises InvalidSignature if verification fails
```

### What the signature covers vs. does not cover

**Covered** (via the chain hash): `request_hash`, `response_hash`, `payment_intent_id`, `timestamp`, `buyer_fingerprint`, `seller`, `upstream_timestamp` (if present).

**Not covered** (mutable metadata): `views_count`, `identity_consistent`, `archive_org`, `timestamp_authority` status. These fields are informational and may change after proof creation.

### Key distribution

The issuer's public key is embedded in each proof (`arkforge_pubkey`) and served at `GET /v1/pubkey`. Verifiers SHOULD pin the public key from a trusted source rather than relying solely on the `arkforge_pubkey` field within the proof itself.

## 7. Independent witnesses

A proof MAY be corroborated by independent witnesses:

| Witness | What it proves | Verification | Availability |
|---------|---------------|--------------|-------------|
| **Ed25519 Signature** | Proof was issued by ArkForge | Verify `arkforge_signature` with `arkforge_pubkey` | All plans |
| **RFC 3161 Timestamp** | Proof existed at claimed time | Verify `.tsr` file via `openssl ts -verify` | All plans |
| **Archive.org** | Proof page was publicly visible | Visit `archive_org.snapshot_url` | All plans |
| **Stripe** | Payment occurred | Check `payment.transaction_id` on Stripe dashboard or API | Pro plan only |

Free tier proofs have 3 witnesses (Ed25519, RFC 3161, Archive.org). Pro proofs add Stripe as a 4th witness.

No witness is required for chain hash verification. Each adds an independent layer of trust.

## 8. Test vectors

See [`test-vectors.json`](test-vectors.json) for machine-readable test cases.

Implementers MUST pass all test vectors to claim conformance.

## 9. Versioning

This spec follows [Semantic Versioning](https://semver.org/).

- **Patch** (1.0.x): clarifications, typo fixes, new test vectors
- **Minor** (1.x.0): new optional fields, new witnesses
- **Major** (x.0.0): changes to chain hash algorithm or required fields

## License

[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — free to use, share, and adapt with attribution.
