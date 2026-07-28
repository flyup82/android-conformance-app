# Android Conformance App Instructions

## Purpose

Build the public deterministic conformance target for Android QAgent. This
repository owns the target app, public seed/reset contract and public build
identity handoff. It does not own Android QAgent runtime policy, private Ground
Truth, evaluator verdicts or release admission.

## Language

Keep code, identifiers, schemas, commands, paths and logs in English. Use
Korean for user-facing progress and reports unless the user requests another
language.

## Authority and safety

- Never store signing keys, passwords, tokens, credentials or private
  evaluator material.
- Never store private expected graph/state/finding/severity/evidence answers or
  a private repository path.
- Keep every seed confined to the synthetic app and deterministic local data.
  No real payment, message, upload, account or third-party effect is allowed.
- Do not install or run an APK, start ADB/emulator, or contact a device without
  the exact Android QAgent target/device/action approval.
- Do not claim conformance, accuracy, Android capability or release readiness
  from source, static validation or a successful build alone.

## Public fixture invariants

- Public seed IDs are exactly `A-D-001` through `A-D-010`.
- Provide `clean`, `normal_twin`, every single seed and `all_seeds`
  compositions.
- Every seed has exactly one public family, independently switchable
  activation, a normal twin and deterministic reset behavior.
- Keep target revision, fixture revision, package/build/signing reference and
  reset identity machine-readable.
- A public handoff may contain opaque digests, but never hidden expected
  answers.

## Working method

1. Read this file and the public handoff documents before changing source.
2. Implement the smallest independently testable seed/reset slice.
3. Add deterministic static/unit tests in the same change.
4. Run the lowest relevant verification and record non-claims.
5. Use reviewed branches and preserve unrelated user changes.
6. Use `rg` for search and `apply_patch` for deliberate text edits.
