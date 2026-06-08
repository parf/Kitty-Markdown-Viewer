from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import tomllib

from .config import Config


@dataclass(frozen=True)
class Theme:
    name: str
    colors: dict[str, str]


DEFAULT_COLORS = {
    "h1": "#ff5f87",
    "h2": "#5fd7ff",
    "h3": "#ffd75f",
    "h4": "#87ffaf",
    "h5": "#d7afff",
    "h6": "#9ca3af",
    "body": "#e6e6e6",
    "muted": "#9ca3af",
    "link": "#5fafff",
    "link_underline": "#5fafff",
    "inline_code": "#ffaf5f",
    "code_block": "#d7d7d7",
    "diff_remove_fg": "#ff5f5f",
    "diff_remove_bg": "#3a1010",
    "diff_add_fg": "#5fff87",
    "diff_add_bg": "#103a1a",
    "json_key": "#5fd7ff",
    "json_string": "#ffd75f",
    "json_number": "#d7afff",
    "json_literal": "#87ffaf",
    "code_keyword": "#ff5f87",
    "code_function": "#5fd7ff",
    "code_type": "#d7afff",
    "code_macro": "#87ffaf",
    "date": "#ffaf5f",
    "number_major": "#ffd75f",
    "blockquote": "#afd75f",
    "table_border": "#5f8787",
    "table_header": "#ffffff",
    "table_text": "#e6e6e6",
    "rule": "#5f8787",
    "error": "#ff5f5f",
}


def load_theme(path: Path, name: str) -> Theme:
    with path.open("rb") as fh:
        data = tomllib.load(fh)
    colors = DEFAULT_COLORS | dict(data.get("colors", {}))
    return Theme(name=name, colors=colors)


def resolve_theme(config: Config, override: str | None = None) -> Theme:
    schema = override or config.schema
    if schema == "detect":
        schema = detect_schema()
    if schema == "light":
        return load_theme(config.light_theme_path, "light")
    return load_theme(config.dark_theme_path, "dark")


def detect_schema() -> str:
    background = _query_kitty_background()
    if not background:
        return "dark"
    rgb = _parse_hex_color(background)
    if not rgb:
        return "dark"
    r, g, b = rgb
    luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
    return "light" if luminance > 0.5 else "dark"


def _query_kitty_background() -> str | None:
    commands = [
        ["kitten", "@", "get-colors"],
        ["kitty", "@", "get-colors"],
    ]
    for command in commands:
        try:
            result = subprocess.run(
                command,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=0.75,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if result.returncode != 0:
            continue
        match = re.search(r"^background\\s+(.+)$", result.stdout, re.MULTILINE)
        if match:
            return match.group(1).strip()
    return None


def _parse_hex_color(value: str) -> tuple[int, int, int] | None:
    match = re.search(r"#?([0-9a-fA-F]{6})", value)
    if not match:
        return None
    hex_value = match.group(1)
    return (
        int(hex_value[0:2], 16),
        int(hex_value[2:4], 16),
        int(hex_value[4:6], 16),
    )
