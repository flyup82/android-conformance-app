from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from tools.build_publication import (
    GRADLE_VARIANTS,
    TASKS,
    VARIANTS,
    BuildPublicationError,
    build_release_matrix,
    collect_publication,
    parse_signer_certificate_digest,
)


ROOT = Path(__file__).resolve().parents[1]
CERTIFICATE = "sha256:" + "a" * 64
SOURCE_REVISION = "b" * 40


class BuildPublicationTest(unittest.TestCase):
    def signing_environment(self, keystore: Path) -> dict[str, str]:
        return {
            "AQ_SIGNING_KEYSTORE": str(keystore),
            "AQ_SIGNING_STORE_PASSWORD": "not-a-real-password",
            "AQ_SIGNING_KEY_ALIAS": "conformance",
            "AQ_SIGNING_KEY_PASSWORD": "not-a-real-password",
        }

    def test_plan_has_exact_matrix_and_zero_boundary_calls(self) -> None:
        calls: list[object] = []
        result = build_release_matrix(
            execute=False,
            runner=lambda *args, **kwargs: calls.append((args, kwargs)),
        )
        self.assertEqual(calls, [])
        self.assertEqual(result["variants"], list(VARIANTS))
        self.assertEqual(result["tasks"], list(TASKS))
        self.assertEqual(result["artifact_count"], 13)
        self.assertFalse(result["executed"])
        self.assertFalse(result["signing_performed"])
        self.assertFalse(result["apk_install"])
        self.assertFalse(result["device_contact"])

    def test_execute_rejects_missing_signing_environment_before_runner(self) -> None:
        calls: list[object] = []
        with self.assertRaisesRegex(
            BuildPublicationError, "signing_environment_missing"
        ):
            build_release_matrix(
                execute=True,
                environment={},
                runner=lambda *args, **kwargs: calls.append((args, kwargs)),
            )
        self.assertEqual(calls, [])

    def test_execute_invokes_exact_release_matrix_once(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            keystore = Path(temp) / "external.jks"
            keystore.write_bytes(b"opaque-test-material")
            keystore.chmod(0o600)
            calls: list[tuple[tuple[str, ...], Path, bool]] = []

            def runner(command, *, cwd, env, check):
                self.assertEqual(env["AQ_SIGNING_KEY_ALIAS"], "conformance")
                calls.append((tuple(command), cwd, check))

            result = build_release_matrix(
                execute=True,
                environment=self.signing_environment(keystore),
                runner=runner,
            )
        self.assertEqual(len(calls), 1)
        self.assertEqual(
            calls[0][0],
            (
                str(ROOT / "gradlew"),
                "--no-daemon",
                "--stacktrace",
                *TASKS,
            ),
        )
        self.assertEqual(calls[0][1], ROOT)
        self.assertTrue(calls[0][2])
        self.assertEqual(len(GRADLE_VARIANTS), 13)
        self.assertTrue(result["signing_performed"])

    def test_keystore_inside_repository_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            keystore = root / "local.jks"
            keystore.write_bytes(b"opaque-test-material")
            keystore.chmod(0o600)
            with self.assertRaisesRegex(
                BuildPublicationError, "signing_keystore_inside_repository"
            ):
                build_release_matrix(
                    execute=True,
                    environment=self.signing_environment(keystore),
                    repository_root=root,
                    runner=lambda *args, **kwargs: None,
                )

    def create_fake_apks(self, root: Path) -> None:
        for variant in VARIANTS:
            apk = (
                root
                / "app"
                / "build"
                / "outputs"
                / "apk"
                / variant
                / "release"
                / f"app-{variant}-release.apk"
            )
            apk.parent.mkdir(parents=True)
            apk.write_bytes(f"signed-{variant}".encode())

    def test_collection_exact_matches_all_signers_before_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            output = Path(temp) / "publication"
            self.create_fake_apks(root)
            manifest = collect_publication(
                source_revision=SOURCE_REVISION,
                expected_certificate_sha256=CERTIFICATE,
                output_dir=output,
                repository_root=root,
                apksigner=Path("/exact/apksigner"),
                signer_reader=lambda apk, signer: CERTIFICATE,
            )
            self.assertEqual(len(manifest["artifacts"]), 13)
            self.assertEqual(
                {item["variant"] for item in manifest["artifacts"]},
                set(VARIANTS),
            )
            self.assertEqual(
                {item["signing_certificate_sha256"] for item in manifest["artifacts"]},
                {CERTIFICATE},
            )
            self.assertTrue((output / "build-publication.json").is_file())
            self.assertEqual(len(list((output / "apks").glob("*.apk"))), 13)

    def test_signer_mismatch_leaves_zero_publication_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            output = Path(temp) / "publication"
            self.create_fake_apks(root)
            with self.assertRaisesRegex(BuildPublicationError, "apk_signer_mismatch"):
                collect_publication(
                    source_revision=SOURCE_REVISION,
                    expected_certificate_sha256=CERTIFICATE,
                    output_dir=output,
                    repository_root=root,
                    apksigner=Path("/exact/apksigner"),
                    signer_reader=lambda apk, signer: "sha256:" + "c" * 64,
                )
            self.assertFalse(output.exists())

    def test_apksigner_output_requires_exactly_one_certificate(self) -> None:
        output = (
            "Signer #1 certificate SHA-256 digest: "
            + ":".join(["AA"] * 32)
        )
        self.assertEqual(parse_signer_certificate_digest(output), CERTIFICATE)
        with self.assertRaisesRegex(
            BuildPublicationError, "apk_signer_count_or_digest_invalid"
        ):
            parse_signer_certificate_digest(output + "\n" + output)


if __name__ == "__main__":
    unittest.main()
