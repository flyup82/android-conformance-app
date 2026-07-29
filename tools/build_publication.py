#!/usr/bin/env python3
"""Plan or execute the exact signed public APK build matrix without device contact."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_REVISION = "android-conformance-r2"
PACKAGE_ID = "io.github.flyup82.androidconformance"
VARIANTS = (
    "clean",
    "normalTwin",
    *(f"seed{index:03d}" for index in range(1, 11)),
    "allSeeds",
)
GRADLE_VARIANTS = (
    "Clean",
    "NormalTwin",
    *(f"Seed{index:03d}" for index in range(1, 11)),
    "AllSeeds",
)
TASKS = tuple(f":app:assemble{variant}Release" for variant in GRADLE_VARIANTS)
SIGNING_ENVIRONMENT = (
    "AQ_SIGNING_KEYSTORE",
    "AQ_SIGNING_STORE_PASSWORD",
    "AQ_SIGNING_KEY_ALIAS",
    "AQ_SIGNING_KEY_PASSWORD",
)
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
SOURCE_REVISION = re.compile(r"^[0-9a-f]{40}$")
CERTIFICATE_LINE = re.compile(
    r"Signer #[0-9]+ certificate SHA-256 digest: ([0-9A-Fa-f:]+)"
)


class BuildPublicationError(ValueError):
    pass


def publication_plan() -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "scope": "signed_apk_build_publication",
        "fixture_revision": FIXTURE_REVISION,
        "package_id": PACKAGE_ID,
        "variants": list(VARIANTS),
        "tasks": list(TASKS),
        "artifact_count": len(VARIANTS),
        "signing_mode": "user_managed_external",
        "artifact_channel": "github_actions_artifact",
        "retention_days": 30,
        "apk_install": False,
        "adb": False,
        "emulator": False,
        "device_contact": False,
    }


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def validate_signing_environment(
    environment: Mapping[str, str], repository_root: Path = ROOT
) -> Path:
    missing = [name for name in SIGNING_ENVIRONMENT if not environment.get(name)]
    if missing:
        raise BuildPublicationError(
            "signing_environment_missing:" + ",".join(sorted(missing))
        )
    keystore = Path(environment["AQ_SIGNING_KEYSTORE"])
    if not keystore.is_absolute():
        raise BuildPublicationError("signing_keystore_path_not_absolute")
    if keystore.is_symlink() or not keystore.is_file():
        raise BuildPublicationError("signing_keystore_invalid")
    resolved_keystore = keystore.resolve()
    if _is_within(resolved_keystore, repository_root.resolve()):
        raise BuildPublicationError("signing_keystore_inside_repository")
    if stat.S_IMODE(resolved_keystore.stat().st_mode) & 0o077:
        raise BuildPublicationError("signing_keystore_not_owner_only")
    return resolved_keystore


def build_release_matrix(
    *,
    execute: bool,
    environment: Mapping[str, str] | None = None,
    repository_root: Path = ROOT,
    runner: Callable[..., Any] = subprocess.run,
) -> dict[str, Any]:
    plan = publication_plan()
    if not execute:
        return {
            **plan,
            "executed": False,
            "signing_performed": False,
            "artifact_staged": False,
        }
    validate_signing_environment(environment or {}, repository_root)
    command = (
        str(repository_root / "gradlew"),
        "--no-daemon",
        "--stacktrace",
        *TASKS,
    )
    runner(command, cwd=repository_root, env=dict(environment or {}), check=True)
    return {
        **plan,
        "executed": True,
        "signing_performed": True,
        "artifact_staged": False,
    }


def parse_signer_certificate_digest(output: str) -> str:
    digests = [
        match.replace(":", "").lower()
        for match in CERTIFICATE_LINE.findall(output)
    ]
    if len(digests) != 1:
        raise BuildPublicationError("apk_signer_count_or_digest_invalid")
    digest = digests[0]
    if len(digest) != 64:
        raise BuildPublicationError("apk_signer_digest_invalid")
    return "sha256:" + digest


def read_signer_certificate_digest(apk: Path, apksigner: Path) -> str:
    result = subprocess.run(
        (
            str(apksigner),
            "verify",
            "--verbose",
            "--print-certs",
            str(apk),
        ),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise BuildPublicationError(f"apk_signature_invalid:{apk.name}")
    return parse_signer_certificate_digest(result.stdout)


def _apk_path(repository_root: Path, variant: str) -> Path:
    return (
        repository_root
        / "app"
        / "build"
        / "outputs"
        / "apk"
        / variant
        / "release"
        / f"app-{variant}-release.apk"
    )


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_publication_digest(value: dict[str, Any]) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def collect_publication(
    *,
    source_revision: str,
    expected_certificate_sha256: str,
    output_dir: Path,
    repository_root: Path = ROOT,
    apksigner: Path | None = None,
    signer_reader: Callable[[Path, Path], str] = read_signer_certificate_digest,
) -> dict[str, Any]:
    if not SOURCE_REVISION.fullmatch(source_revision):
        raise BuildPublicationError("source_revision_invalid")
    if not SHA256.fullmatch(expected_certificate_sha256):
        raise BuildPublicationError("certificate_sha256_invalid")
    if not output_dir.is_absolute():
        raise BuildPublicationError("publication_output_not_absolute")
    if os.path.lexists(output_dir):
        raise BuildPublicationError("publication_output_already_exists")
    output_parent = output_dir.parent
    if output_parent.is_symlink() or not output_parent.is_dir():
        raise BuildPublicationError("publication_parent_invalid")
    signer = apksigner or Path("apksigner")
    root = repository_root.resolve()
    inspected: list[dict[str, str]] = []
    for variant in VARIANTS:
        apk = _apk_path(repository_root, variant)
        if apk.is_symlink() or not apk.is_file():
            raise BuildPublicationError(f"apk_missing_or_invalid:{variant}")
        resolved = apk.resolve()
        if not _is_within(resolved, root):
            raise BuildPublicationError(f"apk_path_escape:{variant}")
        observed_certificate = signer_reader(resolved, signer)
        if observed_certificate != expected_certificate_sha256:
            raise BuildPublicationError(f"apk_signer_mismatch:{variant}")
        inspected.append(
            {
                "variant": variant,
                "filename": apk.name,
                "apk_sha256": _sha256(resolved),
                "signing_certificate_sha256": observed_certificate,
            }
        )

    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "type": "PublicBuildPublication",
        "status": "staged_for_github_actions_artifact",
        "source_revision": source_revision,
        "fixture_revision": FIXTURE_REVISION,
        "package_id": PACKAGE_ID,
        "signing": {
            "mode": "user_managed_external",
            "reference": "github-environment:conformance-release",
            "certificate_sha256": expected_certificate_sha256,
            "key_material_present": False,
        },
        "artifacts": inspected,
        "artifact_channel": "github_actions_artifact",
        "retention_days": 30,
        "claims": {
            "signed_apk_set_verified": True,
            "device_verified": False,
            "conformance_verified": False,
            "generalization": False,
        },
    }
    manifest = {**body, "publication_digest": canonical_publication_digest(body)}
    staging = Path(
        tempfile.mkdtemp(prefix=".android-conformance-publication.", dir=output_parent)
    )
    try:
        apk_output = staging / "apks"
        apk_output.mkdir()
        for item in inspected:
            source = _apk_path(repository_root, item["variant"])
            destination = apk_output / item["filename"]
            shutil.copyfile(source, destination)
            if _sha256(destination) != item["apk_sha256"]:
                raise BuildPublicationError(
                    f"apk_copy_digest_mismatch:{item['variant']}"
                )
            if (
                signer_reader(destination, signer)
                != item["signing_certificate_sha256"]
            ):
                raise BuildPublicationError(
                    f"apk_copy_signer_mismatch:{item['variant']}"
                )
        (staging / "build-publication.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(staging, output_dir)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--source-revision")
    parser.add_argument("--certificate-sha256")
    parser.add_argument("--apksigner", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    if not args.execute:
        print(json.dumps(build_release_matrix(execute=False), sort_keys=True))
        return 0
    if (
        args.source_revision is None
        or args.certificate_sha256 is None
        or args.apksigner is None
        or args.output_dir is None
    ):
        parser.error(
            "--execute requires --source-revision, --certificate-sha256, "
            "--apksigner and --output-dir"
        )
    try:
        result = build_release_matrix(execute=True, environment=os.environ)
        manifest = collect_publication(
            source_revision=args.source_revision,
            expected_certificate_sha256=args.certificate_sha256,
            output_dir=args.output_dir,
            apksigner=args.apksigner,
        )
    except (OSError, subprocess.SubprocessError, BuildPublicationError) as error:
        print(f"build_publication_failed:{error}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                **result,
                "artifact_staged": True,
                "publication_digest": manifest["publication_digest"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
