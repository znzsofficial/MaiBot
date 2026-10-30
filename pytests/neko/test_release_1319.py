"""Preserve explicit pre-release settings through the real config serializer."""

from copy import deepcopy

import tomlkit

from src.config.config import CONFIG_VERSION, Config, load_config_from_file, write_config_to_file


def test_1319_config_copy_keeps_existing_values_and_only_adds_empty_profiles(tmp_path):
    config = Config()
    config.personality.personality = "synthetic unchanged persona"
    config.personality.behavior_style = "synthetic unchanged behavior"
    config.personality.reply_style = "synthetic unchanged reply"
    config.chat.reply_style.group_chat_prompt = "synthetic group prompt"
    config.chat.reply_style.private_chat_prompts = "synthetic private prompt"
    config.chat.max_context_size = 37
    config.chat.max_private_context_size = 61
    config.experimental.focus_mode = True
    config.experimental.focus_on_private = False
    config.experimental.group_attention_drift.enabled = False
    config.experimental.private_attention_drift.enabled = True
    config.capabilities.files = False
    path = tmp_path / "bot_config.toml"
    write_config_to_file(config, path, "8.15.63")
    old = tomlkit.parse(path.read_text(encoding="utf-8")).unwrap()
    # These fields did not exist in 1.3.18; simulate a real old copy, not new defaults.
    del old["personality"]["profiles"]
    del old["personality"]["selected_profile"]
    path.write_text(tomlkit.dumps(old), encoding="utf-8")
    original = deepcopy(old)
    migrated, updated = load_config_from_file(Config, path, CONFIG_VERSION)
    assert updated and CONFIG_VERSION == "8.15.68"
    expected = deepcopy(original)
    expected["inner"]["version"] = CONFIG_VERSION
    expected["personality"].update(profiles=[], selected_profile="")
    assert tomlkit.parse(path.read_text(encoding="utf-8")).unwrap() == expected
    assert migrated.chat.max_context_size == 37
    assert migrated.chat.max_private_context_size == 61
    assert not migrated.desktop_pet.enabled
    assert not migrated.desktop_pet.chat_tools_enabled
    _, again_updated = load_config_from_file(Config, path, CONFIG_VERSION)
    assert not again_updated
    assert tomlkit.parse(path.read_text(encoding="utf-8")).unwrap() == expected
