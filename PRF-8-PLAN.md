# PRF-8: Kitty Markdown CLI Renderer

Author: Serg Parf <sergey.porfiriev@gmail.com>

## Goal

Build `kitty-md`, a small CLI filter that renders Markdown with latest-kitty terminal features instead of portable lowest-common-denominator terminal output.

Core requirements:

- Use kitty-first rendering: truecolor, OSC 8 hyperlinks, OSC 66 text sizing, styled underlines, and kitty graphics.
- Render H1/H2 as genuinely large text. H1 defaults to scale 4, H2 defaults to scale 2.
- Render H3 as two-line-height text with a separator line underneath.
- Render Markdown links as web-like label-only clickable text.
- Make all bare `http`, `https`, `ftp`, and `mailto` links clickable.
- Render inline images via `kitten icat`, with alt text/caption below the image.
- Support local files, stdin, explicit `-` stdin, and remote Markdown URLs.
- Support GitHub-style pipe tables with Unicode boxes and wrapped cell content.
- Support light/dark themes, defaulting to kitty background detection.
- Auto-create commented TOML config/theme files under `~/.config/kitty-md/`.
- Always emit kitty/color/control sequences, including when stdout is redirected.

## Current Implementation

Package layout:

```text
.
├── pyproject.toml
├── README.md
├── PRF-8-PLAN.md
├── scripts/
│   └── build_zipapp.py
├── src/
│   └── kitty_markdown_viewer/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── fetch.py
│       ├── themes.py
│       └── renderer.py
└── tests/
    ├── test_cli.py
    ├── test_config.py
    ├── test_fetch.py
    └── test_renderer.py
```

Implemented command:

```bash
kitty-md
cat README.md | kitty-md
kitty-md README.md
kitty-md file1.md - file2.md
kitty-md https://example.com/README.md
```

Behavior:

- `kitty-md` with no args and interactive stdin shows help.
- No-arg piped stdin renders Markdown.
- `-` reads stdin explicitly among file/URL inputs.
- URL inputs follow redirects and use a 10 second timeout.
- Remote Markdown fetch failures fail immediately.
- Remote image fetch failures render an error plus alt/caption and continue.
- Local image paths may reference any readable path.
- Raw HTML support is intentionally small: `<br>` becomes a line break; other HTML renders literally.
- Pager support is deferred; output goes to stdout.

## Config And Themes

Default files:

```text
~/.config/kitty-md/config.toml
~/.config/kitty-md/themes/dark.toml
~/.config/kitty-md/themes/light.toml
```

Rules:

- Missing config/theme files are created silently on first run.
- `--init-config` refuses to overwrite existing config/theme files.
- CLI flags override config values.
- Config uses TOML and includes comments explaining options.
- Users can define custom colors by editing or adding theme TOML files.
- `detect` queries kitty background color where possible and falls back to `dark`.

## Rendering Notes

Markdown parsing uses `markdown-it-py`; rendering is custom where kitty behavior matters.

Kitty sample references used:

- `/rd/bin/sample/kitty/text-sizing-demo` for OSC 66 large text.
- `/rd/bin/sample/kitty/link-demo` and `/rd/bin/render-link` for OSC 8 clickable labels.
- `/rd/bin/sample/kitty/image-display-demo` for `kitten icat`.
- `/rd/bin/sample/kitty/underlines-demo` for styled/colored underlines.
- `/rd/bin/sample/kitty/horizontal-line-demo` for full-width rules.

Table rendering:

- Parses GitHub-style pipe tables.
- Preserves left/right/center alignment markers.
- Computes visible width while ignoring ANSI/OSC escapes.
- Wraps long cell text to additional lines like web table cells.
- Uses ellipsis only for unbreakable segments that cannot fit cleanly.
- Keeps links clickable inside cells.
- Defaults to Unicode boxed tables, with `--table-style plain` available.

## Install Paths

Normal package entrypoint:

```bash
pip install .
kitty-md --help
```

Self-contained Python-required executable:

```bash
python3 scripts/build_zipapp.py
./dist/kitty-md --help
```

Local install currently used:

```bash
install -m 755 dist/kitty-md /home/parf/bin/kitty-md
```

## Verification

Automated:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 scripts/build_zipapp.py
/home/parf/bin/kitty-md --help
```

Manual kitty checks:

- Confirm links are clickable and show only labels for Markdown links.
- Confirm bare `http`, `https`, `ftp`, and `mailto` links are clickable.
- Confirm H1/H2 are large via OSC 66, not just styled.
- Confirm H3 uses two-line-height text plus separator.
- Confirm inline images render in-place with alt/caption below.
- Confirm tables remain readable with wrapped cells and clickable links.
- Confirm both light and dark themes are usable.
- Confirm no-arg interactive usage shows help.
- Confirm pipe mode still renders stdin.

## Follow-Ups

- Improve long-heading scale/wrap heuristics after visual testing in kitty.
- Add more table fixtures for nested inline styles and very wide Unicode text.
- Add optional pager support as a separate task.
- Add richer raw HTML support only if real input requires it.
- Consider install helper command for copying the zipapp to `~/bin`.

