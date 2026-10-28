"""Run bounded fork contracts using an isolated disposable instance directory."""

from pathlib import Path
from tempfile import TemporaryDirectory
from importlib.metadata import version

import os
import argparse
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
    "pytests/plugin_runtime/test_config_widgets.py",
    "pytests/plugin_runtime/test_internal_chat_capability.py",
    # v1.3.17-added behavior, not the unrelated historical locale/metadata suite.
    "pytests/prompt_test/test_prompt_i18n.py::test_outdated_custom_prompt_uses_builtin_template",
    "pytests/prompt_test/test_prompt_i18n.py::test_missing_prompt_message_includes_name_and_locale",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--include-retired-life",
        action="store_true",
        help="Also require the private pinned Life integration locally; never used by public CI",
    )
    args = parser.parse_args()
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
            NEKO_RETIRED_LIFE_TESTS="1" if args.include_retired_life else "0",
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
                *(["pytests/neko_retired/test_life_bridge.py"] if args.include_retired_life else []),
                "-q",
            ],
            cwd=ROOT,
            env=env,
        )
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
