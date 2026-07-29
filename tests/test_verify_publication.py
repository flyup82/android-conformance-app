from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.build_publication import VARIANTS, collect_publication
from tools.verify_publication import (
    PublicationVerificationError,
    verify_publication,
)


CERTIFICATE = "sha256:" + "a" * 64
SOURCE_REVISION = "b" * 40


class VerifyPublicationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repository = self.root / "repository"
        self.publication = self.root / "publication"
        self.apksigner = self.root / "apksigner"
        self.apksigner.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        self.apksigner.chmod(0o700)
        for variant in VARIANTS:
            apk = (
                self.repository
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
        collect_publication(
            source_revision=SOURCE_REVISION,
            expected_certificate_sha256=CERTIFICATE,
            output_dir=self.publication,
            repository_root=self.repository,
            apksigner=self.apksigner,
            signer_reader=lambda apk, signer: CERTIFICATE,
        )

    def verify(self) -> dict:
        return verify_publication(
            publication_dir=self.publication,
            expected_source_revision=SOURCE_REVISION,
            expected_certificate_sha256=CERTIFICATE,
            apksigner=self.apksigner,
            signer_reader=lambda apk, signer: CERTIFICATE,
        )

    def manifest(self) -> tuple[Path, dict]:
        path = self.publication / "build-publication.json"
        return path, json.loads(path.read_text(encoding="utf-8"))

    def write_manifest(self, value: dict) -> None:
        path = self.publication / "build-publication.json"
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_exact_downloaded_publication_is_verified_without_device(self) -> None:
        result = self.verify()
        self.assertTrue(result["verified"])
        self.assertEqual(result["artifact_count"], 13)
        self.assertFalse(result["device_contacted"])
        self.assertFalse(result["conformance_verified"])
        self.assertFalse(result["generalization"])

    def test_apk_byte_or_signer_tamper_fails_closed(self) -> None:
        apk = self.publication / "apks" / "app-clean-release.apk"
        apk.write_bytes(b"tampered")
        with self.assertRaisesRegex(
            PublicationVerificationError,
            "apk_digest_mismatch",
        ):
            self.verify()

        apk.write_bytes(b"signed-clean")
        with self.assertRaisesRegex(
            PublicationVerificationError,
            "apk_signer_mismatch",
        ):
            verify_publication(
                publication_dir=self.publication,
                expected_source_revision=SOURCE_REVISION,
                expected_certificate_sha256=CERTIFICATE,
                apksigner=self.apksigner,
                signer_reader=lambda path, signer: "sha256:" + "c" * 64,
            )

        def tampering_signer(path: Path, signer: Path) -> str:
            path.write_bytes(b"tampered-during-signer-check")
            return CERTIFICATE

        with self.assertRaisesRegex(
            PublicationVerificationError,
            "apk_digest_mismatch",
        ):
            verify_publication(
                publication_dir=self.publication,
                expected_source_revision=SOURCE_REVISION,
                expected_certificate_sha256=CERTIFICATE,
                apksigner=self.apksigner,
                signer_reader=tampering_signer,
            )

    def test_manifest_digest_and_source_drift_fail_closed(self) -> None:
        _, manifest = self.manifest()
        manifest["claims"]["device_verified"] = True
        self.write_manifest(manifest)
        with self.assertRaisesRegex(
            PublicationVerificationError,
            "publication_contract_mismatch",
        ):
            self.verify()

        manifest["claims"]["device_verified"] = False
        self.write_manifest(manifest)
        with self.assertRaisesRegex(
            PublicationVerificationError,
            "publication_contract_mismatch",
        ):
            verify_publication(
                publication_dir=self.publication,
                expected_source_revision="c" * 40,
                expected_certificate_sha256=CERTIFICATE,
                apksigner=self.apksigner,
                signer_reader=lambda path, signer: CERTIFICATE,
            )

    def test_extra_reordered_or_symlink_artifact_fails_closed(self) -> None:
        extra = self.publication / "apks" / "unexpected.apk"
        extra.write_bytes(b"unexpected")
        with self.assertRaisesRegex(
            PublicationVerificationError,
            "publication_inventory_invalid",
        ):
            self.verify()
        extra.unlink()

        path, manifest = self.manifest()
        manifest["artifacts"][0:2] = reversed(manifest["artifacts"][0:2])
        path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            PublicationVerificationError,
            "publication_digest_mismatch|publication_artifacts_invalid",
        ):
            self.verify()

        manifest["artifacts"][0:2] = reversed(manifest["artifacts"][0:2])
        self.write_manifest(manifest)
        target = self.publication / "apks" / "app-clean-release.apk"
        target.unlink()
        target.symlink_to(self.repository / "outside.apk")
        with self.assertRaisesRegex(
            PublicationVerificationError,
            "publication_inventory_invalid",
        ):
            self.verify()

    def test_verifier_has_no_signing_secret_or_device_surface(self) -> None:
        source = (
            Path(__file__).resolve().parents[1]
            / "tools"
            / "verify_publication.py"
        ).read_text(encoding="utf-8")
        for forbidden in (
            "AQ_SIGNING_STORE_PASSWORD",
            "AQ_SIGNING_KEY_PASSWORD",
            "AQ_SIGNING_KEYSTORE",
            "adb ",
            "emulator",
            "install",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
