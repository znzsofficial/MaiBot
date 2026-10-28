"""Public pinned TTS consumer against actual host receipts and Focus payloads."""

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import importlib.util
import os
import subprocess
import sys

import pytest
import neko_pytest_guard  # noqa: F401 -- deny model/QQ network in standalone runs

from src.core.tooling import ToolSpec
from src.llm_models.payload_content.context_item import ContextItemBuilder, RoleType
from src.llm_models.payload_content.context_snapshot import serialize_context_item_snapshot
from src.maisaka.builtin_tool import reply
from src.maisaka.context.planner_messages import build_planner_prefix
from src.maisaka.focus.tools import routed_schema


TTS_PIN = "7be09dec956fbae6a8600eef5df14cf116e18d57"


def load(name, filename):
    root = Path(os.environ["NEKO_PLUGIN_FIXTURES"]) / "neko-tts"
    path = root / filename
    expected = subprocess.check_output(["git", "show", TTS_PIN + ":" + filename], cwd=root)
    assert path.read_bytes().replace(b"\r\n", b"\n") == expected.replace(b"\r\n", b"\n")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("success", [False, True], ids=["unknown", "confirmed"])
async def test_actual_host_receipt_drives_tts_once(success):
    deferred = load("neko_bridge_tts", "deferred_speech.py").DeferredSpeech()
    assert deferred.register("synthetic-a", "reply-a", "call-a", [(0, "planned")])
    voices = []

    async def consume(name, **kwargs):
        assert name == "maisaka.reply.after_send"
        args = [kwargs[key] for key in ("session_id", "reply_id", "call_id", "send_results")]
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
    assert deferred.claim("foreign", "reply-a", "call-a", results) == []
    await reply._notify_reply_delivery(context, execution, results)
    await reply._notify_reply_delivery(context, execution, results)
    assert voices == ([(0, "actual sent text")] if success else [])


def test_actual_host_focus_snapshot_is_understood_by_pinned_tts():
    tts = load("neko_bridge_tts_focus", "focus_scope.py")
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
            .build(),
        )
        for scope in scopes
    ]
    assert tts.planner_scopes("", definitions) == tuple(scopes)
    assert [item["parts"][0]["text"] for item in items] == [
        build_planner_prefix(
            timestamp=datetime(2026, 10, 24),
            user_name="synthetic",
            message_id="message",
            chat_id=scope,
            include_chat_id=True,
        )
        for scope in scopes
    ]
