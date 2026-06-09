from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from kitty_markdown_viewer.config import load_config
from kitty_markdown_viewer.renderer import MarkdownRenderer, Source, strip_escape_sequences
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

    def test_heading_levels_four_five_six_have_distinct_styles(self) -> None:
        markdown = "#### Heading Level 4\n\n##### Heading Level 5\n\n###### Heading Level 6\n"
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp)).render(markdown)
        self.assertIn("\x1b]66;s=2:n=2:d=3;Heading Level 4\x07", output)
        self.assertIn("\x1b[1m\x1b[58;2;215;175;255m\x1b[4:1mHeading Level 5", output)
        self.assertIn("\x1b[1mHeading Level 6", output)

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

    def test_dates_are_colored(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp)).render("Ship date: 2026-03-10")
        self.assertIn("\x1b[38;2;255;175;95m2026-03-10\x1b[0m", output)

    def test_paths_are_colored(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp)).render("Config: ~/.config/cat-md/config.toml and /home/parf/bin/cat-md")
        self.assertIn("\x1b[38;2;215;175;255m~/.config/cat-md/config.toml\x1b[0m", output)
        self.assertIn("\x1b[38;2;215;175;255m/home/parf/bin/cat-md\x1b[0m", output)

    def test_paths_are_colored_in_generic_code_blocks(self) -> None:
        markdown = "```\n~/.config/cat-md/themes/dark.toml\n/home/parf/bin/cat-md\n```"
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp), width=100).render(markdown)
        self.assertIn("\x1b[38;2;215;175;255m~/.config/cat-md/themes/dark.toml\x1b[0m", output)
        self.assertIn("\x1b[38;2;215;175;255m/home/parf/bin/cat-md\x1b[0m", output)

    def test_large_numbers_style_groups(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp)).render("Values: 108 1204 48217 309884 1204928")
        self.assertIn("108", output)
        self.assertIn("1\x1b[38;2;156;163;175m204\x1b[0m", output)
        self.assertIn("48\x1b[38;2;156;163;175m217\x1b[0m", output)
        self.assertIn("309\x1b[38;2;156;163;175m884\x1b[0m", output)
        self.assertIn("\x1b[38;2;255;215;95m\x1b[1m1\x1b[0m204\x1b[38;2;156;163;175m928\x1b[0m", output)

    def test_unicode_table_wraps_cells(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp), width=32).render("| A | B |\n|---|---|\n| one two three four five | [x](https://x.test) |\n")
        self.assertIn("┌", output)
        self.assertIn("┼", output)
        self.assertIn("\x1b]8;;https://x.test\x1b\\", output)
        self.assertIn("one two", output)

    def test_ordered_list_preserves_start_value(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp)).render("4. hydrate renderer\n5. ship demo\n")
        self.assertIn("4. hydrate renderer", output)
        self.assertIn("5. ship demo", output)

    def test_definition_list_renders_term_and_definition(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp)).render("Renderer\n: terminal-first Markdown display\n")
        self.assertIn("Renderer", output)
        self.assertIn("→", output)
        self.assertIn("terminal-first Markdown display", output)

    def test_footnotes_render_refs_and_section(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp)).render("Useful detail[^note].\n\n[^note]: rendered at the bottom\n")
        self.assertIn("Useful detail", output)
        self.assertIn("¹", output)
        self.assertIn("rendered at the bottom", output)

    def test_front_matter_renders_as_metadata_block(self) -> None:
        markdown = "---\ntitle: Demo\ndate: 2026-06-08\n---\n\n# Hello\n"
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp)).render(markdown)
        self.assertIn("title", output)
        self.assertIn("Demo", output)
        self.assertIn("\x1b]66;s=4;Hello\x07", output)

    def test_code_block_box_uses_needed_width(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp), width=100).render("```\n# Build and run\ncargo build\ncargo run -- DEMO.md\n```")
        top = next(line for line in output.splitlines() if "┌" in line)
        self.assertLess(len(strip_escape_sequences(top)), 40)
        self.assertIn("cargo run -- DEMO.md", output)

    def test_code_block_highlights_diff_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp), width=100).render("```\n- status: pending\n+ status: shipped\n```")
        self.assertIn("\x1b[48;2;58;16;16m- status: pending", output)
        self.assertIn("\x1b[48;2;16;58;26m+ status: shipped", output)

    def test_code_block_highlights_json_strings_keys_and_numbers(self) -> None:
        markdown = '```json\n{\n  "name": "catmd-demo",\n  "version": "1.0.0",\n  "count": 12,\n  "enabled": true\n}\n```'
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp), width=100).render(markdown)
        self.assertIn('\x1b[38;2;95;215;255m"name"', output)
        self.assertIn('\x1b[38;2;255;215;95m"catmd-demo"', output)
        self.assertIn('\x1b[38;2;215;175;255m12', output)
        self.assertIn('\x1b[38;2;135;255;175mtrue', output)

    def test_code_block_highlights_comments_grey(self) -> None:
        markdown = "```\n# Build and run\nvalue = 1 // inline\n/* block */\n```"
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp), width=100).render(markdown)
        self.assertIn('\x1b[38;2;156;163;175m# Build and run', output)
        self.assertIn('\x1b[38;2;156;163;175m// inline', output)
        self.assertIn('\x1b[38;2;156;163;175m/* block */', output)

    def test_code_block_highlights_rust(self) -> None:
        markdown = '```rust\nfn summarize(name: &str, tasks_done: usize) -> String {\n    format!("{name} completed {tasks_done} tasks")\n}\n\nfn main() {\n    println!("{}", summarize("Avery", 7));\n}\n```'
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp), width=100).render(markdown)
        self.assertIn('\x1b[38;2;255;95;135mfn', output)
        self.assertIn('\x1b[38;2;95;215;255msummarize', output)
        self.assertIn('\x1b[38;2;215;175;255musize', output)
        self.assertIn('\x1b[38;2;135;255;175mformat!', output)
        self.assertIn('\x1b[38;2;255;215;95m"Avery"', output)
        self.assertIn('\x1b[38;2;215;175;255m7', output)

    def test_code_block_highlights_python(self) -> None:
        markdown = '```python\ndef summarize(name: str, tasks_done: int) -> str:\n    return f"{name} completed {tasks_done} tasks"\n\n\nif __name__ == "__main__":\n    print(summarize("Morgan", 7))\n```'
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp), width=100).render(markdown)
        self.assertIn('\x1b[38;2;255;95;135mdef', output)
        self.assertIn('\x1b[38;2;95;215;255msummarize', output)
        self.assertIn('\x1b[38;2;215;175;255mstr', output)
        self.assertIn('\x1b[38;2;255;95;135mreturn', output)
        self.assertIn('\x1b[38;2;135;255;175m__name__', output)
        self.assertIn('\x1b[38;2;255;215;95m"Morgan"', output)
        self.assertIn('\x1b[38;2;215;175;255m7', output)

    def test_code_block_highlights_cpp(self) -> None:
        markdown = '```cpp\nstd::string summarize(const std::string& name, int tasks_done) {\n    return name + " completed " + std::to_string(tasks_done) + " tasks";\n}\n\nint main() {\n    std::cout << summarize("Taylor", 42) << std::endl;\n}\n```'
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp), width=100).render(markdown)
        self.assertIn('\x1b[38;2;215;175;255mstd::string', output)
        self.assertIn('\x1b[38;2;255;95;135mconst', output)
        self.assertIn('\x1b[38;2;95;215;255msummarize', output)
        self.assertIn('\x1b[38;2;255;95;135mreturn', output)
        self.assertIn('\x1b[38;2;95;215;255mstd::to_string', output)
        self.assertIn('\x1b[38;2;135;255;175mstd::cout', output)
        self.assertIn('\x1b[38;2;255;215;95m"Taylor"', output)

    def test_code_block_highlights_php(self) -> None:
        markdown = '```php\n<?php\n\nfunction summarize(string $name, int $tasksDone): string {\n    return "{$name} completed {$tasksDone} tasks";\n}\n\necho summarize("Riley", 1204) . PHP_EOL;\n```'
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp), width=100).render(markdown)
        self.assertIn('\x1b[38;2;135;255;175m<?php', output)
        self.assertIn('\x1b[38;2;255;95;135mfunction', output)
        self.assertIn('\x1b[38;2;215;175;255mstring', output)
        self.assertIn('\x1b[38;2;135;255;175m$name', output)
        self.assertIn('\x1b[38;2;255;95;135mreturn', output)
        self.assertIn('\x1b[38;2;255;215;95m"Riley"', output)
        self.assertIn('\x1b[38;2;135;255;175mPHP_EOL', output)

    def test_code_block_highlights_html(self) -> None:
        markdown = '```html\n<section class="summary" data-count="1204">\n  <h2>Renderer demo</h2>\n</section>\n```'
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp), width=100).render(markdown)
        self.assertIn('\x1b[38;2;95;215;255msection', output)
        self.assertIn('\x1b[38;2;215;175;255mclass', output)
        self.assertIn('\x1b[38;2;255;215;95m"summary"', output)
        self.assertIn('\x1b[38;2;95;215;255mh2', output)

    def test_raw_html_block_renders_highlighted(self) -> None:
        markdown = '<section class="summary">\n  <h2>Renderer demo</h2>\n</section>\n'
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp), width=100).render(markdown)
        self.assertIn("┌", output)
        self.assertIn('\x1b[38;2;95;215;255msection', output)

    def test_code_block_highlights_yaml_toml_sql_js_css(self) -> None:
        markdown = """```yaml
title: "Demo"
count: 1204
enabled: true
```

```toml
[render]
schema = "dark"
width = 80
```

```sql
select count(*) from events where total > 1204
```

```js
const total = parseInt("1204", 10);
return total;
```

```css
.summary {
  color: #fff;
  margin: 12px;
}
```
"""
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp), width=100).render(markdown)
        self.assertIn('\x1b[38;2;95;215;255mtitle', output)
        self.assertIn('\x1b[38;2;135;255;175mtrue', output)
        self.assertIn('\x1b[38;2;135;255;175m[render]', output)
        self.assertIn('\x1b[38;2;255;95;135mSELECT', output)
        self.assertIn('\x1b[38;2;95;215;255mparseInt', output)
        self.assertIn('\x1b[38;2;95;215;255m.summary', output)
        self.assertIn('\x1b[38;2;95;215;255mcolor', output)

    def test_code_block_highlights_shell_commands(self) -> None:
        markdown = "```bash\nPYTHONPATH=src python3 -m unittest discover -s tests -v\npython3 scripts/build_zipapp.py\n/home/parf/bin/cat-md --help\n./dist/cat-md --help\n```"
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp), width=100).render(markdown)
        self.assertIn('\x1b[38;2;135;255;175mPYTHONPATH=', output)
        self.assertIn('\x1b[38;2;95;215;255mpython3', output)
        self.assertIn('\x1b[38;2;215;175;255munittest', output)
        self.assertIn('\x1b[38;2;255;95;135m-m', output)
        self.assertIn('\x1b[38;2;215;175;255mscripts/build_zipapp.py', output)
        self.assertIn('\x1b[38;2;215;175;255m/home/parf/bin/cat-md', output)
        self.assertIn('\x1b[38;2;215;175;255m./dist/cat-md', output)
        self.assertIn('\x1b[38;2;255;95;135m--help', output)

    def test_html_br_and_raw_html(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp)).render("a<br>b <b>raw</b>")
        self.assertIn("a\nb", output)
        self.assertIn("<b>raw</b>", output)

    def test_strikethrough(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp)).render("keep ~~remove~~ done")
        self.assertIn("\x1b[9mremove\x1b[29m", output)
        self.assertNotIn("~~remove~~", output)

    def test_task_list_markers_render_as_fancy_unicode(self) -> None:
        markdown = "- [x] Create initial brief\n- [ ] Final legal review\n\n• [x] Add code samples\n• [ ] Publish release blog\n"
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp)).render(markdown)
        self.assertIn("✅", output)
        self.assertIn("⬜", output)
        self.assertIn("Add code samples\n•", output)
        self.assertNotIn("[x]", output)
        self.assertNotIn("[ ]", output)

    def test_nested_list_keeps_nested_bullets(self) -> None:
        markdown = "- Project kickoff complete\n- Documentation drafted\n- Review items:\n  - Confirm release date\n  - Confirm owner for QA\n  - Confirm rollout checklist\n"
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp)).render(markdown)
        self.assertIn("• Review items:", output)
        self.assertIn("    • Confirm release date", output)
        self.assertIn("    • Confirm owner for QA", output)
        self.assertIn("    • Confirm rollout checklist", output)

    def test_callouts_render_with_fancy_unicode_labels(self) -> None:
        markdown = "> [!NOTE]\n> Useful note\n\n> [!WARNING]\n> Careful now\n"
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp)).render(markdown)
        self.assertIn("█", output)
        self.assertIn("🛈", output)
        self.assertIn("Note", output)
        self.assertIn("Useful note", output)
        self.assertIn("⚠️", output)
        self.assertIn("Warning", output)
        self.assertNotIn("[!NOTE]", output)
        self.assertNotIn("[!WARNING]", output)

    def test_extra_notice_callouts_render_with_fancy_unicode_labels(self) -> None:
        markdown = "\n\n".join(
            f"> [!{kind}]\n> Notice body"
            for kind in ["INFO", "DANGER", "SUCCESS", "ERROR", "QUESTION", "EXAMPLE"]
        )
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp)).render(markdown)
        for label in ["Info", "Danger", "Success", "Error", "Question", "Example"]:
            self.assertIn(label, output)
        for icon in ["🔷", "⚡", "✅", "🛑", "❓", "🧪"]:
            self.assertIn(icon, output)
        self.assertIn("\x1b[38;2;255;0;95m", output)
        self.assertIn("\x1b[38;2;95;255;135m", output)
        self.assertIn("\x1b[38;2;255;135;255m", output)
        for marker in ["[!INFO]", "[!DANGER]", "[!SUCCESS]", "[!ERROR]", "[!QUESTION]", "[!EXAMPLE]"]:
            self.assertNotIn(marker, output)

    def test_nested_blockquote_preserves_nested_level(self) -> None:
        markdown = "> Outer quote\n>\n> > Nested quote\n"
        with tempfile.TemporaryDirectory() as temp:
            output = make_renderer(Path(temp)).render(markdown)
        self.assertIn("Outer quote", output)
        self.assertIn("Nested quote", output)
        nested_line = next(line for line in output.splitlines() if "Nested quote" in line)
        self.assertGreaterEqual(nested_line.count("▌"), 2)

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
        self.assertNotIn("--place", command)
        self.assertIn("--stdin", command)
        self.assertIn("no", command)
        self.assertIn("<image>", output)
        self.assertIn("Alt text", output)


if __name__ == "__main__":
    unittest.main()
