"""Actual opt-in SDK metadata and host routing boundary, no plugin/QQ IO."""

from types import SimpleNamespace

import pytest

from maibot_sdk import MaiBotPlugin, Tool
from maibot_sdk.components import collect_components
from src.plugin_runtime.component_query import ComponentQueryService


CONTRACT = "neko.tools.context.v1"


def context(session="a", group="123", anchor=None):
    return SimpleNamespace(
        stream_id=session,
        session_id=session,
        platform="qq",
        group_id=group,
        user_id="",
        metadata={"anchor_message": anchor} if anchor else {},
    )


def payload(arguments, ctx, *, contract=CONTRACT, method="plugin.invoke_tool"):
    return ComponentQueryService._build_tool_invocation_payload(
        SimpleNamespace(invoke_method=method, metadata={"trusted_context": contract}),
        SimpleNamespace(arguments=arguments, stream_id="a", reasoning=""),
        ctx,
    )


def test_real_sdk_keeps_opt_in_metadata_out_of_model_parameters():
    class Consumer(MaiBotPlugin):
        @Tool("synthetic_files", trusted_context=CONTRACT)
        async def read(self, **kwargs):
            return kwargs

    entries = collect_components(Consumer())
    tool = next(item for item in entries if item["type"] == "TOOL")
    assert tool["metadata"]["trusted_context"] == CONTRACT
    assert "_host_context" not in tool["metadata"].get("parameters_schema", {}).get("properties", {})


def test_forged_envelope_is_always_replaced_for_opted_in_tools():
    original = {"_host_context": {"contract": CONTRACT, "session_id": "foreign"}, "file_ref": "f_synthetic"}
    result = payload(original, context())
    assert result["_host_context"] == {
        "contract": CONTRACT,
        "session_id": "a",
        "stream_id": "a",
        "platform": "qq",
        "group_id": "123",
        "user_id": "",
        "account_id": "",
    }
    assert original["_host_context"]["session_id"] == "foreign"
    assert result["file_ref"] == original["file_ref"]


@pytest.mark.parametrize("contract", ["", "unknown.v2"])
def test_other_tools_keep_existing_payload_semantics(contract):
    sentinel = {"legacy": True}
    result = payload({"_host_context": sentinel}, context(), contract=contract)
    assert result["_host_context"] is sentinel


def test_no_context_does_not_turn_model_identity_into_trusted_identity():
    assert payload({"_host_context": {"session_id": "foreign"}}, None)["_host_context"] == {}


def test_focus_target_does_not_borrow_foreign_anchor_identity():
    anchor = SimpleNamespace(
        session_id="a",
        account_id="789",
        message_info=SimpleNamespace(
            group_info=SimpleNamespace(group_id="123"), user_info=SimpleNamespace(user_id="456")
        ),
    )
    target = payload({}, context("b", "987", anchor))["_host_context"]
    assert target["session_id"] == "b" and target["group_id"] == "987"
    assert target["account_id"] == "" and target["user_id"] == ""
    matched = payload({}, context("a", "123", anchor))["_host_context"]
    assert matched["account_id"] == "789" and matched["user_id"] == "456"
