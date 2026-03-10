#!/usr/bin/env python3
"""Verify internal consistency of the proof spec.

Checks:
1. spec_version in test-vectors.json matches SPEC.md title and examples
2. All test vector hashes are correct (recomputed from inputs)
3. test-vectors.json vector count matches README.md claim
"""

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SPEC = ROOT / "SPEC.md"
VECTORS = ROOT / "test-vectors.json"
README = ROOT / "README.md"


def canonical_json(data: dict) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def check_spec_version():
    """spec_version in test-vectors.json must appear in SPEC.md examples."""
    vectors = json.loads(VECTORS.read_text())
    spec_ver = vectors["spec_version"]  # e.g. "1.1.0"
    major_minor = ".".join(spec_ver.split(".")[:2])  # e.g. "1.1"

    spec_text = SPEC.read_text()

    # The JSON example in SPEC.md must show the current major.minor
    pattern = rf'"spec_version":\s*"{re.escape(major_minor)}"'
    if not re.search(pattern, spec_text):
        print(f"FAIL: SPEC.md JSON example does not contain spec_version \"{major_minor}\"")
        return False

    # The title must contain the full semver
    if spec_ver not in spec_text.split("\n")[0]:
        print(f"FAIL: SPEC.md title does not contain version {spec_ver}")
        return False

    print(f"OK: spec_version {spec_ver} consistent in SPEC.md")
    return True


def check_test_vectors():
    """Recompute all test vector hashes and compare to expected values."""
    vectors = json.loads(VECTORS.read_text())
    ok = True

    for v in vectors["vectors"]:
        name = v["name"]
        inp = v["input"]
        exp = v["expected"]

        # Canonical JSON
        canon_req = canonical_json(inp["request"])
        canon_resp = canonical_json(inp["response"])

        if canon_req != exp["canonical_request"]:
            print(f"FAIL [{name}]: canonical_request mismatch")
            print(f"  got:      {canon_req}")
            print(f"  expected: {exp['canonical_request']}")
            ok = False

        if canon_resp != exp["canonical_response"]:
            print(f"FAIL [{name}]: canonical_response mismatch")
            print(f"  got:      {canon_resp}")
            print(f"  expected: {exp['canonical_response']}")
            ok = False

        # Hashes
        req_hash = sha256(canon_req)
        resp_hash = sha256(canon_resp)
        buyer_fp = sha256(inp["api_key"])

        for field, computed, expected in [
            ("request_hash", req_hash, exp["request_hash"]),
            ("response_hash", resp_hash, exp["response_hash"]),
            ("buyer_fingerprint", buyer_fp, exp["buyer_fingerprint"]),
        ]:
            if computed != expected:
                print(f"FAIL [{name}]: {field} mismatch")
                print(f"  got:      {computed}")
                print(f"  expected: {expected}")
                ok = False

        # Chain hash — algorithm depends on vector's spec_version
        algo = v.get("algorithm", "concatenation")
        if algo == "canonical_json":
            chain_data = {
                "buyer_fingerprint": buyer_fp,
                "request_hash": req_hash,
                "response_hash": resp_hash,
                "seller": inp["seller"],
                "timestamp": inp["timestamp"],
                "transaction_id": inp["payment_intent_id"],
            }
            if inp.get("upstream_timestamp"):
                chain_data["upstream_timestamp"] = inp["upstream_timestamp"]
            if inp.get("receipt_content_hash"):
                chain_data["receipt_content_hash"] = inp["receipt_content_hash"]
            # Verify canonical_chain_data if present
            if "canonical_chain_data" in exp:
                actual_canonical = canonical_json(chain_data)
                if actual_canonical != exp["canonical_chain_data"]:
                    print(f"FAIL [{name}]: canonical_chain_data mismatch")
                    print(f"  got:      {actual_canonical}")
                    print(f"  expected: {exp['canonical_chain_data']}")
                    ok = False
            chain_hash = sha256(canonical_json(chain_data))
        else:
            chain_input = (
                req_hash
                + resp_hash
                + inp["payment_intent_id"]
                + inp["timestamp"]
                + buyer_fp
                + inp["seller"]
            )
            if inp.get("upstream_timestamp"):
                chain_input += inp["upstream_timestamp"]
            if inp.get("receipt_content_hash"):
                chain_input += inp["receipt_content_hash"]
            chain_hash = sha256(chain_input)

        if chain_hash != exp["chain_hash"]:
            print(f"FAIL [{name}]: chain_hash mismatch")
            print(f"  got:      {chain_hash}")
            print(f"  expected: {exp['chain_hash']}")
            ok = False
        else:
            print(f"OK [{name}]: all hashes verified")

    return ok


def check_vector_count():
    """README vector count must match actual count."""
    vectors = json.loads(VECTORS.read_text())
    actual = len(vectors["vectors"])

    readme_text = README.read_text()
    match = re.search(r"contains (\d+) test cases", readme_text)
    if not match:
        print("WARN: README.md does not mention test case count — skipping")
        return True

    claimed = int(match.group(1))
    if claimed != actual:
        print(f"FAIL: README.md claims {claimed} test cases, but test-vectors.json has {actual}")
        return False

    print(f"OK: vector count {actual} matches README.md")
    return True


def main():
    results = [
        check_spec_version(),
        check_test_vectors(),
        check_vector_count(),
    ]
    if not all(results):
        print("\nFAILED — inconsistencies found")
        sys.exit(1)
    print("\nALL CHECKS PASSED")


if __name__ == "__main__":
    main()
