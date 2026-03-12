# Contributing to proof-spec

## What this repo is

This repository defines the ArkForge Proof Format — an open standard for verifiable HTTP transaction proofs. Contributions are welcome.

## How to contribute

Open an issue first for any non-trivial change to the spec. Breaking changes (field renames, removals) require discussion.

For typos and clarifications, a PR directly is fine.

## Branching

- `main` is protected — no direct push
- Branch from `main`: `feat/your-change` or `fix/clarification`
- Open a PR against `main`

## What we accept

- Clarifications to existing field definitions
- New optional fields (with use case justification)
- Additional test vectors in `test-vectors.json`
- New implementations in the implementations table

## What requires an issue first

- Breaking changes to existing fields
- New required fields
- Changes to the proof verification algorithm

## Adding your implementation

Edit the implementations table in `README.md`:

```markdown
| Your library | language | link |
```

Open a PR — no issue required.

## Questions

Open an issue or reach out at [arkforge.tech](https://arkforge.tech).
