from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from kitty_markdown_viewer.config import ensure_defaults, load_config


class ConfigTests(unittest.TestCase):
    def test_config_and_themes_created_silently(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config_path = root / "config.toml"
            config = load_config(config_path)
            self.assertTrue(config_path.exists())
            self.assertTrue((root / "themes" / "dark.toml").exists())
            self.assertTrue((root / "themes" / "light.toml").exists())
            self.assertEqual(config.schema, "detect")
            self.assertTrue(config.pager)
            self.assertEqual(config.pager_command, "less -r")

    def test_init_config_refuses_to_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            config_path = Path(temp) / "config.toml"
            ensure_defaults(config_path)
            with self.assertRaises(FileExistsError):
                ensure_defaults(config_path, refuse_existing=True)


if __name__ == "__main__":
    unittest.main()
