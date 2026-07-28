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
are being developed through reviewed changes. The current source is a
composition/identity scaffold: it does not yet implement or claim the ten
seeded behaviors. No APK has been published, installed or executed, and no
Android device capability has been verified.

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
```

The Gradle wrapper is pinned to 9.5.0. Its official-tag source URLs and file
digests are recorded in `gradle/wrapper/source-lock.json`. A successful static
validation or Gradle configuration is not APK or device evidence.

## Security and authority

- Never commit a signing key, keystore password, token or credential.
- Never copy private Ground Truth or evaluator-private material here.
- Test APK publication, installation, ADB/emulator/device execution and release
  admission require their own Android QAgent gates.
- Seeded behavior is permitted only on an explicitly approved disposable lab
  target.

The normative product requirements remain in the `android-qagent` repository.
