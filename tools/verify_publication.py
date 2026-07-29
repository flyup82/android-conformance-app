#!/usr/bin/env python3
"""Verify one downloaded public signed-APK publication without device contact."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any, Callable, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.build_publication import (  # noqa: E402
    FIXTURE_REVISION,
    PACKAGE_ID,
    SHA256,
    SOURCE_REVISION,
    VARIANTS,
    canonical_publication_digest,
    read_signer_certificate_digest,
)


EXPECTED_ROOT_ENTRIES = frozenset({"apks", "build-publication.json"})
MANIFEST_MAX_BYTES = 128 * 1024


class PublicationVerificationError(ValueError):
    pass


def _exact_object(
    value: Any,
    fields: set[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise PublicationVerificationError(f"{label}_fields_invalid")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _read_manifest(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise PublicationVerificationError("publication_manifest_invalid")
    if path.stat().st_size > MANIFEST_MAX_BYTES:
        raise PublicationVerificationError("publication_manifest_invalid")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise PublicationVerificationError(
            "publication_manifest_invalid"
        ) from error
    if not isinstance(value, dict):
        raise PublicationVerificationError("publication_manifest_invalid")
    return value


def verify_publication(
    *,
    publication_dir: Path,
    expected_source_revision: str,
    expected_certificate_sha256: str,
    apksigner: Path,
    signer_reader: Callable[[Path, Path], str] = read_signer_certificate_digest,
) -> dict[str, Any]:
    if not SOURCE_REVISION.fullmatch(expected_source_revision):
        raise PublicationVerificationError("source_revision_invalid")
    if not SHA256.fullmatch(expected_certificate_sha256):
        raise PublicationVerificationError("certificate_sha256_invalid")
    if (
        publication_dir.is_symlink()
        or not publication_dir.is_dir()
        or not publication_dir.is_absolute()
    ):
        raise PublicationVerificationError("publication_directory_invalid")
    if (
        apksigner.is_symlink()
        or not apksigner.is_file()
        or not os.access(apksigner, os.X_OK)
    ):
        raise PublicationVerificationError("apksigner_invalid")

    entries = {entry.name for entry in publication_dir.iterdir()}
    if entries != EXPECTED_ROOT_ENTRIES:
        raise PublicationVerificationError("publication_inventory_invalid")
    apk_root = publication_dir / "apks"
    if apk_root.is_symlink() or not apk_root.is_dir():
        raise PublicationVerificationError("publication_inventory_invalid")

    manifest = _read_manifest(publication_dir / "build-publication.json")
    root = _exact_object(
        manifest,
        {
            "schema_version",
            "type",
            "status",
            "source_revision",
            "fixture_revision",
            "package_id",
            "signing",
            "artifacts",
            "artifact_channel",
            "retention_days",
            "claims",
            "publication_digest",
        },
        "publication",
    )
    signing = _exact_object(
        root["signing"],
        {"mode", "reference", "certificate_sha256", "key_material_present"},
        "signing",
    )
    claims = _exact_object(
        root["claims"],
        {
            "signed_apk_set_verified",
            "device_verified",
            "conformance_verified",
            "generalization",
        },
        "claims",
    )
    if (
        root["schema_version"] != "1.0.0"
        or root["type"] != "PublicBuildPublication"
        or root["status"] != "staged_for_github_actions_artifact"
        or root["source_revision"] != expected_source_revision
        or root["fixture_revision"] != FIXTURE_REVISION
        or root["package_id"] != PACKAGE_ID
        or root["artifact_channel"] != "github_actions_artifact"
        or root["retention_days"] != 30
        or signing
        != {
            "mode": "user_managed_external",
            "reference": "github-environment:conformance-release",
            "certificate_sha256": expected_certificate_sha256,
            "key_material_present": False,
        }
        or claims
        != {
            "signed_apk_set_verified": True,
            "device_verified": False,
            "conformance_verified": False,
            "generalization": False,
        }
    ):
        raise PublicationVerificationError("publication_contract_mismatch")

    digest_body = dict(root)
    publication_digest = digest_body.pop("publication_digest")
    if (
        not isinstance(publication_digest, str)
        or not SHA256.fullmatch(publication_digest)
        or publication_digest != canonical_publication_digest(digest_body)
    ):
        raise PublicationVerificationError("publication_digest_mismatch")

    artifacts = root["artifacts"]
    if not isinstance(artifacts, list) or len(artifacts) != len(VARIANTS):
        raise PublicationVerificationError("publication_artifacts_invalid")
    expected_filenames = {f"app-{variant}-release.apk" for variant in VARIANTS}
    actual_entries = {entry.name for entry in apk_root.iterdir()}
    if actual_entries != expected_filenames:
        raise PublicationVerificationError("publication_inventory_invalid")

    for index, (artifact, variant) in enumerate(zip(artifacts, VARIANTS)):
        item = _exact_object(
            artifact,
            {
                "variant",
                "filename",
                "apk_sha256",
                "signing_certificate_sha256",
            },
            f"artifact_{index}",
        )
        expected_filename = f"app-{variant}-release.apk"
        if (
            item["variant"] != variant
            or item["filename"] != expected_filename
            or not isinstance(item["apk_sha256"], str)
            or not SHA256.fullmatch(item["apk_sha256"])
            or item["signing_certificate_sha256"]
            != expected_certificate_sha256
        ):
            raise PublicationVerificationError("publication_artifacts_invalid")
        apk = apk_root / expected_filename
        if (
            apk.is_symlink()
            or not apk.is_file()
            or not stat.S_ISREG(apk.stat().st_mode)
        ):
            raise PublicationVerificationError("publication_inventory_invalid")
        if _sha256(apk) != item["apk_sha256"]:
            raise PublicationVerificationError("apk_digest_mismatch")
        if signer_reader(apk, apksigner) != expected_certificate_sha256:
            raise PublicationVerificationError("apk_signer_mismatch")
        if _sha256(apk) != item["apk_sha256"]:
            raise PublicationVerificationError("apk_digest_mismatch")

    return {
        "verified": True,
        "code": "public_build_publication_verified",
        "source_revision": expected_source_revision,
        "publication_digest": publication_digest,
        "signing_certificate_sha256": expected_certificate_sha256,
        "artifact_count": len(VARIANTS),
        "device_contacted": False,
        "conformance_verified": False,
        "generalization": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publication-dir", required=True, type=Path)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--certificate-sha256", required=True)
    parser.add_argument("--apksigner", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = verify_publication(
            publication_dir=args.publication_dir,
            expected_source_revision=args.source_revision,
            expected_certificate_sha256=args.certificate_sha256,
            apksigner=args.apksigner,
        )
    except (OSError, PublicationVerificationError) as error:
        code = (
            str(error)
            if isinstance(error, PublicationVerificationError)
            else "publication_io_error"
        )
        print(json.dumps({"verified": False, "code": code}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
