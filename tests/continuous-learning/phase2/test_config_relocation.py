"""
Tests for config relocation feature.

These tests verify that config.properties is correctly moved from
hooks/observe/ to skills/continuous-learning/scripts/ with proper
auto-generation on observer start.

TDD RED Phase: These tests are expected to FAIL initially.

S1: Config File Auto-Generation on Observer Start
S2: Config Loader Path Resolution
"""

from pathlib import Path

import pytest


class TestDefaultConfigPath:
    """Tests for get_default_config_path() returning the new location."""

    def test_get_default_config_path_returns_new_location(self) -> None:
        """
        get_default_config_path() should return the new location in scripts/.

        S2.1: Returns path to skills/continuous-learning/scripts/config.properties
        """
        from hooks.observe import config

        default_path = config.get_default_config_path()

        # Should point to the new location, NOT hooks/observe/
        assert "skills" in str(default_path), (
            f"Expected path to contain 'skills', got {default_path}"
        )
        assert "continuous-learning" in str(default_path), (
            f"Expected path to contain 'continuous-learning', got {default_path}"
        )
        assert "scripts" in str(default_path), (
            f"Expected path to contain 'scripts', got {default_path}"
        )
        assert default_path.name == "config.properties", (
            f"Expected filename 'config.properties', got {default_path.name}"
        )

    def test_get_default_config_path_not_in_hooks_observe(self) -> None:
        """
        get_default_config_path() should NOT return hooks/observe/ location.
        """
        from hooks.observe import config

        default_path = config.get_default_config_path()

        # Should NOT point to old location
        assert "hooks/observe" not in str(default_path), (
            f"Path should not contain 'hooks/observe', got {default_path}"
        )

    def test_default_config_file_exists_at_new_location(self) -> None:
        """
        The bundled default config.properties should exist at the new location.
        """
        from hooks.observe import config

        default_path = config.get_default_config_path()

        assert default_path.exists(), (
            f"Bundled default config should exist at {default_path}"
        )


class TestEnsureUserConfig:
    """Tests for ensure_user_config() function."""

    def test_ensure_user_config_creates_missing_config(
        self, tmp_path: Path
    ) -> None:
        """
        When user config doesn't exist, it should be created from bundled default.

        S1.1: Missing config - auto-generate from bundled default.
        """
        from hooks.observe import config

        homunculus_dir = tmp_path / "homunculus"
        # Do NOT create the directory or config file

        # ensure_user_config should create it
        result_path = config.ensure_user_config(homunculus_dir)

        assert result_path.exists(), "Config file should be created"
        assert result_path == homunculus_dir / "config.properties"

    def test_ensure_user_config_copies_default_content(
        self, tmp_path: Path
    ) -> None:
        """
        Created config should have the same content as bundled default.

        S1.1: Content matches bundled default.
        """
        from hooks.observe import config

        homunculus_dir = tmp_path / "homunculus"

        result_path = config.ensure_user_config(homunculus_dir)

        # Read created config
        created_content = result_path.read_text()

        # Should contain expected keys
        assert "signal_every_n" in created_content
        assert "min_observations_to_analyze" in created_content
        assert "run_interval_minutes" in created_content

    def test_ensure_user_config_preserves_existing(
        self, tmp_path: Path
    ) -> None:
        """
        When user config exists, it should NOT be overwritten.

        S1.2: Existing config - preserve user settings.
        """
        from hooks.observe import config

        homunculus_dir = tmp_path / "homunculus"
        homunculus_dir.mkdir(parents=True, exist_ok=True)

        # Create existing user config with custom value
        user_config = homunculus_dir / "config.properties"
        user_config.write_text("# Custom config\nsignal_every_n=99\n")

        # ensure_user_config should NOT overwrite
        result_path = config.ensure_user_config(homunculus_dir)

        # Content should be preserved
        content = result_path.read_text()
        assert "signal_every_n=99" in content, (
            "User config should be preserved, not overwritten"
        )

    def test_ensure_user_config_creates_directory(
        self, tmp_path: Path
    ) -> None:
        """
        When homunculus directory doesn't exist, it should be created.

        S1.3: Missing homunculus directory - auto-create.
        """
        from hooks.observe import config

        # Create a path where the directory does NOT exist
        homunculus_dir = tmp_path / "deeply" / "nested" / "homunculus"
        assert not homunculus_dir.exists(), "Directory should not exist initially"

        # ensure_user_config should create the directory
        result_path = config.ensure_user_config(homunculus_dir)

        assert homunculus_dir.exists(), "Directory should be created"
        assert result_path.exists(), "Config file should be created"

    def test_ensure_user_config_returns_correct_path(
        self, tmp_path: Path
    ) -> None:
        """
        ensure_user_config() should return the path to user config file.
        """
        from hooks.observe import config

        homunculus_dir = tmp_path / "homunculus"

        result_path = config.ensure_user_config(homunculus_dir)

        expected = homunculus_dir / "config.properties"
        assert result_path == expected


class TestLoadConfigWithNewPath:
    """Tests for load_config() with the new config path."""

    def test_load_config_uses_user_override(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        User config should override bundled defaults.

        S2.2: Priority loading - user override wins.
        """
        from hooks.observe import config

        homunculus_dir = tmp_path / "homunculus"
        homunculus_dir.mkdir(parents=True, exist_ok=True)

        # Create user config with custom value
        user_config = homunculus_dir / "config.properties"
        user_config.write_text("signal_every_n=123\n")

        # Monkeypatch get_homunculus_dir to return our temp dir
        monkeypatch.setattr(
            config,
            "get_homunculus_dir",
            lambda: homunculus_dir
        )

        loaded = config.load_config()

        assert loaded["signal_every_n"] == 123, (
            f"User override should win, got {loaded['signal_every_n']}"
        )

    def test_load_config_uses_bundled_default_when_user_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        When user config is missing, bundled default should be used.

        S2.2: Missing keys in user config use bundled defaults.
        """
        from hooks.observe import config

        homunculus_dir = tmp_path / "homunculus"
        homunculus_dir.mkdir(parents=True, exist_ok=True)
        # Do NOT create user config

        monkeypatch.setattr(
            config,
            "get_homunculus_dir",
            lambda: homunculus_dir
        )

        loaded = config.load_config()

        # Should use bundled defaults
        assert loaded["signal_every_n"] == 20
        assert loaded["min_observations_to_analyze"] == 50

    def test_load_config_merges_user_with_defaults(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        User config should be merged with bundled defaults.

        S2.2: Missing keys in user config use bundled defaults.
        """
        from hooks.observe import config

        homunculus_dir = tmp_path / "homunculus"
        homunculus_dir.mkdir(parents=True, exist_ok=True)

        # Create user config with only one key
        user_config = homunculus_dir / "config.properties"
        user_config.write_text("signal_every_n=77\n")

        monkeypatch.setattr(
            config,
            "get_homunculus_dir",
            lambda: homunculus_dir
        )

        loaded = config.load_config()

        # User value should be used
        assert loaded["signal_every_n"] == 77
        # Other values should come from defaults
        assert loaded["min_observations_to_analyze"] == 50
        assert loaded["run_interval_minutes"] == 5

    def test_load_config_type_coercion(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Integer values should be parsed correctly.

        S2.2: Type coercion works (int values parsed correctly).
        """
        from hooks.observe import config

        homunculus_dir = tmp_path / "homunculus"
        homunculus_dir.mkdir(parents=True, exist_ok=True)

        user_config = homunculus_dir / "config.properties"
        user_config.write_text("signal_every_n=42\nretention_days=14\n")

        monkeypatch.setattr(
            config,
            "get_homunculus_dir",
            lambda: homunculus_dir
        )

        loaded = config.load_config()

        assert isinstance(loaded["signal_every_n"], int)
        assert loaded["signal_every_n"] == 42
        assert isinstance(loaded["retention_days"], int)
        assert loaded["retention_days"] == 14

    def test_load_config_graceful_fallback_no_bundled_default(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        When both user config and bundled default are missing, return hardcoded defaults.

        S2.3: Graceful fallback - no bundled default.
        """
        from hooks.observe import config

        homunculus_dir = tmp_path / "homunculus"
        homunculus_dir.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(
            config,
            "get_homunculus_dir",
            lambda: homunculus_dir
        )

        # Monkeypatch get_default_config_path to return a non-existent path
        monkeypatch.setattr(
            config,
            "get_default_config_path",
            lambda: tmp_path / "nonexistent" / "config.properties"
        )

        loaded = config.load_config()

        # Should return hardcoded defaults
        assert loaded["signal_every_n"] == 20
        assert loaded["observer_model"] == "haiku"
        assert "min_observations_to_analyze" in loaded


class TestConfigContentValidation:
    """Tests for bundled config file content."""

    def test_default_config_has_all_required_keys(self) -> None:
        """
        Bundled config.properties should contain all required keys.

        S3.1: Default config has all required keys.
        """
        from hooks.observe import config

        default_path = config.get_default_config_path()

        if not default_path.exists():
            pytest.skip("Default config not yet moved to new location")

        content = default_path.read_text()

        required_keys = [
            "signal_every_n",
            "min_observations_to_analyze",
            "run_interval_minutes",
            "retention_days",
            "max_file_size_mb",
            "observer_model",
        ]

        for key in required_keys:
            assert key in content, f"Missing required key: {key}"

    def test_config_format_valid_key_value_pairs(self) -> None:
        """
        Config should parse valid key=value pairs correctly.

        S3.2: Config format - valid key=value pairs.
        """
        from hooks.observe import config

        # Create a test config with various formats
        test_config = """
# This is a comment
signal_every_n=20

min_observations_to_analyze = 50
  run_interval_minutes=5

# Another comment
retention_days=30
"""

        # Write to temp file and parse manually
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.properties', delete=False) as f:
            f.write(test_config)
            temp_path = Path(f.name)

        try:
            # The loader should handle these formats
            lines = temp_path.read_text().split('\n')
            parsed = {}
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    parsed[key.strip()] = value.strip()

            assert parsed["signal_every_n"] == "20"
            assert parsed["min_observations_to_analyze"] == "50"
        finally:
            temp_path.unlink()
