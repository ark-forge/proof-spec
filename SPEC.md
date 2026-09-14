# ArkForge Proof Specification v3.1.0

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
| `commitments` | object | One commitment per committed field, `field -> sha256:<hex>` (spec_version `"3.0"`) |
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
  "commitments": {
    "buyer_fingerprint": "sha256:<hex>",
    "request_hash": "sha256:<hex>",
    "response_hash": "sha256:<hex>",
    "seller": "sha256:<hex>",
    "timestamp": "sha256:<hex>",
    "transaction_id": "sha256:<hex>"
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
  "spec_version": "3.1",
  "timestamp": "2026-02-25T17:09:47Z",
  "hashes": {
    "request": "sha256:<hex>",
    "response": "sha256:<hex>",
    "chain": "sha256:<hex>"
  },
  "commitments": {
    "buyer_fingerprint": "sha256:<hex>",
    "request_hash": "sha256:<hex>",
    "response_hash": "sha256:<hex>",
    "seller": "sha256:<hex>",
    "timestamp": "sha256:<hex>",
    "transaction_id": "sha256:<hex>"
  },
  "batch_anchor": {
    "status": "anchored",
    "batch_id": "batch_20260913_132956_516",
    "leaf_index": 0,
    "tree_size": 4,
    "audit_path": ["<hex>", "<hex>"],
    "root": "sha256:<hex>"
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
  "verification_url": "https://trust.arkforge.tech/v1/proof/prf_20260225_170950_fdec72"
}
```

**Note:** `spec_version` indicates the chain hash algorithm used:
- `"3.0"` (current): Merkle root of per-field commitments — see section 2
- `"1.2"`, `"2.1"`: canonical JSON over the values themselves — see section 2 backward compatibility
- `"1.1"`, `"2.0"` (legacy): string concatenation — same section

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
| `spec_version` | string | Proof format version (`"3.0"`, `"2.1"`, `"1.2"`, `"1.1"`, `"2.0"`). Selects the chain hash algorithm — **not** informational |
| `batch_anchor` | object | Inclusion proof from this chain hash up to the anchored batch root — see section 2.2 |
| `upstream_timestamp` | string | Upstream service's HTTP `Date` header (RFC 7231 format). **Included in chain hash** when present |
| `provider_payment` | object | External receipt verification (see section 2.1). `receipt_content_hash` **included in chain hash** when present |
| `arkforge_signature` | string | Ed25519 signature of the chain hash. Format: `ed25519:<base64url_without_padding>` |
| `arkforge_pubkey` | string | Ed25519 public key used for signing. Format: `ed25519:<base64url_without_padding>` |
| `verification_url` | string | URL to verify and view the proof (e.g. `https://trust.arkforge.tech/v1/proof/<proof_id>`) |
| `parties.agent_identity` | string | Agent identity. If the API key has a cryptographically verified DID bound via Ed25519 challenge-response, this field contains the verified DID and takes precedence over any caller-declared value. Otherwise, contains the caller's self-declared name. |
| `parties.agent_identity_verified` | bool | `true` if `agent_identity` is a cryptographically verified DID bound to the API key. Absent if the identity is self-declared. |
| `parties.did_resolution_status` | string | DID resolution status at proof creation time. `"bound"` if `agent_identity` is a cryptographically verified DID bound via Ed25519 challenge-response at registration time. `"unverified"` if `agent_identity` is caller-declared without cryptographic verification. Absent if no `agent_identity` is provided. |
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

### Algorithm (spec_version "3.1" — current)

Each chain field is committed to separately, and the chain hash is the RFC 6962 Merkle
root of those commitments:

```
commitment(field) = SHA256(field_name || 0x00 || nonce || canonical_json(value))

chain_hash = MerkleRootRFC6962([ leaf(commitment(f)) for f in sorted(fields) ])
  leaf(x)       = SHA256(0x00 || x)
  node(l, r)    = SHA256(0x01 || l || r)
```

- `field_name` is the UTF-8 field name, followed by a single `0x00` byte. It is in the
  preimage so that a commitment cannot be moved from one field to another during a
  partial disclosure.
- `nonce` is **32 fresh random bytes, drawn per field and per proof**. Per field, so
  that disclosing one field does not let anyone brute-force a low-entropy neighbour
  (an amount, a domain). Per proof, so that two proofs over the same value do not
  produce equal commitments that link them.
- `value` is encoded with `canonical_json`, never `str()`: `100` and `"100"` must not
  open the same commitment.
- Leaves are ordered by field name, which a verifier reconstructs from the published
  commitments alone. There is no separate ordering to publish or to trust.

**Why commitments?** Up to spec 2.1 the chain hash was computed over the field values
themselves. A public proof redacts `transaction_id` and `buyer_fingerprint`, so a third
party could not recompute the anchored hash at all — the published verification
procedure either skipped the check or reported TAMPERED against an honest issuer. With
per-field commitments the proof publishes every commitment and no value: the anchored
hash is recomputable from public data, and nothing that was private becomes public.

### Fields committed

```
request_hash, response_hash, transaction_id, timestamp, buyer_fingerprint, seller
agent_identity, agent_identity_verified, did_resolution_status,
identity_consistent                                              (spec 3.1, ALWAYS)
[+ upstream_timestamp]      when present and non-null
[+ receipt_content_hash]    when present, stripped of its "sha256:" prefix
```

**Spec 3.1 added the identity block.** `identity_consistent` belongs to it: it is a
judgment ON the identity, so committing its three neighbours and leaving it out would
rebuild the same hole one field to the left. Up to 3.0 those four fields were served in
public proof responses (section 9) but committed nowhere: outside the Merkle root,
therefore outside `hashes.chain`, the Ed25519 signature, the RFC 3161 token and the
Rekor entry. An attestor could restate an agent's identity after anchoring and every
external witness still verified. Any ranking or audit that reads
`agent_identity_verified` was, up to 3.0, reading the attestor's unbacked word.

The block is committed **unconditionally**, unlike `upstream_timestamp` and
`receipt_content_hash`. An absent identity is committed as `null`. Committing it only
when present would let an attestor omit the fields and leave a verifier with no
commitment to check against.

`agent_identity_verified` is `true` or `null`, never `false`: a single normalisation
at the source, so the value committed and the value served cannot disagree.
`agent_version` is NOT committed — it carries no verifiable claim.

#### Reference implementation (Python)

```python
import json, hashlib, secrets

def canonical_json(data) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))

def commit(field: str, nonce: bytes, value) -> bytes:
    return hashlib.sha256(field.encode("utf-8") + b"\x00" + nonce
                          + canonical_json(value).encode("utf-8")).digest()

def leaf(x: bytes) -> bytes:   return hashlib.sha256(b"\x00" + x).digest()
def node(l: bytes, r: bytes) -> bytes: return hashlib.sha256(b"\x01" + l + r).digest()

def merkle_root(leaves):
    # RFC 6962: the odd node is promoted, never duplicated. Duplicating it (the
    # Bitcoin shape, CVE-2012-2459) lets two different leaf sets share a root.
    if len(leaves) == 1:
        return leaves[0]
    k = 1
    while k * 2 < len(leaves):
        k *= 2
    return node(merkle_root(leaves[:k]), merkle_root(leaves[k:]))

nonces      = {f: secrets.token_bytes(32) for f in chain_data}
commitments = {f: commit(f, nonces[f], v).hex() for f, v in chain_data.items()}
chain_hash  = merkle_root([leaf(bytes.fromhex(commitments[f]))
                           for f in sorted(commitments)]).hex()
```

### Public opening of the identity block (spec 3.1)

A commitment hides its value: a third party recomputes the root from the published
digests and never learns a field. For the identity block that is not enough, because
the values must be **readable** by whoever reads the proof. So spec 3.1 publishes those
four nonces in the proof itself, under `disclosed`:

```json
"disclosed": {
  "agent_identity":          {"nonce": "<64 hex>", "value": "did:web:agent.example"},
  "agent_identity_verified": {"nonce": "<64 hex>", "value": true},
  "did_resolution_status":   {"nonce": "<64 hex>", "value": "bound"},
  "identity_consistent":     {"nonce": "<64 hex>", "value": true}
}
```

Any party checks each triplet against the commitment the anchors cover:

```python
assert commit(field, bytes.fromhex(item["nonce"]), item["value"]).hex() \
       == proof["commitments"][field]
```

Hiding is given up on these four fields and on **no other**: every remaining nonce
stays secret. A verifier MUST treat the flat `agent_identity*` fields of a public
response as informational and take the value from `disclosed`; an attestor MUST serve
the same value in both.

**What this establishes, and what it does not.** It makes the identity claim
non-repudiable: the attestor committed to it before anchoring and cannot restate it.
It does **not** let a third party verify the binding itself — no public artefact proves
the Ed25519 challenge-response happened. A verifier that needs more MUST resolve the
DID itself.

A `spec_version` below `"3.1"` carries no anchored identity. A verifier MUST NOT treat
its `agent_identity_verified` as evidence.

### Selective disclosure

The proof owner holds the nonces. To prove one field to a counterparty without revealing
any other, the owner hands over that field's `(nonce, value)` pair out of band. The
counterparty recomputes `commitment(field)` and compares it with the commitment published
in the proof — which is already covered by the anchored chain hash.

```python
recomputed = commit(field, bytes.fromhex(nonce), value).hex()
assert recomputed == proof["commitments"][field]
```

Nothing about the undisclosed fields follows: each carries its own independent 32-byte
nonce. There is no disclosure endpoint and no signed disclosure format — the anchored
commitment is what makes the pair self-sufficient.

### Definitions

| Component | Source in proof JSON | Derivation |
|-----------|---------------------|-----------|
| `request_hash` | `hashes.request` | `SHA256(canonical_json(request_data))`, without the `sha256:` prefix |
| `response_hash` | `hashes.response` | `SHA256(canonical_json(response_data))`, without the `sha256:` prefix |
| `transaction_id` | `payment.transaction_id` | Used as-is: Stripe ID (`pi_...`), credit ID (`crd_...`), or `free_tier` |
| `timestamp` | `timestamp` | ISO 8601 UTC string (e.g. `2026-02-25T17:09:47Z`) |
| `buyer_fingerprint` | `parties.buyer_fingerprint` | `SHA256(api_key)` — hash of the raw API key string |
| `seller` | `parties.seller` | Target domain (e.g. `arkforge.fr`) |
| `upstream_timestamp` | `upstream_timestamp` | Upstream service's HTTP `Date` header. **Committed only when present and non-null** |
| `receipt_content_hash` | `provider_payment.receipt_content_hash` | SHA-256 hex of raw receipt bytes. **Committed only when present**. Strip the `sha256:` prefix |
| `agent_identity` | `parties.agent_identity` | Declared or bound agent DID, or `null`. **Committed unconditionally (3.1)** |
| `agent_identity_verified` | `parties.agent_identity_verified` | `true` when the DID is bound via Ed25519 challenge-response, else `null` — never `false`. **Committed unconditionally (3.1)** |
| `did_resolution_status` | `parties.did_resolution_status` | `"bound"`, `"unverified"`, or `null`. **Committed unconditionally (3.1)** |
| `identity_consistent` | `identity_consistent` | `true`/`false`/`null` — whether the declared identity agrees with what the attestor already knows for this key. **Committed unconditionally (3.1)** |
| `commitments` | `commitments` | One hex commitment per committed field, published in full |
| `disclosed` | `disclosed` | The identity block's `(nonce, value)` pairs, published for everyone (3.1) |

### Backward compatibility

`spec_version` selects the algorithm. Earlier proofs keep theirs; nothing is recomputed
or re-anchored retroactively.

| `spec_version` | Chain hash |
|---|---|
| `"3.1"` | Merkle root of per-field commitments, identity block included and publicly opened (current) |
| `"3.0"` | Merkle root of per-field commitments; identity served but **not** committed |
| `"1.2"`, `"2.1"` | `SHA256(canonical_json(chain_data))` over the **values** |
| `"1.1"`, `"2.0"`, absent | `SHA256` of the values concatenated as raw UTF-8, no separator (legacy) |

**Values algorithm (spec_version "1.2" and "2.1")**

```
chain_data = {
  "buyer_fingerprint": <hex>, "request_hash": <hex>, "response_hash": <hex>,
  "seller": <string>, "timestamp": <ISO 8601>, "transaction_id": <string>,
  // optional, only when present and non-null:
  "upstream_timestamp": <string>, "receipt_content_hash": <hex>,
}
chain_hash = SHA256(canonical_json(chain_data))
```

**Legacy algorithm (spec_version "1.1", "2.0", absent)**

```
input = request_hash + response_hash + transaction_id + timestamp + buyer_fingerprint + seller
       [+ upstream_timestamp if present]
       [+ receipt_content_hash (stripped of "sha256:" prefix) if present]
chain_hash = SHA256(input.encode("utf-8")).hexdigest()
```

**Why not raw concatenation?** Variable-length string concatenation without separators
creates preimage ambiguity: two different inputs can produce the same concatenated
string (e.g. `"ab"+"cd"` = `"a"+"bcd"`). Canonical JSON eliminated that in spec 1.2;
per-field commitments keep it and add third-party verifiability on top.

## 2.2. Batch anchoring

External anchors — an RFC 3161 timestamp and a Sigstore Rekor entry — MAY cover a
**batch** of proofs rather than a single one. Chain hashes accumulate, and the anchored
artefact is the RFC 6962 Merkle root over them, same primitive as the chain hash one
level down:

```
batch_root = MerkleRootRFC6962([ leaf(chain_hash_bytes) for each proof in the batch ])
```

Each proof then carries its own inclusion proof down from that root:

```json
"batch_anchor": {
  "status": "anchored",
  "batch_id": "batch_20260913_132956_516",
  "leaf_index": 0,
  "tree_size": 4,
  "audit_path": ["<hex>", "<hex>"],
  "root": "sha256:<hex>"
}
```

A verifier walks the path from its leaf to the claimed root (RFC 6962 §2.1.1), then
checks the external anchors against **that root** rather than against the chain hash.

Three checks are not optional:

- the walk must reach the claimed root;
- `leaf_index` must lie in `[0, tree_size)`;
- `len(audit_path)` must equal the length a tree of `tree_size` requires for
  `leaf_index` — that length is deterministic. Without it, an overstated `tree_size` is
  accepted: the walk consumes the real siblings, reaches the real root and stops early,
  with every other check satisfied.

**Pending state.** Between issuance and batch close a proof has no external anchor.
`batch_anchor.status` is then `"pending"`, and a verifier MUST report that as waiting,
never as tampering. A proof that is merely waiting is not a forged one.

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

### Current algorithm (spec_version "3.0")

No field value is needed: the commitments are published and the chain hash is their
Merkle root.

```python
import json, hashlib

proof = json.loads(open("proof.json").read())
c = proof["commitments"]

def leaf(x):    return hashlib.sha256(b"\x00" + x).digest()
def node(l, r): return hashlib.sha256(b"\x01" + l + r).digest()

def merkle_root(leaves):
    if len(leaves) == 1:
        return leaves[0]
    k = 1
    while k * 2 < len(leaves):
        k *= 2
    return node(merkle_root(leaves[:k]), merkle_root(leaves[k:]))

leaves   = [leaf(bytes.fromhex(c[f].removeprefix("sha256:"))) for f in sorted(c)]
computed = merkle_root(leaves).hex()
expected = proof["hashes"]["chain"].removeprefix("sha256:")
print("VERIFIED" if computed == expected else "TAMPERED")
```

Recomputing the chain hash proves self-consistency only — whoever fabricates a proof
produces coherent hashes. The evidence is the RFC 3161 timestamp and the Sigstore Rekor
entry on the anchored hash (the batch root when `batch_anchor.status` is `"anchored"`,
the chain hash itself otherwise).

### Values algorithm (spec_version "1.2" / "2.1")

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

The issuer's public key is embedded in each proof (`arkforge_pubkey`) and served at two canonical endpoints:

- `GET /v1/pubkey` — JSON `{"pubkey": "ed25519:<base64url>", "algorithm": "Ed25519"}`
- `GET /.well-known/did.json` — W3C DID Document (`did:web:trust.arkforge.tech`) with `Ed25519VerificationKey2020` and `publicKeyJwk` (kty=OKP, crv=Ed25519, x=`<base64url>`)

Verifiers SHOULD pin the public key from a trusted source rather than relying solely on the `arkforge_pubkey` field within the proof itself. The DID Document can be resolved by any conformant `did:web` resolver.

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

## 9. API Response Filtering

Implementations MAY filter sensitive fields from public API responses while keeping the internal proof structure intact.

When a proof is returned via an **unauthenticated** endpoint:

- `parties.buyer_fingerprint` SHOULD be omitted (privacy)
- `parties.agent_identity`, `parties.agent_identity_verified`, `parties.did_resolution_status`, and `parties.seller` SHOULD be included (third-party auditability)
- For `spec_version` `"3.1"`, `disclosed` MUST be included: it carries the identity block's nonces, without which the anchored identity cannot be opened and the flat fields above are unbacked
- `certification_fee` amounts and receipt URLs SHOULD be omitted
- `buyer_reputation_score` and `buyer_profile_url` SHOULD be omitted
- `provider_payment`: only `type`, `receipt_content_hash`, and `verification_status` SHOULD be retained; `receipt_url` and `parsed_fields` SHOULD be omitted

When a proof is returned via an **authenticated owner-only** endpoint:

- All fields MAY be included
- Ownership SHOULD be verified by comparing `sha256(api_key)` against `parties.buyer_fingerprint`

**Note:** these filtering rules apply to API responses only. The stored proof structure is not affected; `verify_proof_integrity()` always operates on the full internal proof.

## 10. Versioning

This spec follows [Semantic Versioning](https://semver.org/).

- **Patch** (1.0.x): clarifications, typo fixes, new test vectors
- **Minor** (1.x.0): new optional fields, new witnesses, new chain hash algorithm (backward-compatible — old `spec_version` values remain verifiable)
- **Major** (x.0.0): non-backward-compatible changes to chain hash algorithm, removal of required fields, or breaking changes to verification procedure

## License

[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — free to use, share, and adapt with attribution.
