"""Small release deltas: monitor reasoning and adapter metadata, never real IO."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from src.maisaka.monitor.events import _serialize_planner_block
from src.platform_io import DriverKind
from src.platform_io.types import RouteKey
from src.plugin_runtime.host.supervisor import PluginRunnerSupervisor
from src.services.telemetry_platform_service import collect_telemetry_adapters


def test_monitor_keeps_reasoning_only_result():
    result = _serialize_planner_block(None, None, None, None, None, None, None, reasoning="synthetic reasoning")
    assert result["reasoning"] == "synthetic reasoning"


def test_telemetry_collects_only_deduplicated_platform_and_protocol(monkeypatch):
    def driver(kind, plugin_type="adapter", protocol="napcat"):
        return SimpleNamespace(
            descriptor=SimpleNamespace(
                kind=kind,
                platform="qq",
                account_id="must-not-be-exported",
                metadata={"plugin_type": plugin_type, "protocol": protocol, "scope": "private-scope"},
            )
        )

    drivers = [
        driver(DriverKind.LOCAL),
        driver(DriverKind.PLUGIN, plugin_type="plugin"),
        driver(DriverKind.PLUGIN),
        driver(DriverKind.PLUGIN),
        driver(DriverKind.PLUGIN, protocol="snowluma"),
    ]
    manager = SimpleNamespace(driver_registry=SimpleNamespace(list=lambda: drivers))
    monkeypatch.setattr("src.services.telemetry_platform_service.get_platform_io_manager", lambda: manager)
    assert collect_telemetry_adapters() == [
        {"platform": "qq", "protocol": "napcat"},
        {"platform": "qq", "protocol": "snowluma"},
    ]


@pytest.mark.parametrize("protocol", [None, "napcat", ""])
@pytest.mark.asyncio
async def test_runtime_protocol_overrides_static_metadata_without_changing_route(monkeypatch, protocol):
    supervisor = object.__new__(PluginRunnerSupervisor)
    supervisor._registered_plugins = {"adapter": SimpleNamespace(plugin_type="adapter")}
    supervisor._unregister_message_gateway_driver = AsyncMock()
    manager = SimpleNamespace(
        is_started=False, register_driver=Mock(), bind_send_route=Mock(), bind_receive_route=Mock()
    )
    monkeypatch.setattr("src.plugin_runtime.host.supervisor.get_platform_io_manager", lambda: manager)
    gateway = SimpleNamespace(
        name="gateway",
        supports_send=True,
        supports_receive=True,
        route_type="exact",
        protocol="static-protocol",
        metadata={"protocol": "untrusted-static-metadata"},
    )
    route = RouteKey("qq", "synthetic-bot", "synthetic-connection")
    await supervisor._register_message_gateway_driver("adapter", gateway, route, protocol=protocol)
    expected = "static-protocol" if protocol is None else protocol
    assert manager.register_driver.call_args.args[0].descriptor.metadata["protocol"] == expected
    for callback in (manager.bind_send_route, manager.bind_receive_route):
        binding = callback.call_args.args[0]
        assert binding.route_key == route
        assert binding.metadata["protocol"] == expected
