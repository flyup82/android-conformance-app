from __future__ import annotations

import unittest

from tools.compile_source_matrix import (
    FORBIDDEN_TASK_PARTS,
    TASKS,
    VARIANTS,
    CompileMatrixError,
    compile_command,
    run_compile_matrix,
    validate_compile_command,
)


class CompileSourceMatrixTest(unittest.TestCase):
    def test_matrix_has_clean_twin_ten_singles_and_all_seeds(self) -> None:
        self.assertEqual(
            VARIANTS,
            (
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
            ),
        )
        self.assertEqual(len(TASKS), 13)
        self.assertEqual(len(set(TASKS)), 13)

    def test_every_task_is_java_compile_only(self) -> None:
        command = compile_command()
        self.assertEqual(command[:3], ("./gradlew", "--no-daemon", "--stacktrace"))
        for task in command[3:]:
            lowered = task.lower()
            self.assertTrue(task.startswith(":app:compile"))
            self.assertTrue(task.endswith("DebugJavaWithJavac"))
            self.assertFalse(
                any(part in lowered for part in FORBIDDEN_TASK_PARTS)
            )

    def test_default_is_plan_only_and_contacts_no_runner(self) -> None:
        calls: list[tuple[tuple[str, ...], bool]] = []

        def spy(command, *, check):
            calls.append((tuple(command), check))

        result = run_compile_matrix(execute=False, runner=spy)
        self.assertEqual(calls, [])
        self.assertFalse(result["executed"])
        self.assertFalse(result["apk_packaged"])
        self.assertFalse(result["signing_performed"])
        self.assertFalse(result["artifact_published"])
        self.assertFalse(result["device_contacted"])

    def test_execute_invokes_the_exact_matrix_once(self) -> None:
        calls: list[tuple[tuple[str, ...], bool]] = []

        def spy(command, *, check):
            calls.append((tuple(command), check))

        result = run_compile_matrix(execute=True, runner=spy)
        self.assertEqual(calls, [(compile_command(), True)])
        self.assertTrue(result["executed"])
        self.assertEqual(result["task_count"], 13)

    def test_package_or_device_task_is_rejected(self) -> None:
        for task in (
            ":app:assembleCleanDebug",
            ":app:packageCleanDebug",
            ":app:installCleanDebug",
            ":app:connectedCleanDebugAndroidTest",
        ):
            command = list(compile_command())
            command[-1] = task
            with self.subTest(task=task):
                with self.assertRaises(CompileMatrixError):
                    validate_compile_command(command)


if __name__ == "__main__":
    unittest.main()
