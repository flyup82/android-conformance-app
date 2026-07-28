#!/usr/bin/env python3
"""Compile and run the pure-Java seed behavior tests without Android tooling."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = Path("io/github/flyup82/androidconformance")
SOURCE = ROOT / "app/src/main/java" / PACKAGE / "SeedBehavior.java"
TEST = ROOT / "app/src/test/java" / PACKAGE / "SeedBehaviorSelfTest.java"


def main() -> int:
    javac = shutil.which("javac")
    java = shutil.which("java")
    if javac is None or java is None:
        print("behavior_unit_unavailable: JDK 17 java/javac required", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="android-conformance-java-") as temp:
        output = Path(temp) / "classes"
        output.mkdir()
        subprocess.run(
            [
                javac,
                "--release",
                "17",
                "-d",
                str(output),
                str(SOURCE),
                str(TEST),
            ],
            check=True,
        )
        subprocess.run(
            [
                java,
                "-ea",
                "-cp",
                str(output),
                "io.github.flyup82.androidconformance.SeedBehaviorSelfTest",
            ],
            check=True,
        )
    print("behavior_unit_valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
