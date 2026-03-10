# ArkForge Proof Specification v2.1.0

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

A conformant proof is a JSON object. The following fields are **required**:

### Required fields

| Field | Type | Description |
|-------|------|-------------|
| `proof_id` | string | Unique proof identifier (e.g. `prf_20260225_170950_fdec72`) |
| `timestamp` | string | ISO 8601 UTC timestamp of proof creation (e.g. `2026-02-25T17:09:47Z`) |
| `hashes.request` | string | SHA-256 hash of canonical JSON request. Format: `sha256:<hex>` |
| `hashes.response` | string | SHA-256 hash of canonical JSON response. Format: `sha256:<hex>` |
| `hashes.chain` | string | Chain hash binding all components. Format: `sha256:<hex>` |
| `parties.buyer_fingerprint` | string | SHA-256 hash of the buyer's API key (hex) |
| `parties.seller` | string | Target service domain (e.g. `arkforge.fr`) |
| `payment.provider` | string | Payment provider identifier (see Payment variants) |
| `payment.transaction_id` | string | Payment reference used in chain hash (see Payment variants) |
| `payment.amount` | number | Payment amount |
| `payment.currency` | string | Currency code (e.g. `"eur"`) |
| `payment.status` | string | Payment status (e.g. `"succeeded"`, `"free_tier"`) |

### Minimal example (required fields only)

```json
{
  "proof_id": "prf_20260225_170950_fdec72",
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
    "provider": "prepaid_credit",
    "transaction_id": "crd_20260225_170950_a1b2c3",
    "amount": 0.10,
    "currency": "eur",
    "status": "succeeded"
  }
}
```

### Full example (with optional fields)

```json
{
  "proof_id": "prf_20260225_170950_fdec72",
  "spec_version": "2.1",
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
  "verification_url": "https://arkforge.tech/trust/v1/proof/prf_20260225_170950_fdec72"
}
```

**Note:** `spec_version` indicates the chain hash algorithm used:
- `"1.2"` (current): canonical JSON chain hash — see section 2
- `"2.1"` (current + receipt): canonical JSON chain hash with `receipt_content_hash`
- `"1.1"`, `"2.0"` (legacy): string concatenation — see section 2 backward compatibility

### Payment variants

The `payment` object reflects how the proof was generated:

| Plan | `provider` | `transaction_id` | `amount` | `status` |
|------|-----------|-----------------|----------|----------|
| Pro (Stripe direct) | `"stripe"` | Stripe Payment Intent ID (`pi_...`) | `> 0` | `"succeeded"` |
| Pro (prepaid credits) | `"prepaid_credit"` | Credit transaction ID (`crd_...`) | `> 0` | `"succeeded"` |
| Free | `"none"` | `"free_tier"` | `0.0` | `"free_tier"` |

All variants produce a valid chain hash. The `payment.transaction_id` value is used as-is in the chain hash computation (see section 2).

### Optional fields

| Field | Type | Description |
|-------|------|-------------|
| `spec_version` | string | Proof format version (`"1.1"` or `"2.0"`). Informational for auditors |
| `upstream_timestamp` | string | Upstream service's HTTP `Date` header (RFC 7231 format). **Included in chain hash** when present |
| `provider_payment` | object | External receipt verification (see section 2.1). `receipt_content_hash` **included in chain hash** when present |
| `arkforge_signature` | string | Ed25519 signature of the chain hash. Format: `ed25519:<base64url_without_padding>` |
| `arkforge_pubkey` | string | Ed25519 public key used for signing. Format: `ed25519:<base64url_without_padding>` |
| `verification_url` | string | URL to verify and view the proof (e.g. `https://arkforge.tech/trust/v1/proof/<proof_id>`) |
| `parties.agent_identity` | string | Agent's self-declared name |
| `parties.agent_version` | string | Agent's version string |
| `identity_consistent` | bool/null | Whether identity matches previous calls with same key |
| `timestamp_authority` | object | TSA status, provider, download URL, and `tsr_base64` (base64-encoded .tsr file) |
| `verification_algorithm` | string | URL to algorithm documentation |
| `transaction_success` | bool | Whether the upstream service returned a success response (HTTP status < 400) |
| `upstream_status_code` | int | HTTP status code returned by the upstream service |
| `disputed` | bool | Whether this proof has been disputed. Set by the dispute system |
| `dispute_id` | string | Reference to the dispute record (e.g. `disp_a1b2c3d4`). Set when disputed |
| `transparency_log` | object | Sigstore Rekor entry. **Post-chain-hash metadata, does not affect chain hash formula.** See section 7.1 |

## 2. Chain hash algorithm

The chain hash binds every element of a transaction into a single verifiable seal.

### Algorithm (spec_version "1.2" and "2.1" — current)

The chain hash is computed by serializing all components into a canonical JSON object and hashing the result.

```
chain_data = {
  "buyer_fingerprint": <hex>,
  "request_hash":      <hex>,
  "response_hash":     <hex>,
  "seller":            <string>,
  "timestamp":         <ISO 8601 string>,
  "transaction_id":    <string>,
  // optional fields — only include when present and non-null:
  "upstream_timestamp":    <string>,   // spec_version "1.2" with upstream
  "receipt_content_hash":  <hex>,      // spec_version "2.1" — strip "sha256:" prefix
}

chain_hash = SHA256(canonical_json(chain_data))
```

Keys are sorted alphabetically (canonical JSON). Optional fields are included in the dict only when present and non-null.

#### Reference implementation (Python)

```python
import json, hashlib

def canonical_json(data: dict) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

chain_data = {
    "buyer_fingerprint": buyer_fingerprint,
    "request_hash":      request_hash,
    "response_hash":     response_hash,
    "seller":            seller,
    "timestamp":         timestamp,
    "transaction_id":    transaction_id,
}
if upstream_timestamp:
    chain_data["upstream_timestamp"] = upstream_timestamp
if receipt_content_hash:
    chain_data["receipt_content_hash"] = receipt_content_hash.removeprefix("sha256:")

chain_hash = sha256_hex(canonical_json(chain_data))
```

### Definitions

| Component | Source in proof JSON | Derivation |
|-----------|---------------------|-----------|
| `request_hash` | `hashes.request` | `SHA256(canonical_json(request_data))`, without the `sha256:` prefix |
| `response_hash` | `hashes.response` | `SHA256(canonical_json(response_data))`, without the `sha256:` prefix |
| `transaction_id` | `payment.transaction_id` | Used as-is: Stripe ID (`pi_...`), credit ID (`crd_...`), or `free_tier` |
| `timestamp` | `timestamp` | ISO 8601 UTC string (e.g. `2026-02-25T17:09:47Z`) |
| `buyer_fingerprint` | `parties.buyer_fingerprint` | `SHA256(api_key)` — hash of the raw API key string |
| `seller` | `parties.seller` | Target domain (e.g. `arkforge.fr`) |
| `upstream_timestamp` | `upstream_timestamp` | Upstream service's HTTP `Date` header. **Included in chain_data only when present and non-null** |
| `receipt_content_hash` | `provider_payment.receipt_content_hash` | SHA-256 hex of raw receipt bytes. **Included in chain_data only when present**. Strip the `sha256:` prefix |

### Backward compatibility (spec_version "1.1" and "2.0" — legacy)

Proofs with `spec_version` `"1.1"`, `"2.0"`, or absent use the **legacy string concatenation formula**:

```
input = request_hash + response_hash + transaction_id + timestamp + buyer_fingerprint + seller
       [+ upstream_timestamp if present]
       [+ receipt_content_hash (stripped of "sha256:" prefix) if present]

chain_hash = SHA256(input.encode("utf-8")).hexdigest()
```

Use `spec_version` to select the algorithm:
- `"1.2"`, `"2.1"`: canonical JSON (current)
- `"1.1"`, `"2.0"`, absent: string concatenation (legacy)

**Why canonical JSON?** Variable-length string concatenation without separators creates preimage ambiguity: two different inputs can produce the same concatenated string (e.g. `"ab"+"cd"` = `"a"+"bcd"`). Canonical JSON eliminates this by encoding field boundaries explicitly.

## 2.1. Payment evidence (v2.0)

A proof MAY include external payment evidence — an independently fetched receipt from a payment service provider (PSP). When present, the receipt content hash is included in the chain hash.

### Structure

```json
{
  "provider_payment": {
    "type": "stripe",
    "receipt_url": "https://pay.stripe.com/receipts/payment/...",
    "receipt_fetch_status": "fetched",
    "receipt_content_hash": "sha256:<hex>",
    "parsing_status": "success",
    "parsed_fields": {"amount": 25.0, "currency": "usd", "status": "paid", "date": "..."},
    "payment_verification": "fetched"
  }
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | PSP identifier (e.g. `"stripe"`) |
| `receipt_url` | string | Original receipt URL fetched by ArkForge |
| `receipt_fetch_status` | string | `"fetched"` (success) or `"failed"` (timeout, HTTP error, invalid domain) |
| `receipt_content_hash` | string | `sha256:<hex>` — SHA-256 of the raw receipt bytes. **Included in chain hash** |
| `parsing_status` | string | `"success"`, `"failed"`, or `"not_attempted"` |
| `parsed_fields` | object/null | Extracted fields (amount, currency, status, date). Null if parsing failed |
| `payment_verification` | string | `"fetched"` (independently verified) or `"failed"` |
| `receipt_fetch_error` | string | Error details (only present on failure) |

### Chain hash impact

When `provider_payment.receipt_content_hash` is present, its value (with the `sha256:` prefix stripped) is appended to the chain hash input. This binds the external receipt to the proof — modifying the receipt content after the fact invalidates the chain hash.

### What payment evidence proves vs. does not prove

**Proves:** ArkForge fetched a receipt from the PSP at the time of proof creation, and the content matched the stored hash.

**Does NOT prove:** that the receipt is for the correct transaction, the correct amount, or the correct provider. The provider must verify the receipt independently — the proof records what ArkForge observed.

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
    return json.dumps(data, sort_keys=True, separators=(",", ":"))
```

**Note:** input data MUST contain only standard JSON types (strings, numbers, booleans, arrays, objects, null). Non-serializable types (e.g. datetime objects) must be converted to strings before canonicalization.

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

Given a proof JSON, any party can verify the integrity of chain-hash-bound fields.

First, determine the algorithm from `spec_version`:

### Current algorithm (spec_version "1.2" / "2.1")

```python
import json, hashlib

def canonical_json(d):
    return json.dumps(d, sort_keys=True, separators=(",", ":"))

def sha256_hex(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

proof = json.loads(open("proof.json").read())

request_hash  = proof["hashes"]["request"].removeprefix("sha256:")
response_hash = proof["hashes"]["response"].removeprefix("sha256:")

chain_data = {
    "buyer_fingerprint": proof["parties"]["buyer_fingerprint"],
    "request_hash":      request_hash,
    "response_hash":     response_hash,
    "seller":            proof["parties"]["seller"],
    "timestamp":         proof["timestamp"],
    "transaction_id":    proof["payment"]["transaction_id"],
}
if proof.get("upstream_timestamp"):
    chain_data["upstream_timestamp"] = proof["upstream_timestamp"]
rcv = (proof.get("provider_payment") or {}).get("receipt_content_hash")
if rcv:
    chain_data["receipt_content_hash"] = rcv.removeprefix("sha256:")

computed = sha256_hex(canonical_json(chain_data))
expected = proof["hashes"]["chain"].removeprefix("sha256:")
print("VERIFIED" if computed == expected else "TAMPERED")
```

### Legacy algorithm (spec_version "1.1" / "2.0" / absent)

```bash
REQUEST_HASH=$(echo "$PROOF" | jq -r '.hashes.request' | sed 's/sha256://')
RESPONSE_HASH=$(echo "$PROOF" | jq -r '.hashes.response' | sed 's/sha256://')
PAYMENT_ID=$(echo "$PROOF" | jq -r '.payment.transaction_id')
TIMESTAMP=$(echo "$PROOF" | jq -r '.timestamp')
BUYER=$(echo "$PROOF" | jq -r '.parties.buyer_fingerprint')
SELLER=$(echo "$PROOF" | jq -r '.parties.seller')
UPSTREAM=$(echo "$PROOF" | jq -r '.upstream_timestamp // empty')
RECEIPT_HASH=$(echo "$PROOF" | jq -r '.provider_payment.receipt_content_hash // empty' | sed 's/sha256://')

# Linux:
COMPUTED=$(printf '%s' "${REQUEST_HASH}${RESPONSE_HASH}${PAYMENT_ID}${TIMESTAMP}${BUYER}${SELLER}${UPSTREAM}${RECEIPT_HASH}" | sha256sum | cut -d' ' -f1)
# macOS:
# COMPUTED=$(printf '%s' "..." | shasum -a 256 | cut -d' ' -f1)

EXPECTED=$(echo "$PROOF" | jq -r '.hashes.chain' | sed 's/sha256://')
[ "$COMPUTED" = "$EXPECTED" ] && echo "VERIFIED" || echo "TAMPERED"
```

If the chain hash matches, no chain-hash-bound field was altered after creation.

### What verification proves

- The request/response pair is authentic (hashes match)
- The payment transaction ID is bound to this specific execution
- The timestamp is bound to this specific execution
- The external receipt content (if present) is bound to this specific proof
- No chain-hash-bound field was modified after proof creation

### What verification does NOT prove

- That the payment actually occurred (verify via Stripe API for Pro proofs; Free proofs have `payment.provider = "none"`)
- That the timestamp is accurate (verify via RFC 3161 TSA)
- That the response content is correct (verify via the service)
- That mutable metadata fields (`identity_consistent`, `timestamp_authority`, `transaction_success`, `upstream_status_code`, `disputed`, `dispute_id`) are unchanged — these are informational and may be updated after proof creation without affecting the chain hash

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

**Covered** (via the chain hash): `hashes.request`, `hashes.response`, `payment.transaction_id`, `timestamp`, `parties.buyer_fingerprint`, `parties.seller`, `upstream_timestamp` (if present), `provider_payment.receipt_content_hash` (if present).

**Not covered** (mutable metadata): `identity_consistent`, `timestamp_authority` status, `transaction_success`, `upstream_status_code`, `disputed`, `dispute_id`. These fields are informational and may change after proof creation.

### Key distribution

The issuer's public key is embedded in each proof (`arkforge_pubkey`) and served at `GET /v1/pubkey`. Verifiers SHOULD pin the public key from a trusted source rather than relying solely on the `arkforge_pubkey` field within the proof itself.

## 7. Independent witnesses

A proof MAY be corroborated by independent witnesses:

| Witness | What it proves | Verification | Availability |
|---------|---------------|--------------|-------------|
| **Ed25519 Signature** | Proof was issued by ArkForge | Verify `arkforge_signature` with `arkforge_pubkey` | All plans |
| **RFC 3161 Timestamp** | Proof existed at claimed time | Verify `.tsr` file via `openssl ts -verify` | All plans |
| **Sigstore Rekor** | Chain hash registered in append-only public log | See section 7.1 | All plans |
| **Stripe** | Payment occurred | Check `payment.transaction_id` on Stripe dashboard or API | Pro plan only |
| **External Receipt** | Receipt content at time of proof | Fetch `provider_payment.receipt_url`, hash content, compare to `receipt_content_hash` | When `provider_payment` is present |

Free tier proofs have 3 witnesses (Ed25519, RFC 3161, Sigstore Rekor). Pro proofs add Stripe as a 4th witness. Proofs with external payment evidence add the receipt as an additional witness.

No witness is required for chain hash verification. Each adds an independent layer of trust.

### 7.1 Transparency log (Sigstore Rekor)

Rekor is an append-only public transparency log operated by the Linux Foundation under the Sigstore project. When present, `transparency_log` contains:

```json
{
  "provider": "sigstore-rekor",
  "status": "verified",
  "uuid": "24296fb...",
  "log_index": 12345678,
  "integrated_time": 1709500000,
  "log_url": "https://rekor.sigstore.dev/api/v1/log/entries/24296fb...",
  "verify_url": "https://search.sigstore.dev/?logIndex=12345678"
}
```

If Rekor is unavailable at proof creation time, `status` is `"failed"` and the proof remains valid (all other witnesses are unaffected).

**Important**: `transparency_log` is post-chain-hash metadata. It is populated after the chain hash is computed and **does not affect the chain hash formula**. Verifiers MUST NOT include `transparency_log` in chain hash recomputation.

**Independent verification**: Visit `verify_url` or fetch `log_url` directly to confirm the chain hash was registered in the public log without relying on ArkForge.

## 8. Test vectors

See [`test-vectors.json`](test-vectors.json) for machine-readable test cases.

Implementers MUST pass all test vectors to claim conformance.

## 9. Versioning

This spec follows [Semantic Versioning](https://semver.org/).

- **Patch** (1.0.x): clarifications, typo fixes, new test vectors
- **Minor** (1.x.0): new optional fields, new witnesses, new chain hash algorithm (backward-compatible — old `spec_version` values remain verifiable)
- **Major** (x.0.0): non-backward-compatible changes to chain hash algorithm, removal of required fields, or breaking changes to verification procedure

## License

[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — free to use, share, and adapt with attribution.
