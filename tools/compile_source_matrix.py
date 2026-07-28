#!/usr/bin/env python3
"""Plan or execute the compile-only public fixture matrix.

This helper invokes only Java source compilation tasks. It never assembles,
packages, signs, publishes, installs, starts ADB/emulator, or contacts a device.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from collections.abc import Callable, Sequence
from typing import Any


VARIANTS = (
    "Clean",
    "NormalTwin",
    "Seed001",
    "Seed002",
    "Seed003",
    "Seed004",
    "Seed005",
    "Seed006",
    "Seed007",
    "Seed008",
    "Seed009",
    "Seed010",
    "AllSeeds",
)
TASKS = tuple(
    f":app:compile{variant}DebugJavaWithJavac"
    for variant in VARIANTS
)
FORBIDDEN_TASK_PARTS = (
    "assemble",
    "bundle",
    "package",
    "sign",
    "publish",
    "upload",
    "install",
    "connected",
    "device",
    "adb",
    "emulator",
)


class CompileMatrixError(ValueError):
    pass


def compile_command() -> tuple[str, ...]:
    command = ("./gradlew", "--no-daemon", "--stacktrace", *TASKS)
    validate_compile_command(command)
    return command


def validate_compile_command(command: Sequence[str]) -> None:
    if tuple(command[:3]) != ("./gradlew", "--no-daemon", "--stacktrace"):
        raise CompileMatrixError("compile command prefix is not exact")
    tasks = tuple(command[3:])
    if tasks != TASKS or len(tasks) != 13 or len(set(tasks)) != 13:
        raise CompileMatrixError("compile task matrix is incomplete or reordered")
    for task in tasks:
        lowered = task.lower()
        if not task.startswith(":app:compile") or not task.endswith(
            "DebugJavaWithJavac"
        ):
            raise CompileMatrixError("non-compile Gradle task is forbidden")
        if any(part in lowered for part in FORBIDDEN_TASK_PARTS):
            raise CompileMatrixError("package/sign/publish/device task is forbidden")


def run_compile_matrix(
    *,
    execute: bool,
    runner: Callable[..., Any] = subprocess.run,
) -> dict[str, Any]:
    command = compile_command()
    if not execute:
        return {
            "scope": "android_source_compile_only",
            "executed": False,
            "task_count": len(TASKS),
            "variants": list(VARIANTS),
            "apk_packaged": False,
            "signing_performed": False,
            "artifact_published": False,
            "device_contacted": False,
        }
    runner(command, check=True)
    return {
        "scope": "android_source_compile_only",
        "executed": True,
        "task_count": len(TASKS),
        "variants": list(VARIANTS),
        "apk_packaged": False,
        "signing_performed": False,
        "artifact_published": False,
        "device_contacted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="run the exact compile-only Gradle task matrix",
    )
    args = parser.parse_args()
    try:
        result = run_compile_matrix(execute=args.execute)
    except (CompileMatrixError, OSError, subprocess.CalledProcessError) as error:
        print(
            json.dumps(
                {
                    "scope": "android_source_compile_only",
                    "executed": args.execute,
                    "valid": False,
                    "error": type(error).__name__,
                },
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps({**result, "valid": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
