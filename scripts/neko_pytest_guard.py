"""Explicit pytest result gate; deny network except Windows' stdlib socketpair."""

from pathlib import Path

import ipaddress
import sys


_collected = set()
_completed = set()
_skipped = []
REQUIRED = {
    "pytests/neko/test_reply_contracts.py",
    "pytests/neko/test_life_compaction.py",
    "pytests/neko/test_source_policy.py",
    "pytests/neko/test_plugin_bridge.py",
    "pytests/maisaka/test_context_compaction.py",
    "pytests/maisaka/test_focus_group_runtime.py",
    "pytests/maisaka/test_replyer_expression_selection.py",
    "pytests/maisaka/test_planner_text_reply.py",
    "pytests/plugin_runtime/test_reply_extension_platform_scope.py",
}


def _network_guard(event, args):
    if event != "socket.connect":
        return
    address = args[1]
    if isinstance(address, tuple):
        try:
            caller = sys._getframe(1)
            if (
                ipaddress.ip_address(address[0]).is_loopback
                and caller.f_code.co_name == "_fallback_socketpair"
                and caller.f_globals.get("__name__") == "socket"
                and caller.f_locals.get("csock") is args[0]
                and address == (caller.f_locals.get("addr"), caller.f_locals.get("port"))
            ):
                return
        except ValueError:
            pass
    raise RuntimeError("External network disabled in synthetic fork tests")


# Windows asyncio uses an internal loopback socket pair; allow it, not suppliers.
sys.addaudithook(_network_guard)


def pytest_collection_finish(session):
    _collected.update(item.nodeid for item in session.items)


def pytest_runtest_logreport(report):
    if report.skipped:
        _skipped.append(report.nodeid)
    if report.when == "call" and report.passed:
        _completed.add(report.nodeid)


def contracts_complete(collected, completed, skipped):
    paths = {identity.split("::", 1)[0] for identity in completed}
    return bool(collected and not skipped and REQUIRED <= paths and completed == collected)


def pytest_sessionfinish(session, exitstatus):
    if not contracts_complete(_collected, _completed, _skipped):
        session.exitstatus = 1
        print("Fork contract gate failed: missing group, incomplete execution or unexpected skip", file=sys.stderr)


def pytest_report_header():
    from importlib.metadata import version
    import maibot_sdk

    return f"Real SDK {version('maibot-plugin-sdk')} at {Path(maibot_sdk.__file__).name}; synthetic instance only"
