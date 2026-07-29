from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.validate_public_handoff import ValidationError, validate


ROOT = Path(__file__).resolve().parents[1]


class PublicHandoffTest(unittest.TestCase):
    def copy_fixture(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        shutil.copytree(ROOT / "public", root / "public")
        return temp, root

    def copy_repository(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        shutil.copytree(
            ROOT,
            root,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
        return temp, root

    def mutate(self, root: Path, name: str, callback) -> None:
        path = root / "public" / name
        value = json.loads(path.read_text(encoding="utf-8"))
        callback(value)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

    def test_current_public_handoff_is_valid(self) -> None:
        validate(ROOT)

    def test_private_expected_field_is_rejected(self) -> None:
        temp, root = self.copy_fixture()
        self.addCleanup(temp.cleanup)
        self.mutate(
            root,
            "conformance-handoff.json",
            lambda value: value.update({"expected_graph": {"nodes": []}}),
        )
        with self.assertRaisesRegex(ValidationError, "private or secret-shaped key"):
            validate(root)

    def test_missing_seed_is_rejected(self) -> None:
        temp, root = self.copy_fixture()
        self.addCleanup(temp.cleanup)
        self.mutate(
            root,
            "seed-catalog.json",
            lambda value: value["seeds"].pop(),
        )
        with self.assertRaisesRegex(ValidationError, "seed order or membership"):
            validate(root)

    def test_trigger_drift_is_rejected(self) -> None:
        temp, root = self.copy_fixture()
        self.addCleanup(temp.cleanup)
        self.mutate(
            root,
            "seed-catalog.json",
            lambda value: value["seeds"][3].update({"trigger_id": "other_retry"}),
        )
        with self.assertRaisesRegex(ValidationError, "catalog seed public handoff"):
            validate(root)

    def test_effect_scope_drift_is_rejected(self) -> None:
        temp, root = self.copy_fixture()
        self.addCleanup(temp.cleanup)
        self.mutate(
            root,
            "seed-catalog.json",
            lambda value: value["seeds"][8].update(
                {"external_effects": ["implicit_external_intent"]}
            ),
        )
        with self.assertRaisesRegex(ValidationError, "catalog seed public handoff"):
            validate(root)

    def test_reset_package_drift_is_rejected(self) -> None:
        temp, root = self.copy_fixture()
        self.addCleanup(temp.cleanup)
        self.mutate(
            root,
            "reset-profile.json",
            lambda value: value.update({"package_id": "other.package"}),
        )
        with self.assertRaisesRegex(ValidationError, "reset identity"):
            validate(root)

    def test_published_claim_without_artifact_is_rejected(self) -> None:
        temp, root = self.copy_fixture()
        self.addCleanup(temp.cleanup)
        self.mutate(
            root,
            "conformance-handoff.json",
            lambda value: value["claims"].update({"apk_verified": True}),
        )
        with self.assertRaisesRegex(ValidationError, "claim boundary"):
            validate(root)

    def test_missing_behavior_unit_projection_is_rejected(self) -> None:
        temp, root = self.copy_repository()
        self.addCleanup(temp.cleanup)
        behavior = (
            root
            / "app/src/main/java/io/github/flyup82/androidconformance/SeedBehavior.java"
        )
        behavior.write_text(
            behavior.read_text(encoding="utf-8").replace(
                "webViewRecoveryAvailable",
                "removedRecoveryMethod",
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValidationError, "behavior contract"):
            validate(root)

    def test_external_network_permission_is_rejected(self) -> None:
        temp, root = self.copy_repository()
        self.addCleanup(temp.cleanup)
        manifest = root / "app/src/main/AndroidManifest.xml"
        manifest.write_text(
            manifest.read_text(encoding="utf-8").replace(
                "<application",
                '<uses-permission android:name="android.permission.INTERNET" />\n'
                "    <application",
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValidationError, "external network permission"):
            validate(root)

    def test_compile_matrix_missing_variant_is_rejected(self) -> None:
        temp, root = self.copy_repository()
        self.addCleanup(temp.cleanup)
        script = root / "tools/compile_source_matrix.py"
        script.write_text(
            script.read_text(encoding="utf-8").replace('"Seed010",', ""),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValidationError, "compile matrix missing Seed010"):
            validate(root)

    def test_workflow_apk_assembly_is_rejected(self) -> None:
        temp, root = self.copy_repository()
        self.addCleanup(temp.cleanup)
        workflow = root / ".github/workflows/public-contract.yml"
        workflow.write_text(
            workflow.read_text(encoding="utf-8").replace(
                "python3 tools/compile_source_matrix.py --execute",
                "./gradlew assemble",
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValidationError, "compile-only CI"):
            validate(root)

    def test_android_setup_action_pin_drift_is_rejected(self) -> None:
        temp, root = self.copy_repository()
        self.addCleanup(temp.cleanup)
        workflow = root / ".github/workflows/public-contract.yml"
        workflow.write_text(
            workflow.read_text(encoding="utf-8").replace(
                "android-actions/setup-android@"
                "9fc6c4e9069bf8d3d10b2204b1fb8f6ef7065407",
                "android-actions/setup-android@v3",
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValidationError, "compile-only CI missing"):
            validate(root)

    def test_publication_workflow_cannot_become_automatic(self) -> None:
        temp, root = self.copy_repository()
        self.addCleanup(temp.cleanup)
        workflow = root / ".github/workflows/build-publication.yml"
        workflow.write_text(
            workflow.read_text(encoding="utf-8").replace(
                "  workflow_dispatch:",
                "  pull_request:",
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            ValidationError, "build publication workflow missing workflow_dispatch"
        ):
            validate(root)

    def test_publication_workflow_requires_exact_action_pins(self) -> None:
        temp, root = self.copy_repository()
        self.addCleanup(temp.cleanup)
        workflow = root / ".github/workflows/build-publication.yml"
        workflow.write_text(
            workflow.read_text(encoding="utf-8").replace(
                "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
                "actions/upload-artifact@v4",
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            ValidationError, "build publication workflow missing actions/upload"
        ):
            validate(root)

    def test_publication_contract_cannot_claim_an_artifact_before_handoff(self) -> None:
        temp, root = self.copy_repository()
        self.addCleanup(temp.cleanup)
        path = root / "public/build-publication-contract.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["claims"]["signed_apk_published"] = True
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValidationError, "build publication contract"):
            validate(root)

    def test_wrapper_tamper_is_rejected(self) -> None:
        temp, root = self.copy_repository()
        self.addCleanup(temp.cleanup)
        with (root / "gradlew").open("a", encoding="utf-8") as stream:
            stream.write("\n# tampered\n")
        with self.assertRaisesRegex(ValidationError, "wrapper digest gradlew"):
            validate(root)

    def test_signing_material_is_rejected(self) -> None:
        temp, root = self.copy_repository()
        self.addCleanup(temp.cleanup)
        (root / "test-key.jks").write_bytes(b"not-a-real-key")
        with self.assertRaisesRegex(ValidationError, "signing material"):
            validate(root)


if __name__ == "__main__":
    unittest.main()
