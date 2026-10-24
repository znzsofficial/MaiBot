"""Run bounded fork contracts using an isolated disposable instance directory."""

from pathlib import Path
from tempfile import TemporaryDirectory
from importlib.metadata import version

import os
import json
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
TESTS = (
    "pytests/neko",
    "pytests/maisaka/test_context_compaction.py",
    "pytests/maisaka/test_focus_group_runtime.py",
    "pytests/maisaka/test_replyer_expression_selection.py",
    "pytests/maisaka/test_planner_text_reply.py",
    "pytests/plugin_runtime/test_reply_extension_platform_scope.py",
)


def main():
    manifest = json.loads((ROOT / "neko-patches.json").read_text(encoding="utf-8"))
    for package, expected in manifest["runtime_packages"].items():
        if version(package) != expected:
            raise RuntimeError("Unexpected runtime package: " + package)
    with TemporaryDirectory(prefix="maibot-neko-tests-") as temporary:
        env = dict(
            os.environ,
            MAIBOT_INSTANCE_DIR=temporary,
            MAIBOT_LOCALE="zh-CN",
            PYTHONPATH=str(ROOT / "scripts") + os.pathsep + str(ROOT),
            PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
            PYTHONIOENCODING="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-p",
                "neko_pytest_guard",
                "-p",
                "pytest_asyncio.plugin",
                "-o",
                "asyncio_mode=auto",
                *TESTS,
                "-q",
            ],
            cwd=ROOT,
            env=env,
        )
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
