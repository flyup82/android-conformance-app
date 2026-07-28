# Android Conformance App

> **DRAFT — not a released or verified Android QAgent target**

`android-conformance-app` is the public, deterministic test target for
[`android-qagent`](https://github.com/flyup82/android-qagent). It is a synthetic
lab application, not a production app and not Android QAgent itself.

The repository will provide:

- one clean baseline and one normal-twin composition;
- independently switchable public seeds `A-D-001` through `A-D-010`;
- deterministic fixture identity and reset instructions;
- public package, build and signing-certificate references;
- no private expected graph, finding, severity, evidence or evaluator answer.

Private Ground Truth belongs to a separate USER/evaluator-only repository.
Its path, content, credentials and raw evaluator output must never be added
here.

## Current status

Repository authority was approved by Android QAgent
`DEC-20260728-043`. The Android source, public handoff and static validation
are being developed through reviewed changes. Fixture revision
`android-conformance-r2` implements source-level clean/normal-twin behavior and
ten independently activated seed deltas. The behavior model has a plain-JDK
unit harness, but the Android app has not been built, published, installed or
executed. No APK, device, or conformance capability has been verified.

## Public behavior surfaces

| Seed | Route | Deterministic trigger | Bounded effect |
|---|---|---|---|
| `A-D-001` | `lifecycle` | recreate after increment | app-local lifecycle state |
| `A-D-002` | `navigation` | back from local detail | app-local route |
| `A-D-003` | `permission` | deny camera permission | permission prompt only; camera is never opened |
| `A-D-004` | `network` | retry embedded transport | no external network |
| `A-D-005` | `accessibility` | inspect symbol action | view semantics only |
| `A-D-006` | `adaptive` | inspect long localized text | layout only |
| `A-D-007` | `stability` | trigger controlled failure | exact fixture process only |
| `A-D-008` | `persistence` | recreate after increment | exact fixture private storage only |
| `A-D-009` | `intent` | send untrusted local route | explicit same-package intent only |
| `A-D-010` | `webview` | activate local recovery link | embedded HTML only |

The table is a public trigger/safety contract, not a private expected graph,
finding, severity, evidence, or evaluator answer.

## Public compositions

The `fixture` product-flavor dimension declares:

- `clean` and `normalTwin`;
- `seed001` through `seed010`, each activating exactly one matching public
  seed;
- `allSeeds`, activating the ordered complete catalog.

All variants keep the exact package
`io.github.flyup82.androidconformance`; variants replace one another rather
than creating parallel package identities. Release signing is intentionally
external and USER-owned.

Public machine-readable handoff files live under `public/`. Validate them
without Android tooling:

```bash
python3 tools/validate_public_handoff.py
python3 -m unittest discover -s tests -v
python3 tools/run_behavior_unit_tests.py
```

The last command requires JDK 17 and compiles only the pure-Java behavior model
and self-test; it does not invoke Gradle or Android tooling. The Gradle wrapper
is pinned to 9.5.0. Its official-tag source URLs and file digests are recorded
in `gradle/wrapper/source-lock.json`. Successful static or pure-Java validation
is not Android build, APK, or device evidence.

## Security and authority

- Never commit a signing key, keystore password, token or credential.
- Never copy private Ground Truth or evaluator-private material here.
- Test APK publication, installation, ADB/emulator/device execution and release
  admission require their own Android QAgent gates.
- Seeded behavior is permitted only on an explicitly approved disposable lab
  target.

The normative product requirements remain in the `android-qagent` repository.
