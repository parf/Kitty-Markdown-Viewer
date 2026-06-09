from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import tomllib


DEFAULT_CONFIG = """# cat-md configuration.
# This file is created silently on first run. CLI flags override these values.

[render]
# Theme selection. Use "detect", "dark", or "light".
schema = "detect"

# Width in terminal cells. Use 0 to read the current terminal width.
width = 0

# Table rendering style. "unicode" is the primary style; "plain" is simpler.
table_style = "unicode"

# Emit kitty/color/control sequences even when stdout is redirected.
always_emit_escape_sequences = true

[headings]
# Kitty OSC 66 text scales. H1 is intentionally very large.
h1_scale = 4
h2_scale = 2
h3_scale = 2

# If true, very long large headings may reduce scale to fit better.
shrink_long_headings = true

[images]
# Render Markdown images through kitten icat.
enabled = true

# Maximum image width in terminal cells. 0 means terminal width.
max_width = 0

# Maximum image height in terminal cells. 0 means let kitty decide.
max_height = 0

[fetch]
# Remote Markdown/image fetch timeout in seconds.
timeout_seconds = 10

# Remote Markdown auth headers/cookies are intentionally out of scope for v1.

[themes]
# Theme files are TOML files under ~/.config/cat-md/themes by default.
dark = "themes/dark.toml"
light = "themes/light.toml"
"""


DEFAULT_DARK_THEME = """# cat-md dark theme.

[colors]
h1 = "#ff5f87"
h2 = "#5fd7ff"
h3 = "#ffd75f"
h4 = "#87ffaf"
h5 = "#d7afff"
h6 = "#9ca3af"
body = "#e6e6e6"
muted = "#9ca3af"
link = "#5fafff"
link_underline = "#5fafff"
inline_code = "#ffaf5f"
code_block = "#d7d7d7"
diff_remove_fg = "#ff5f5f"
diff_remove_bg = "#3a1010"
diff_add_fg = "#5fff87"
diff_add_bg = "#103a1a"
json_key = "#5fd7ff"
json_string = "#ffd75f"
json_number = "#d7afff"
json_literal = "#87ffaf"
code_keyword = "#ff5f87"
code_function = "#5fd7ff"
code_type = "#d7afff"
code_macro = "#87ffaf"
date = "#ffaf5f"
number_major = "#ffd75f"
blockquote = "#afd75f"
callout_info = "#00afff"
callout_danger = "#ff005f"
callout_success = "#5fff87"
callout_error = "#ff0000"
callout_question = "#ffd75f"
callout_example = "#ff87ff"
table_border = "#5f8787"
table_header = "#ffffff"
table_text = "#e6e6e6"
rule = "#5f8787"
error = "#ff5f5f"
"""


DEFAULT_LIGHT_THEME = """# cat-md light theme.

[colors]
h1 = "#d7005f"
h2 = "#005faf"
h3 = "#af5f00"
h4 = "#00875f"
h5 = "#5f00af"
h6 = "#606060"
body = "#202020"
muted = "#606060"
link = "#005fd7"
link_underline = "#005fd7"
inline_code = "#af5f00"
code_block = "#303030"
diff_remove_fg = "#af0000"
diff_remove_bg = "#ffd7d7"
diff_add_fg = "#008700"
diff_add_bg = "#d7ffd7"
json_key = "#005faf"
json_string = "#af5f00"
json_number = "#5f00af"
json_literal = "#00875f"
code_keyword = "#af005f"
code_function = "#005faf"
code_type = "#5f00af"
code_macro = "#00875f"
date = "#af5f00"
number_major = "#875f00"
blockquote = "#5f8700"
callout_info = "#005fd7"
callout_danger = "#af0000"
callout_success = "#008700"
callout_error = "#af0000"
callout_question = "#875f00"
callout_example = "#8700af"
table_border = "#5f8787"
table_header = "#000000"
table_text = "#202020"
rule = "#5f8787"
error = "#d70000"
"""


@dataclass(frozen=True)
class Config:
    config_path: Path
    config_dir: Path
    schema: str
    width: int
    table_style: str
    h1_scale: int
    h2_scale: int
    h3_scale: int
    shrink_long_headings: bool
    images_enabled: bool
    image_max_width: int
    image_max_height: int
    fetch_timeout_seconds: float
    dark_theme_path: Path
    light_theme_path: Path


def config_home() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME")
    if base:
        return Path(base)
    return Path.home() / ".config"


def default_config_dir() -> Path:
    return config_home() / "cat-md"


def default_config_path() -> Path:
    return default_config_dir() / "config.toml"


def ensure_defaults(config_path: Path | None = None, *, refuse_existing: bool = False) -> None:
    path = config_path or default_config_path()
    cfg_dir = path.parent
    theme_dir = cfg_dir / "themes"
    files = [
        (path, DEFAULT_CONFIG),
        (theme_dir / "dark.toml", DEFAULT_DARK_THEME),
        (theme_dir / "light.toml", DEFAULT_LIGHT_THEME),
    ]
    existing = [p for p, _ in files if p.exists()]
    if refuse_existing and existing:
        joined = ", ".join(str(p) for p in existing)
        raise FileExistsError(f"refusing to overwrite existing config/theme file(s): {joined}")
    cfg_dir.mkdir(parents=True, exist_ok=True)
    theme_dir.mkdir(parents=True, exist_ok=True)
    for file_path, content in files:
        if not file_path.exists():
            file_path.write_text(content, encoding="utf-8")


def _read_toml(path: Path) -> dict:
    with path.open("rb") as fh:
        return tomllib.load(fh)


def _path_from_config(config_dir: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = config_dir / path
    return path


def load_config(config_path: Path | None = None) -> Config:
    path = config_path or default_config_path()
    ensure_defaults(path)
    data = _read_toml(path)
    render = data.get("render", {})
    headings = data.get("headings", {})
    images = data.get("images", {})
    fetch = data.get("fetch", {})
    themes = data.get("themes", {})
    cfg_dir = path.parent
    return Config(
        config_path=path,
        config_dir=cfg_dir,
        schema=str(render.get("schema", "detect")),
        width=int(render.get("width", 0)),
        table_style=str(render.get("table_style", "unicode")),
        h1_scale=int(headings.get("h1_scale", 4)),
        h2_scale=int(headings.get("h2_scale", 2)),
        h3_scale=int(headings.get("h3_scale", 2)),
        shrink_long_headings=bool(headings.get("shrink_long_headings", True)),
        images_enabled=bool(images.get("enabled", True)),
        image_max_width=int(images.get("max_width", 0)),
        image_max_height=int(images.get("max_height", 0)),
        fetch_timeout_seconds=float(fetch.get("timeout_seconds", 10)),
        dark_theme_path=_path_from_config(cfg_dir, str(themes.get("dark", "themes/dark.toml"))),
        light_theme_path=_path_from_config(cfg_dir, str(themes.get("light", "themes/light.toml"))),
    )
