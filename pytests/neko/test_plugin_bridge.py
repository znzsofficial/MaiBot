"""Pinned public plugin consumers against actual host receipts and Focus payloads."""

from datetime import datetime
from pathlib import Path
from types import ModuleType, SimpleNamespace

import importlib
import importlib.util
import os
import sqlite3
import subprocess
import sys

import pytest
import neko_pytest_guard  # noqa: F401 -- install the network guard for standalone runs

from src.core.tooling import ToolSpec
from src.llm_models.payload_content.context_item import ContextItemBuilder, RoleType
from src.llm_models.payload_content.context_snapshot import serialize_context_item_snapshot
from src.maisaka.builtin_tool import reply
from src.maisaka.context.planner_messages import build_planner_prefix
from src.maisaka.focus.tools import routed_schema


PINS = {"neko-life": "f6116cfc76943c9bd6b78b47d309478645908a75", "neko-tts": "7be09dec956fbae6a8600eef5df14cf116e18d57"}


def pinned_file(repository, name):
    root = Path(os.environ["NEKO_PLUGIN_FIXTURES"]) / repository
    path = root / name
    expected = subprocess.check_output(["git", "show", PINS[repository] + ":" + name], cwd=root)
    assert path.read_bytes().replace(b"\r\n", b"\n") == expected.replace(b"\r\n", b"\n")
    return path


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("success", [False, True], ids=["unknown", "confirmed"])
async def test_actual_host_receipt_drives_life_and_tts_once(success):
    deferred = load("neko_bridge_tts", pinned_file("neko-tts", "deferred_speech.py")).DeferredSpeech()
    store_path = pinned_file("neko-life", "neko_life/store.py")
    pinned_file("neko-life", "neko_life/materials.py")
    package = ModuleType("neko_bridge_life")
    package.__path__ = [str(store_path.parent)]
    sys.modules[package.__name__] = package
    Store = importlib.import_module("neko_bridge_life.store").Store
    # Only the settlement boundary needs these synthetic tables; no worker/host startup.
    with sqlite3.connect(":memory:") as connection:
        connection.row_factory = sqlite3.Row
        connection.executescript("""
            CREATE TABLE receipts(id TEXT,persona TEXT,status TEXT);
            CREATE TABLE share_executions(receipt TEXT,session TEXT,reply_id TEXT,call_id TEXT,stage TEXT,expected INTEGER);
            CREATE TABLE share_offers(receipt TEXT,activity REAL);
            INSERT INTO receipts VALUES('receipt','persona','adopted');
            INSERT INTO share_executions VALUES('receipt','synthetic-a','reply-a','call-a','sending',1);
            INSERT INTO share_offers VALUES('receipt',0);
        """)
        store = SimpleNamespace(conn=connection, clock=lambda: 100)
        assert deferred.register("synthetic-a", "reply-a", "call-a", [(0, "planned")])
        voices = []

        async def consume(name, **kwargs):
            assert name == "maisaka.reply.after_send"
            args = [kwargs[key] for key in ("session_id", "reply_id", "call_id", "send_results")]
            Store._share_delivery(store, "persona", *args)
            voices.extend(deferred.claim(*args))

        context = SimpleNamespace(
            runtime=SimpleNamespace(session_id="synthetic-a"),
            get_runtime_manager=lambda: SimpleNamespace(invoke_hook=consume),
        )
        execution = SimpleNamespace(targets=[True], reply_id="reply-a", call_id="call-a")
        results = [
            {
                "index": 0,
                "success": success,
                "message_id": "platform-a" if success else "",
                "speech_text": "actual sent text",
            }
        ]
        # Wrong identity cannot settle another session's execution.
        Store._share_delivery(store, "persona", "foreign", "reply-a", "call-a", results)
        assert connection.execute("SELECT status FROM receipts").fetchone()[0] == "adopted"
        await reply._notify_reply_delivery(context, execution, results)
        await reply._notify_reply_delivery(context, execution, results)
        assert connection.execute("SELECT status FROM receipts").fetchone()[0] == ("sent" if success else "unknown")
        assert voices == ([(0, "actual sent text")] if success else [])


def test_actual_host_focus_snapshot_is_understood_by_pinned_plugins():
    life = load("neko_bridge_life_focus", pinned_file("neko-life", "neko_life/focus.py"))
    tts = load("neko_bridge_tts_focus", pinned_file("neko-tts", "focus_scope.py"))
    scopes = ["qq:group:synthetic-a", "qq:group:synthetic-b"]
    schema = routed_schema(
        ToolSpec(
            name="reply",
            description="synthetic",
            parameters_schema={"type": "object", "properties": {}},
            provider_name="synthetic",
            provider_type="builtin",
        ),
        scopes[0],
    )
    schema["properties"]["session_id"]["enum"] = scopes
    definitions = [{"type": "function", "function": {"name": "reply", "parameters": schema}}]
    items = [
        serialize_context_item_snapshot(
            ContextItemBuilder()
            .set_role(RoleType.User)
            .add_text_content(
                build_planner_prefix(
                    timestamp=datetime(2026, 10, 24),
                    user_name="synthetic",
                    message_id="message",
                    chat_id=scope,
                    include_chat_id=True,
                )
            )
            .add_text_content("synthetic message")
            .build()
        )
        for scope in scopes
    ]
    assert life.planner_scopes("", definitions) == tuple(scopes)
    assert tts.planner_scopes("", definitions) == tuple(scopes)
    assert life.items_for_scope(items, scopes[0]) == [items[0]]
