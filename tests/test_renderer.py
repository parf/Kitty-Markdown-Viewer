from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from kitty_markdown_viewer.config import load_config
from kitty_markdown_viewer.renderer import MarkdownRenderer, Source
from kitty_markdown_viewer.themes import resolve_theme


def make_renderer(root: Path, width: int = 60) -> MarkdownRenderer:
    config = load_config(root / "config.toml")
    theme = resolve_theme(config, "dark")
    return MarkdownRenderer(config, theme, width=width)


class RendererTests(unittest.TestCase):
    def test_large_headings_and_h3_separator(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp)).render("# Big\n\n### Small")
        self.assertIn("\x1b]66;s=4;Big\x07", output)
        self.assertIn("\x1b]66;s=2;Small\x07", output)
        self.assertIn("━", output)

    def test_markdown_link_is_label_only_clickable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp)).render("[Realmo](https://realmo.com)")
        self.assertIn("\x1b]8;;https://realmo.com\x1b\\", output)
        self.assertIn("Realmo", output)
        self.assertNotIn("https://realmo.com\x1b\\Realmo", output)

    def test_bare_links_are_clickable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp)).render("https://example.com ftp://host mailto:a@b.com")
        self.assertIn("\x1b]8;;https://example.com\x1b\\", output)
        self.assertIn("\x1b]8;;ftp://host\x1b\\", output)
        self.assertIn("\x1b]8;;mailto:a@b.com\x1b\\", output)

    def test_unicode_table_wraps_cells(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp), width=32).render("| A | B |\n|---|---|\n| one two three four five | [x](https://x.test) |\n")
        self.assertIn("┌", output)
        self.assertIn("┼", output)
        self.assertIn("\x1b]8;;https://x.test\x1b\\", output)
        self.assertIn("one two", output)

    def test_html_br_and_raw_html(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp)).render("a<br>b <b>raw</b>")
        self.assertIn("a\nb", output)
        self.assertIn("<b>raw</b>", output)

    def test_relative_link_resolves_from_source_url(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp)).render("[Doc](next.md)", source=Source(url="https://example.com/docs/readme.md"))
        self.assertIn("\x1b]8;;https://example.com/docs/next.md\x1b\\", output)

    def test_image_uses_icat_with_width_cap_and_alt_caption(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            image = root / "image.png"
            image.write_bytes(b"not really png")
            config = load_config(root / "config.toml")
            config = replace(config, image_max_width=100, image_max_height=7)
            theme = resolve_theme(config, "dark")
            renderer = MarkdownRenderer(config, theme, width=40)
            completed = mock.Mock(returncode=0, stdout="<image>", stderr="")
            with mock.patch("kitty_markdown_viewer.renderer.subprocess.run", return_value=completed) as run:
                output = renderer.render("![Alt text](image.png)", source=Source(path=root / "doc.md"))
        command = run.call_args.args[0]
        self.assertIn("--place", command)
        self.assertIn("40x7@0x0", command)
        self.assertIn("<image>", output)
        self.assertIn("Alt text", output)


if __name__ == "__main__":
    unittest.main()
