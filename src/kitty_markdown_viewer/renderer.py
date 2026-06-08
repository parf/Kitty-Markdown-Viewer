from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import re
import shutil
import subprocess
import textwrap
from urllib.parse import urljoin, urlparse

from markdown_it import MarkdownIt
from markdown_it.token import Token
from wcwidth import wcwidth, wcswidth

from .config import Config
from .fetch import fetch_image_to_temp
from .themes import Theme


ESC = "\x1b"
BEL = "\x07"
ST = ESC + "\\"
RESET = ESC + "[0m"
URL_RE = re.compile(r"(?P<url>(?:https?://|ftp://|mailto:)[^\s<>()]+)", re.IGNORECASE)
BR_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)


@dataclass(frozen=True)
class Source:
    path: Path | None = None
    url: str | None = None


@dataclass
class RenderOptions:
    width: int
    table_style: str = "unicode"


class MarkdownRenderer:
    def __init__(self, config: Config, theme: Theme, *, width: int | None = None) -> None:
        terminal_width = shutil.get_terminal_size((100, 24)).columns
        configured_width = width or config.width or terminal_width
        self.config = config
        self.theme = theme
        self.options = RenderOptions(width=max(20, configured_width), table_style=config.table_style)
        self.md = MarkdownIt("commonmark").enable("table")

    def render(self, markdown: str, *, source: Source | None = None) -> str:
        tokens = self.md.parse(markdown)
        lines: list[str] = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.type == "heading_open":
                inline = tokens[i + 1] if i + 1 < len(tokens) else None
                text = self._inline_plain(inline.children or []) if inline else ""
                lines.extend(self._render_heading(int(token.tag[1]), text))
                i += 3
                continue
            if token.type == "paragraph_open":
                inline = tokens[i + 1] if i + 1 < len(tokens) else None
                rendered = self._render_inline(inline.children or [], source=source) if inline else ""
                if rendered:
                    lines.extend(rendered.splitlines())
                    lines.append("")
                i += 3
                continue
            if token.type == "fence":
                lines.extend(self._render_code_block(token.content, token.info))
                i += 1
                continue
            if token.type == "code_block":
                lines.extend(self._render_code_block(token.content, ""))
                i += 1
                continue
            if token.type == "hr":
                lines.append(self._color("rule") + ("━" * self.options.width) + RESET)
                lines.append("")
                i += 1
                continue
            if token.type == "blockquote_open":
                end = self._find_matching(tokens, i)
                inner = self._render_inner(tokens[i + 1 : end], source=source)
                quote_color = self._color("blockquote")
                for line in inner.splitlines():
                    lines.append(f"{quote_color}▌{RESET} {line}")
                lines.append("")
                i = end + 1
                continue
            if token.type in {"bullet_list_open", "ordered_list_open"}:
                end = self._find_matching(tokens, i)
                lines.extend(self._render_list(tokens[i:end + 1], ordered=token.type == "ordered_list_open", source=source))
                lines.append("")
                i = end + 1
                continue
            if token.type == "table_open":
                end = self._find_matching(tokens, i)
                lines.extend(self._render_table(tokens[i:end + 1], source=source))
                lines.append("")
                i = end + 1
                continue
            i += 1
        return "\n".join(lines).rstrip() + "\n"

    def _render_inner(self, tokens: list[Token], *, source: Source | None) -> str:
        old = self.md
        del old
        lines: list[str] = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.type == "paragraph_open":
                inline = tokens[i + 1] if i + 1 < len(tokens) else None
                rendered = self._render_inline(inline.children or [], source=source) if inline else ""
                if rendered:
                    lines.extend(rendered.splitlines())
                i += 3
            elif token.type == "fence":
                lines.extend(self._render_code_block(token.content, token.info))
                i += 1
            else:
                i += 1
        return "\n".join(lines)

    def _render_heading(self, level: int, text: str) -> list[str]:
        if level == 1:
            return self._render_large_heading(text, scale=self.config.h1_scale, color_name="h1", blank_after=1)
        if level == 2:
            return self._render_large_heading(text, scale=self.config.h2_scale, color_name="h2", blank_after=1)
        if level == 3:
            lines = self._render_large_heading(text, scale=self.config.h3_scale, color_name="h3", blank_after=0)
            visible_width = min(self.options.width, max(8, wcswidth(text)))
            lines.append(self._color("h3") + ("━" * visible_width) + RESET)
            lines.append("")
            return lines
        return [self._color("h4") + text + RESET, ""]

    def _render_large_heading(self, text: str, *, scale: int, color_name: str, blank_after: int) -> list[str]:
        max_chars = max(1, self.options.width // max(1, scale))
        effective_scale = scale
        if self.config.shrink_long_headings and len(text) > max_chars * 3 and scale > 2:
            effective_scale = scale - 1
            max_chars = max(1, self.options.width // effective_scale)
        wrapped = textwrap.wrap(text, width=max_chars, break_long_words=False) or [text]
        output: list[str] = []
        for part in wrapped:
            output.append(self._color(color_name) + f"{ESC}]66;s={effective_scale};{part}{BEL}" + RESET)
            output.extend([""] * max(0, effective_scale - 1))
        output.extend([""] * blank_after)
        return output

    def _render_code_block(self, content: str, info: str) -> list[str]:
        del info
        color = self._color("code_block")
        border = self._color("muted")
        lines = [border + "┌" + ("─" * (self.options.width - 2)) + "┐" + RESET]
        for raw in content.rstrip("\n").splitlines():
            text = raw[: max(0, self.options.width - 4)]
            lines.append(border + "│ " + RESET + color + text.ljust(self.options.width - 4) + RESET + border + " │" + RESET)
        lines.append(border + "└" + ("─" * (self.options.width - 2)) + "┘" + RESET)
        lines.append("")
        return lines

    def _render_list(self, tokens: list[Token], *, ordered: bool, source: Source | None) -> list[str]:
        lines: list[str] = []
        item_index = 1
        i = 0
        while i < len(tokens):
            if tokens[i].type == "list_item_open":
                end = self._find_matching(tokens, i)
                marker = f"{item_index}." if ordered else "•"
                item_text = self._render_inner(tokens[i + 1 : end], source=source).strip()
                wrapped = wrap_rendered(item_text, max(10, self.options.width - 4))
                for line_no, line in enumerate(wrapped or [""]):
                    prefix = marker if line_no == 0 else " " * visible_width(marker)
                    lines.append(f"{prefix} {line}")
                item_index += 1
                i = end + 1
            else:
                i += 1
        return lines

    def _render_table(self, tokens: list[Token], *, source: Source | None) -> list[str]:
        rows: list[list[str]] = []
        aligns: list[str] = []
        current_row: list[str] | None = None
        current_aligns: list[str] = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.type == "tr_open":
                current_row = []
                current_aligns = []
            elif token.type in {"th_open", "td_open"} and current_row is not None:
                align = self._align_from_token(token)
                inline = tokens[i + 1] if i + 1 < len(tokens) else None
                current_row.append(self._render_inline(inline.children or [], source=source) if inline else "")
                current_aligns.append(align)
                i += 2
                continue
            elif token.type == "tr_close" and current_row is not None:
                rows.append(current_row)
                if current_aligns:
                    aligns = current_aligns
                current_row = None
            i += 1
        if not rows:
            return []
        column_count = max(len(row) for row in rows)
        for row in rows:
            row.extend([""] * (column_count - len(row)))
        if len(aligns) < column_count:
            aligns.extend(["left"] * (column_count - len(aligns)))
        available = max(10, self.options.width - column_count - 1)
        raw_widths = [max(3, max(visible_width(row[col]) for row in rows)) for col in range(column_count)]
        widths = fit_widths(raw_widths, available)
        if self.options.table_style == "plain":
            return self._render_plain_table(rows, aligns, widths)
        return self._render_unicode_table(rows, aligns, widths)

    def _render_unicode_table(self, rows: list[list[str]], aligns: list[str], widths: list[int]) -> list[str]:
        border_color = self._color("table_border")
        text_color = self._color("table_text")
        header_color = self._color("table_header")

        def border(left: str, sep: str, right: str) -> str:
            pieces = [left]
            for idx, width in enumerate(widths):
                pieces.append("─" * (width + 2))
                pieces.append(right if idx == len(widths) - 1 else sep)
            return border_color + "".join(pieces) + RESET

        output = [border("┌", "┬", "┐")]
        for row_index, row in enumerate(rows):
            wrapped_cells = [wrap_rendered(cell, width) for cell, width in zip(row, widths, strict=False)]
            height = max(len(cell) for cell in wrapped_cells)
            for cell in wrapped_cells:
                cell.extend([""] * (height - len(cell)))
            for line_index in range(height):
                parts = [border_color + "│" + RESET]
                for col, width in enumerate(widths):
                    cell = align_rendered(wrapped_cells[col][line_index], width, aligns[col])
                    color = header_color if row_index == 0 else text_color
                    parts.append(" " + color + cell + RESET + " " + border_color + "│" + RESET)
                output.append("".join(parts))
            if row_index == 0:
                output.append(border("├", "┼", "┤"))
        output.append(border("└", "┴", "┘"))
        return output

    def _render_plain_table(self, rows: list[list[str]], aligns: list[str], widths: list[int]) -> list[str]:
        output: list[str] = []
        for row in rows:
            wrapped_cells = [wrap_rendered(cell, width) for cell, width in zip(row, widths, strict=False)]
            height = max(len(cell) for cell in wrapped_cells)
            for cell in wrapped_cells:
                cell.extend([""] * (height - len(cell)))
            for line_index in range(height):
                output.append("  ".join(align_rendered(wrapped_cells[col][line_index], widths[col], aligns[col]) for col in range(len(widths))))
        return output

    def _render_inline(self, tokens: list[Token], *, source: Source | None) -> str:
        output: list[str] = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.type == "text":
                output.append(linkify_bare(token.content, self._link_style()))
            elif token.type == "softbreak":
                output.append(" ")
            elif token.type == "hardbreak":
                output.append("\n")
            elif token.type == "code_inline":
                output.append(self._color("inline_code") + token.content + RESET)
            elif token.type == "strong_open":
                end = self._find_inline_close(tokens, i, "strong_close")
                output.append(ESC + "[1m" + self._render_inline(tokens[i + 1 : end], source=source) + RESET)
                i = end
            elif token.type == "em_open":
                end = self._find_inline_close(tokens, i, "em_close")
                output.append(ESC + "[3m" + self._render_inline(tokens[i + 1 : end], source=source) + RESET)
                i = end
            elif token.type == "link_open":
                href = token.attrs.get("href", "") if token.attrs else ""
                end = self._find_inline_close(tokens, i, "link_close")
                label = self._render_inline(tokens[i + 1 : end], source=source)
                output.append(link_escape(resolve_url(href, source), label, self._link_style()))
                i = end
            elif token.type == "image":
                output.append(self._render_image(token, source=source))
            elif token.type == "html_inline":
                if BR_RE.fullmatch(token.content.strip()):
                    output.append("\n")
                else:
                    output.append(token.content)
            else:
                output.append(token.content)
            i += 1
        return "".join(output)

    def _inline_plain(self, tokens: list[Token]) -> str:
        parts: list[str] = []
        for token in tokens:
            if token.type == "text":
                parts.append(token.content)
            elif token.type == "code_inline":
                parts.append(token.content)
            elif token.type == "image":
                parts.append(token.content)
            elif token.children:
                parts.append(self._inline_plain(token.children))
        return "".join(parts)

    def _render_image(self, token: Token, *, source: Source | None) -> str:
        alt = token.content or (token.attrs or {}).get("alt", "")
        src = (token.attrs or {}).get("src", "")
        if not self.config.images_enabled:
            return alt
        target = resolve_url(src, source)
        cleanup: Path | None = None
        error: str | None = None
        path: Path
        if urlparse(target).scheme in {"http", "https"}:
            try:
                path = fetch_image_to_temp(target, timeout=self.config.fetch_timeout_seconds)
                cleanup = path
            except Exception as exc:  # remote image failures should not abort rendering
                error = f"[image error: {exc}]"
                path = Path()
        else:
            path = Path(target).expanduser()
            if not path.is_absolute() and source and source.path:
                path = source.path.parent / path
        if error:
            return self._color("error") + error + RESET + ("\n" + alt if alt else "")
        output = self._run_icat(path)
        if cleanup:
            try:
                cleanup.unlink(missing_ok=True)
            except OSError:
                pass
        if alt:
            output = output.rstrip("\n") + "\n" + self._color("muted") + alt + RESET
        return output

    def _run_icat(self, path: Path) -> str:
        width = min(self.config.image_max_width or self.options.width, self.options.width)
        height = max(0, self.config.image_max_height)
        command = ["kitten", "icat", "--align", "left", "--transfer-mode", "detect", "--place", f"{width}x{height}@0x0", str(path)]
        try:
            result = subprocess.run(command, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except OSError as exc:
            return self._color("error") + f"[image error: {exc}]" + RESET
        if result.returncode != 0:
            stderr = result.stderr.strip() or "kitten icat failed"
            return self._color("error") + f"[image error: {stderr}]" + RESET
        return result.stdout

    def _find_matching(self, tokens: list[Token], start: int) -> int:
        level = 0
        opener = tokens[start].type
        closer = opener.replace("_open", "_close")
        for idx in range(start, len(tokens)):
            if tokens[idx].type == opener:
                level += 1
            elif tokens[idx].type == closer:
                level -= 1
                if level == 0:
                    return idx
        return len(tokens) - 1

    def _find_inline_close(self, tokens: list[Token], start: int, close_type: str) -> int:
        for idx in range(start + 1, len(tokens)):
            if tokens[idx].type == close_type:
                return idx
        return start

    def _align_from_token(self, token: Token) -> str:
        style = (token.attrs or {}).get("style", "")
        if "right" in style:
            return "right"
        if "center" in style:
            return "center"
        return "left"

    def _color(self, name: str) -> str:
        return sgr_fg(self.theme.colors.get(name, "#ffffff"))

    def _link_style(self) -> str:
        color = hex_to_rgb(self.theme.colors.get("link", "#5fafff"))
        underline = hex_to_rgb(self.theme.colors.get("link_underline", "#5fafff"))
        return f"{ESC}[38;2;{color[0]};{color[1]};{color[2]}m{ESC}[58;2;{underline[0]};{underline[1]};{underline[2]}m{ESC}[4:1m"


def resolve_url(value: str, source: Source | None) -> str:
    parsed = urlparse(value)
    if parsed.scheme:
        return value
    if source and source.url:
        return urljoin(source.url, value)
    if source and source.path:
        return str((source.path.parent / value).expanduser())
    return value


def link_escape(url: str, label: str, style: str) -> str:
    return f"{ESC}]8;;{url}{ST}{style}{label}{RESET}{ESC}]8;;{ST}"


def linkify_bare(text: str, style: str) -> str:
    pieces: list[str] = []
    pos = 0
    for match in URL_RE.finditer(text):
        start, end = match.span("url")
        url = match.group("url")
        trailing = ""
        while url and url[-1] in ".,;:!?)]}":
            trailing = url[-1] + trailing
            url = url[:-1]
            end -= 1
        pieces.append(text[pos:start])
        pieces.append(link_escape(url, url, style))
        pieces.append(trailing)
        pos = match.end("url")
    pieces.append(text[pos:])
    return "".join(pieces)


def sgr_fg(hex_color: str) -> str:
    r, g, b = hex_to_rgb(hex_color)
    return f"{ESC}[38;2;{r};{g};{b}m"


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) != 6:
        return (255, 255, 255)
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def visible_width(value: str) -> int:
    return wcswidth(strip_escape_sequences(value))


def strip_escape_sequences(value: str) -> str:
    result: list[str] = []
    i = 0
    while i < len(value):
        if value.startswith(ESC + "]", i):
            bel = value.find(BEL, i + 2)
            st = value.find(ST, i + 2)
            ends = [pos for pos in [bel, st] if pos != -1]
            if not ends:
                i += 2
                continue
            end = min(ends)
            i = end + (1 if end == bel else 2)
            continue
        if value.startswith(ESC + "[", i):
            match = re.match(r"\x1b\[[0-9;:]*[A-Za-z]", value[i:])
            if match:
                i += len(match.group(0))
                continue
        result.append(value[i])
        i += 1
    return "".join(result)


def rendered_atoms(value: str) -> list[tuple[str, int]]:
    atoms: list[tuple[str, int]] = []
    i = 0
    while i < len(value):
        if value.startswith(ESC + "]", i):
            bel = value.find(BEL, i + 2)
            st = value.find(ST, i + 2)
            ends = [pos for pos in [bel, st] if pos != -1]
            if ends:
                end = min(ends)
                size = end + (1 if end == bel else 2) - i
                atoms.append((value[i:i + size], 0))
                i += size
                continue
        if value.startswith(ESC + "[", i):
            match = re.match(r"\x1b\[[0-9;:]*[A-Za-z]", value[i:])
            if match:
                atoms.append((match.group(0), 0))
                i += len(match.group(0))
                continue
        char = value[i]
        width = max(0, wcwidth(char))
        atoms.append((char, width))
        i += 1
    return atoms


def wrap_rendered(value: str, width: int) -> list[str]:
    if width <= 0:
        return [value]
    atoms = rendered_atoms(value)
    lines: list[str] = []
    current: list[str] = []
    current_width = 0
    last_space_index: int | None = None
    last_space_width = 0
    for atom, atom_width in atoms:
        if atom == "\n":
            lines.append("".join(current).rstrip())
            current = []
            current_width = 0
            last_space_index = None
            last_space_width = 0
            continue
        if current_width + atom_width > width and current:
            if last_space_index is not None:
                line = "".join(current[:last_space_index]).rstrip()
                rest = current[last_space_index + 1 :]
                lines.append(line)
                current = rest
                current_width = sum(w for text, w in rendered_atoms("".join(current)))
            else:
                current.append("…")
                lines.append("".join(current))
                current = []
                current_width = 0
            last_space_index = None
            last_space_width = 0
        current.append(atom)
        current_width += atom_width
        if atom == " ":
            last_space_index = len(current) - 1
            last_space_width = current_width
    del last_space_width
    if current or not lines:
        lines.append("".join(current).rstrip())
    return lines


def align_rendered(value: str, width: int, align: str) -> str:
    pad = max(0, width - visible_width(value))
    if align == "right":
        return (" " * pad) + value
    if align == "center":
        left = pad // 2
        return (" " * left) + value + (" " * (pad - left))
    return value + (" " * pad)


def fit_widths(raw_widths: list[int], available: int) -> list[int]:
    widths = raw_widths[:]
    if sum(widths) <= available:
        return widths
    minimum = 6
    while sum(widths) > available and max(widths) > minimum:
        idx = max(range(len(widths)), key=widths.__getitem__)
        widths[idx] -= 1
    return [max(3, width) for width in widths]
