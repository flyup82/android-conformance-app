#!/usr/bin/env python3
"""Validate public conformance handoff without Android or private GT access."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
PACKAGE_ID = "io.github.flyup82.androidconformance"
SEED_IDS = [f"A-D-{index:03d}" for index in range(1, 11)]
FORBIDDEN_KEY_PARTS = {
    "credential",
    "expected_answer",
    "expected_evidence",
    "expected_finding",
    "expected_graph",
    "expected_severity",
    "keystore",
    "password",
    "private_gt_path",
    "private_repository_path",
    "secret",
    "token",
}
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


class ValidationError(ValueError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path.name}: root must be an object")
    return value


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def bare_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = key.lower()
            if any(part in lowered for part in FORBIDDEN_KEY_PARTS):
                raise ValidationError(f"{path}.{key}: private or secret-shaped key")
            walk_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_keys(child, f"{path}[{index}]")


def validate_catalog(catalog: dict[str, Any]) -> None:
    if catalog.get("schema_version") != "1.0.0":
        raise ValidationError("catalog schema_version")
    if catalog.get("fixture_revision") != "android-conformance-r1":
        raise ValidationError("catalog fixture_revision")

    seeds = catalog.get("seeds")
    if not isinstance(seeds, list) or [item.get("id") for item in seeds] != SEED_IDS:
        raise ValidationError("catalog seed order or membership")
    if any(
        not isinstance(item.get("family"), str)
        or not isinstance(item.get("fixture_route"), str)
        or item.get("normal_twin_route") != item.get("fixture_route")
        or item.get("activation_flavor") != f"seed{index:03d}"
        for index, item in enumerate(seeds, 1)
    ):
        raise ValidationError("catalog seed public handoff")

    expected_names = ["clean", "normalTwin"] + [
        f"seed{index:03d}" for index in range(1, 11)
    ] + ["allSeeds"]
    compositions = catalog.get("compositions")
    if (
        not isinstance(compositions, list)
        or [item.get("name") for item in compositions] != expected_names
    ):
        raise ValidationError("composition names or order")
    for index, item in enumerate(compositions):
        active = item.get("active_seed_ids")
        if index == 0 and (item.get("kind") != "clean" or active != []):
            raise ValidationError("clean active seeds")
        if index == 1 and (item.get("kind") != "normal_twin" or active != []):
            raise ValidationError("normal twin active seeds")
        elif 2 <= index < 12:
            expected_id = SEED_IDS[index - 2]
            if item.get("kind") != "single_seed" or active != [expected_id]:
                raise ValidationError(f"single seed composition {expected_id}")
        elif index == 12 and (
            item.get("kind") != "all_seeds" or active != SEED_IDS
        ):
            raise ValidationError("all-seeds composition")


def validate_reset(reset: dict[str, Any]) -> None:
    if reset.get("schema_version") != "1.0.0":
        raise ValidationError("reset schema_version")
    if reset.get("package_id") != PACKAGE_ID or reset.get("deterministic") is not True:
        raise ValidationError("reset identity or determinism")
    if reset.get("authority") != "fresh_exact_android_qagent_approval_required":
        raise ValidationError("reset authority")
    if reset.get("steps") != [
        "force_stop_exact_package",
        "clear_exact_package_data",
        "launch_exact_main_activity",
        "verify_fixture_revision_and_composition",
    ]:
        raise ValidationError("reset steps")
    network = reset.get("network")
    if not isinstance(network, dict) or network.get("external_origin_count") != 0:
        raise ValidationError("reset network boundary")


def validate_handoff(
    handoff: dict[str, Any], catalog_path: Path, reset_path: Path
) -> None:
    if handoff.get("schema_version") != "1.0.0":
        raise ValidationError("handoff schema_version")
    if handoff.get("handoff_status") != "source_scaffold":
        raise ValidationError("handoff status must remain honest")
    if handoff.get("package_id") != PACKAGE_ID or handoff.get("namespace") != PACKAGE_ID:
        raise ValidationError("handoff package identity")
    if handoff.get("public_seed_catalog_digest") != digest(catalog_path):
        raise ValidationError("seed catalog digest")
    if handoff.get("reset_profile_digest") != digest(reset_path):
        raise ValidationError("reset profile digest")
    if handoff.get("source_revision") != "PENDING_REVIEWED_COMMIT":
        raise ValidationError("source revision must remain pending before merge")

    build = handoff.get("build")
    if not isinstance(build, dict) or build != {
        "status": "not_built_or_published",
        "artifact_sha256": None,
    }:
        raise ValidationError("build non-claim")
    signing = handoff.get("signing")
    if not isinstance(signing, dict):
        raise ValidationError("signing handoff")
    if signing != {
        "mode": "user_managed_external",
        "reference": "github-environment:conformance-release",
        "certificate_sha256": None,
        "status": "pending_user_handoff",
        "key_material_present": False,
    }:
        raise ValidationError("signing boundary")
    if handoff.get("private_ground_truth_present") is not False:
        raise ValidationError("private GT boundary")
    claims = handoff.get("claims")
    if not isinstance(claims, dict) or claims != {
        "source_scaffold_only": True,
        "apk_verified": False,
        "device_verified": False,
        "conformance_verified": False,
        "generalization": False,
    }:
        raise ValidationError("claim boundary")


def validate_wrapper(root: Path) -> None:
    lock = read_json(root / "gradle" / "wrapper" / "source-lock.json")
    if lock.get("version") != "9.5.0" or lock.get("source_tag") != "v9.5.0":
        raise ValidationError("wrapper version or source tag")
    files = lock.get("files")
    if not isinstance(files, dict):
        raise ValidationError("wrapper source lock")
    expected_paths = {
        "gradlew",
        "gradlew.bat",
        "gradle/wrapper/gradle-wrapper.jar",
    }
    if set(files) != expected_paths:
        raise ValidationError("wrapper file inventory")
    for relative in sorted(expected_paths):
        entry = files[relative]
        if not isinstance(entry, dict):
            raise ValidationError(f"wrapper entry {relative}")
        expected_url = (
            "https://raw.githubusercontent.com/gradle/gradle/v9.5.0/" + relative
        )
        if entry.get("url") != expected_url:
            raise ValidationError(f"wrapper source URL {relative}")
        if entry.get("sha256") != bare_digest(root / relative):
            raise ValidationError(f"wrapper digest {relative}")
    properties = (root / "gradle" / "wrapper" / "gradle-wrapper.properties").read_text(
        encoding="utf-8"
    )
    if "gradle-9.5.0-bin.zip" not in properties:
        raise ValidationError("wrapper distribution URL")


def validate_source_projection(root: Path) -> None:
    build = (root / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    required_build_fragments = [
        'namespace = "io.github.flyup82.androidconformance"',
        'applicationId = "io.github.flyup82.androidconformance"',
        "compileSdk = 36",
        "minSdk = 28",
        "targetSdk = 36",
        'versionName = "0.1.0-dev.1"',
        'create("clean")',
        'create("normalTwin")',
        'create("allSeeds")',
    ]
    for fragment in required_build_fragments:
        if fragment not in build:
            raise ValidationError(f"build projection missing {fragment}")
    if re.findall(r'"(A-D-[0-9]{3})"', build) != SEED_IDS:
        raise ValidationError("Gradle seed projection")
    if "seedIds.forEachIndexed" not in build:
        raise ValidationError("single-seed flavor generator")

    java_catalog = (
        root
        / "app"
        / "src"
        / "main"
        / "java"
        / "io"
        / "github"
        / "flyup82"
        / "androidconformance"
        / "SeedCatalog.java"
    ).read_text(encoding="utf-8")
    if re.findall(r'"(A-D-[0-9]{3})"', java_catalog) != SEED_IDS:
        raise ValidationError("Java seed projection")

    forbidden_material = [
        path
        for path in root.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and path.suffix.lower() in {".jks", ".keystore"}
    ]
    if forbidden_material:
        raise ValidationError("tracked or local signing material")


def validate(root: Path = ROOT) -> None:
    public = root / "public"
    catalog_path = public / "seed-catalog.json"
    reset_path = public / "reset-profile.json"
    handoff_path = public / "conformance-handoff.json"
    catalog = read_json(catalog_path)
    reset = read_json(reset_path)
    handoff = read_json(handoff_path)
    for document in (catalog, reset, handoff):
        walk_keys(document)
    validate_catalog(catalog)
    validate_reset(reset)
    validate_handoff(handoff, catalog_path, reset_path)
    validate_wrapper(root)
    validate_source_projection(root)


def main() -> int:
    try:
        validate()
    except (OSError, UnicodeError, json.JSONDecodeError, ValidationError) as error:
        print(f"public_handoff_invalid: {error}", file=sys.stderr)
        return 1
    print("public_handoff_valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
