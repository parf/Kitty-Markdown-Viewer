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
DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
LARGE_NUMBER_RE = re.compile(r"(?<![\d-])\d{4,}(?![\d-])")
BR_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
TASK_RE = re.compile(r"(?P<prefix>(?:^|(?<=\n)|[•*-]\s+))\[(?P<mark>[ xX])\]\s+")
CALLOUT_RE = re.compile(r"^\[!(?P<kind>[A-Za-z]+)\]\s*(?P<title>.*)$")
JSON_STRING_RE = re.compile(r'"(?:\\.|[^"\\])*"')
JSON_NUMBER_RE = re.compile(r"(?<![\w.])-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?(?![\w.])")
JSON_LITERAL_RE = re.compile(r"\b(?:true|false|null)\b")
LINE_COMMENT_RE = re.compile(r"(?P<prefix>^|\s)(?P<comment>\#.*|//.*)$")
BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/")
RUST_KEYWORD_RE = re.compile(r"\b(?:as|async|await|break|const|continue|crate|dyn|else|enum|extern|false|for|if|impl|in|let|loop|match|mod|move|mut|pub|ref|return|self|Self|static|struct|super|trait|true|type|unsafe|use|where|while|fn)\b")
RUST_TYPE_RE = re.compile(r"\b(?:bool|char|str|String|usize|isize|u8|u16|u32|u64|u128|i8|i16|i32|i64|i128|f32|f64|Vec|Option|Result)\b")
RUST_FUNCTION_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*(?=\()")
RUST_MACRO_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*!)")
PYTHON_KEYWORD_RE = re.compile(r"\b(?:False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b")
PYTHON_TYPE_RE = re.compile(r"\b(?:str|int|float|bool|list|dict|tuple|set|bytes|object)\b")
PYTHON_FUNCTION_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*(?=\()")
PYTHON_DUNDER_RE = re.compile(r"\b(__[A-Za-z_][A-Za-z0-9_]*__)\b")
CPP_KEYWORD_RE = re.compile(r"\b(?:alignas|alignof|auto|break|case|class|const|constexpr|continue|delete|do|else|enum|explicit|extern|for|if|inline|namespace|new|noexcept|nullptr|private|protected|public|return|static|struct|switch|template|this|throw|try|typename|using|virtual|while)\b")
CPP_TYPE_RE = re.compile(r"\b(?:std::string|std::size_t|string|char|short|int|long|float|double|bool|void|size_t)\b")
CPP_FUNCTION_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*(?:::[A-Za-z_][A-Za-z0-9_]*)?)\s*(?=\()")
CPP_STD_SYMBOL_RE = re.compile(r"\b(std::(?:cout|cin|cerr|clog|endl))\b")
CPP_PREPROCESSOR_RE = re.compile(r"^\s*(#[A-Za-z_][A-Za-z0-9_]*)")
ANGLE_INCLUDE_RE = re.compile(r"<[A-Za-z0-9_./-]+>")
PHP_KEYWORD_RE = re.compile(r"\b(?:abstract|and|array|as|break|case|catch|class|clone|const|continue|declare|default|do|echo|else|elseif|empty|extends|final|finally|for|foreach|function|global|if|implements|include|instanceof|interface|namespace|new|null|or|private|protected|public|require|return|static|switch|throw|trait|try|use|var|while|xor)\b")
PHP_TYPE_RE = re.compile(r"\b(?:array|bool|callable|float|int|iterable|mixed|object|string|void)\b")
PHP_FUNCTION_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*(?=\()")
PHP_VARIABLE_RE = re.compile(r"(\$[A-Za-z_][A-Za-z0-9_]*)")
PHP_CONSTANT_RE = re.compile(r"\b([A-Z_][A-Z0-9_]*)\b")
PHP_TAG_RE = re.compile(r"<\?php|\?>")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->")
HTML_TAG_RE = re.compile(r"(</?)([A-Za-z][A-Za-z0-9:-]*)([^>]*?)(/?>)")
HTML_ATTR_RE = re.compile(r"([A-Za-z_:][A-Za-z0-9_:.:-]*)(\s*=\s*)(\"(?:\\.|[^\"])*\"|'(?:\\.|[^'])*')")
SHELL_ASSIGN_RE = re.compile(r"(^|\s)([A-Za-z_][A-Za-z0-9_]*=)([^\s]+)")
SHELL_FLAG_RE = re.compile(r"(?<!\S)(-{1,2}[A-Za-z0-9][A-Za-z0-9_-]*)(?!\S)")
SHELL_PATH_RE = re.compile(r"(?<!\S)((?:~|/|\./|\.\./)?[A-Za-z0-9_./-]+/[A-Za-z0-9_./-]+)(?!\S)")
TEXT_PATH_RE = re.compile(r"(?<![\w/.-])((?:~|/|\./|\.\./)[A-Za-z0-9_./-]*[A-Za-z0-9_-](?:\.[A-Za-z0-9_-]+)?)(?![\w/.-])")
SHELL_COMMAND_RE = re.compile(r"^(\s*)([A-Za-z0-9_./-]+)")
SHELL_MODULE_RE = re.compile(r"(?<=\s-m\s)([A-Za-z_][A-Za-z0-9_.]*)")
CALLOUTS = {
    "NOTE": ("🛈", "h2"),
    "TIP": ("💡", "h4"),
    "IMPORTANT": ("⬥", "h5"),
    "WARNING": ("⚠️", "h3"),
    "CAUTION": ("⛔", "error"),
}


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
        self.md = MarkdownIt("commonmark").enable("table").enable("strikethrough")

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
                lines.extend(self._render_blockquote(inner))
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

    def _render_inner(self, tokens: list[Token], *, source: Source | None, list_depth: int = 0) -> str:
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
            elif token.type == "blockquote_open":
                end = self._find_matching(tokens, i)
                inner = self._render_inner(tokens[i + 1 : end], source=source, list_depth=list_depth)
                lines.extend(self._render_blockquote(inner))
                i = end + 1
            elif token.type in {"bullet_list_open", "ordered_list_open"}:
                end = self._find_matching(tokens, i)
                lines.extend(self._render_list(tokens[i:end + 1], ordered=token.type == "ordered_list_open", source=source, depth=list_depth))
                i = end + 1
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
        if level == 4:
            return self._render_fractional_heading(text, metadata="s=2:n=2:d=3", layout_scale=2, color_name="h4")
        if level == 5:
            underline = self._underline("h5", style=1)
            return [self._color("h5") + ESC + "[1m" + underline + text + RESET + ESC + "[4:0m" + ESC + "[59m", ""]
        return [self._color("h6") + ESC + "[1m" + text + RESET, ""]

    def _render_blockquote(self, inner: str) -> list[str]:
        inner_lines = inner.splitlines()
        if not inner_lines:
            return []
        match = CALLOUT_RE.match(strip_escape_sequences(inner_lines[0]).strip())
        if not match:
            quote_color = self._color("blockquote")
            return [f"{quote_color}▌{RESET} {line}" for line in inner_lines]

        kind = match.group("kind").upper()
        title = match.group("title").strip()
        icon, color_name = CALLOUTS.get(kind, ("◆", "blockquote"))
        color = self._color(color_name)
        heading = f"{icon} {kind.title()}"
        if title:
            heading += f": {title}"
        output = [f"{color}█ {ESC}[1m{heading}{RESET}"]
        for line in inner_lines[1:]:
            output.append(f"{color}│{RESET} {line}")
        return output

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

    def _render_fractional_heading(self, text: str, *, metadata: str, layout_scale: int, color_name: str) -> list[str]:
        max_chars = max(1, self.options.width // max(1, layout_scale))
        wrapped = textwrap.wrap(text, width=max_chars, break_long_words=False) or [text]
        return [self._color(color_name) + f"{ESC}]66;{metadata};{part}{BEL}" + RESET for part in wrapped] + [""]

    def _render_code_block(self, content: str, info: str) -> list[str]:
        color = self._color("code_block")
        border = self._color("muted")
        raw_lines = content.rstrip("\n").splitlines() or [""]
        content_width = max(1, max(visible_width(line) for line in raw_lines))
        box_width = min(self.options.width, max(4, content_width + 4))
        inner_width = box_width - 4
        language = self._code_language(info)
        is_json = self._is_json_block(content, language)
        lines = [border + "┌" + ("─" * (box_width - 2)) + "┐" + RESET]
        for raw in raw_lines:
            text = truncate_rendered(raw, inner_width)
            line_style = self._code_line_style(text, color)
            rendered_text = self._highlight_code_line(text, language, is_json)
            lines.append(border + "│ " + RESET + line_style + align_rendered(rendered_text, inner_width, "left") + RESET + border + " │" + RESET)
        lines.append(border + "└" + ("─" * (box_width - 2)) + "┘" + RESET)
        lines.append("")
        return lines

    def _code_language(self, info: str) -> str:
        return info.strip().split(maxsplit=1)[0].lower() if info.strip() else ""

    def _is_json_block(self, content: str, language: str) -> bool:
        if language in {"json", "jsonc"}:
            return True
        stripped = content.strip()
        return (stripped.startswith("{") and stripped.endswith("}")) or (stripped.startswith("[") and stripped.endswith("]"))

    def _highlight_code_line(self, line: str, language: str, is_json: bool) -> str:
        if is_json:
            return self._highlight_json_line(line)
        if language in {"rs", "rust"}:
            return self._highlight_rust_line(line)
        if language in {"py", "python", "python3"}:
            return self._highlight_python_line(line)
        if language in {"c++", "cpp", "cxx", "cc", "hpp", "h++"}:
            return self._highlight_cpp_line(line)
        if language == "php":
            return self._highlight_php_line(line)
        if language in {"html", "htm"}:
            return self._highlight_html_line(line)
        if language in {"bash", "sh", "shell", "zsh"}:
            return self._highlight_shell_line(line)
        return self._highlight_code_comments(line)

    def _highlight_json_line(self, line: str) -> str:
        pieces: list[str] = []
        pos = 0
        for match in JSON_STRING_RE.finditer(line):
            before = line[pos:match.start()]
            pieces.append(self._highlight_json_scalars(before))
            token = match.group(0)
            after = line[match.end():]
            color_name = "json_key" if re.match(r"\s*:", after) else "json_string"
            pieces.append(self._color(color_name) + token + RESET)
            pos = match.end()
        pieces.append(self._highlight_json_scalars(line[pos:]))
        return "".join(pieces)

    def _highlight_json_scalars(self, text: str) -> str:
        text = JSON_NUMBER_RE.sub(lambda m: self._color("json_number") + m.group(0) + RESET, text)
        return JSON_LITERAL_RE.sub(lambda m: self._color("json_literal") + m.group(0) + RESET, text)

    def _highlight_code_comments(self, line: str) -> str:
        muted = self._color("muted")
        line = BLOCK_COMMENT_RE.sub(lambda m: muted + m.group(0) + RESET, line)
        return LINE_COMMENT_RE.sub(lambda m: m.group("prefix") + muted + m.group("comment") + RESET, line)

    def _highlight_rust_line(self, line: str) -> str:
        comments: list[str] = []

        def store_comment(match: re.Match[str]) -> str:
            comments.append(self._color("muted") + match.group(0) + RESET)
            return f"\0c{len(comments) - 1}\0"

        line = BLOCK_COMMENT_RE.sub(store_comment, line)
        line = LINE_COMMENT_RE.sub(lambda m: m.group("prefix") + store_comment(re.match(r".*", m.group("comment"))), line)

        strings: list[str] = []

        def store_string(match: re.Match[str]) -> str:
            strings.append(self._color("json_string") + match.group(0) + RESET)
            return f"\0s{len(strings) - 1}\0"

        line = JSON_STRING_RE.sub(store_string, line)
        line = JSON_NUMBER_RE.sub(lambda m: self._color("json_number") + m.group(0) + RESET, line)
        line = RUST_MACRO_RE.sub(lambda m: self._color("code_macro") + m.group(1) + RESET, line)
        line = RUST_FUNCTION_RE.sub(lambda m: self._color("code_function") + m.group(1) + RESET, line)
        line = RUST_TYPE_RE.sub(lambda m: self._color("code_type") + m.group(0) + RESET, line)
        line = RUST_KEYWORD_RE.sub(lambda m: self._color("code_keyword") + m.group(0) + RESET, line)
        for idx, value in enumerate(strings):
            line = line.replace(f"\0s{idx}\0", value)
        for idx, value in enumerate(comments):
            line = line.replace(f"\0c{idx}\0", value)
        return line

    def _highlight_python_line(self, line: str) -> str:
        comments: list[str] = []

        def store_comment(match: re.Match[str]) -> str:
            comments.append(self._color("muted") + match.group(0) + RESET)
            return f"\0c{len(comments) - 1}\0"

        line = LINE_COMMENT_RE.sub(lambda m: m.group("prefix") + store_comment(re.match(r".*", m.group("comment"))), line)

        strings: list[str] = []

        def store_string(match: re.Match[str]) -> str:
            strings.append(self._color("json_string") + match.group(0) + RESET)
            return f"\0s{len(strings) - 1}\0"

        line = JSON_STRING_RE.sub(store_string, line)
        line = JSON_NUMBER_RE.sub(lambda m: self._color("json_number") + m.group(0) + RESET, line)
        line = PYTHON_DUNDER_RE.sub(lambda m: self._color("code_macro") + m.group(1) + RESET, line)
        line = PYTHON_FUNCTION_RE.sub(lambda m: self._color("code_function") + m.group(1) + RESET, line)
        line = PYTHON_TYPE_RE.sub(lambda m: self._color("code_type") + m.group(0) + RESET, line)
        line = PYTHON_KEYWORD_RE.sub(lambda m: self._color("code_keyword") + m.group(0) + RESET, line)
        for idx, value in enumerate(strings):
            line = line.replace(f"\0s{idx}\0", value)
        for idx, value in enumerate(comments):
            line = line.replace(f"\0c{idx}\0", value)
        return line

    def _highlight_cpp_line(self, line: str) -> str:
        comments: list[str] = []

        def store_comment(match: re.Match[str]) -> str:
            comments.append(self._color("muted") + match.group(0) + RESET)
            return f"\0C{len(comments) - 1}\0"

        line = BLOCK_COMMENT_RE.sub(store_comment, line)
        line = LINE_COMMENT_RE.sub(lambda m: m.group("prefix") + store_comment(re.match(r".*", m.group("comment"))), line)

        strings: list[str] = []

        def store_string(match: re.Match[str]) -> str:
            strings.append(self._color("json_string") + match.group(0) + RESET)
            return f"\0S{len(strings) - 1}\0"

        line = JSON_STRING_RE.sub(store_string, line)
        line = ANGLE_INCLUDE_RE.sub(lambda m: self._color("json_string") + m.group(0) + RESET, line)
        line = JSON_NUMBER_RE.sub(lambda m: self._color("json_number") + m.group(0) + RESET, line)
        line = CPP_PREPROCESSOR_RE.sub(lambda m: self._color("code_macro") + m.group(1) + RESET, line)
        line = CPP_STD_SYMBOL_RE.sub(lambda m: self._color("code_macro") + m.group(1) + RESET, line)
        line = CPP_FUNCTION_RE.sub(lambda m: self._color("code_function") + m.group(1) + RESET, line)
        line = CPP_TYPE_RE.sub(lambda m: self._color("code_type") + m.group(0) + RESET, line)
        line = CPP_KEYWORD_RE.sub(lambda m: self._color("code_keyword") + m.group(0) + RESET, line)
        for idx, value in enumerate(strings):
            line = line.replace(f"\0S{idx}\0", value)
        for idx, value in enumerate(comments):
            line = line.replace(f"\0C{idx}\0", value)
        return line

    def _highlight_php_line(self, line: str) -> str:
        comments: list[str] = []

        def store_comment(match: re.Match[str]) -> str:
            comments.append(self._color("muted") + match.group(0) + RESET)
            return f"\0c{len(comments) - 1}\0"

        line = BLOCK_COMMENT_RE.sub(store_comment, line)
        line = LINE_COMMENT_RE.sub(lambda m: m.group("prefix") + store_comment(re.match(r".*", m.group("comment"))), line)

        strings: list[str] = []

        def store_string(match: re.Match[str]) -> str:
            strings.append(self._color("json_string") + match.group(0) + RESET)
            return f"\0s{len(strings) - 1}\0"

        line = JSON_STRING_RE.sub(store_string, line)
        line = JSON_NUMBER_RE.sub(lambda m: self._color("json_number") + m.group(0) + RESET, line)
        line = PHP_TAG_RE.sub(lambda m: self._color("code_macro") + m.group(0) + RESET, line)
        line = PHP_VARIABLE_RE.sub(lambda m: self._color("code_macro") + m.group(1) + RESET, line)
        line = PHP_CONSTANT_RE.sub(lambda m: self._color("code_macro") + m.group(1) + RESET, line)
        line = PHP_FUNCTION_RE.sub(lambda m: self._color("code_function") + m.group(1) + RESET, line)
        line = PHP_TYPE_RE.sub(lambda m: self._color("code_type") + m.group(0) + RESET, line)
        line = PHP_KEYWORD_RE.sub(lambda m: self._color("code_keyword") + m.group(0) + RESET, line)
        for idx, value in enumerate(strings):
            line = line.replace(f"\0s{idx}\0", value)
        for idx, value in enumerate(comments):
            line = line.replace(f"\0c{idx}\0", value)
        return line

    def _highlight_html_line(self, line: str) -> str:
        line = HTML_COMMENT_RE.sub(lambda m: self._color("muted") + m.group(0) + RESET, line)

        def replace_tag(match: re.Match[str]) -> str:
            open_part, name, attrs, close_part = match.groups()
            rendered_attrs = HTML_ATTR_RE.sub(
                lambda attr: self._color("code_type") + attr.group(1) + RESET + attr.group(2) + self._color("json_string") + attr.group(3) + RESET,
                attrs,
            )
            return open_part + self._color("code_function") + name + RESET + rendered_attrs + close_part

        return HTML_TAG_RE.sub(replace_tag, line)

    def _highlight_shell_line(self, line: str) -> str:
        if line.lstrip().startswith("#"):
            return self._highlight_code_comments(line)

        strings: list[str] = []

        def store_string(match: re.Match[str]) -> str:
            strings.append(self._color("json_string") + match.group(0) + RESET)
            return f"\0s{len(strings) - 1}\0"

        line = JSON_STRING_RE.sub(store_string, line)
        line = SHELL_ASSIGN_RE.sub(lambda m: m.group(1) + self._color("code_macro") + m.group(2) + RESET + self._color("json_string") + m.group(3) + RESET, line)
        line = SHELL_COMMAND_RE.sub(lambda m: m.group(1) + self._color("code_type" if "/" in m.group(2) else "code_function") + m.group(2) + RESET, line)
        line = SHELL_MODULE_RE.sub(lambda m: self._color("code_type") + m.group(1) + RESET, line)
        line = SHELL_PATH_RE.sub(lambda m: self._color("code_type") + m.group(1) + RESET, line)
        line = SHELL_FLAG_RE.sub(lambda m: self._color("code_keyword") + m.group(1) + RESET, line)
        for idx, value in enumerate(strings):
            line = line.replace(f"\0s{idx}\0", value)
        return line

    def _code_line_style(self, text: str, default: str) -> str:
        stripped = text.lstrip()
        if stripped.startswith("- ") or stripped.startswith("-\t") or stripped == "-":
            return self._fg_bg("diff_remove_fg", "diff_remove_bg")
        if stripped.startswith("+ ") or stripped.startswith("+\t") or stripped == "+":
            return self._fg_bg("diff_add_fg", "diff_add_bg")
        return default

    def _render_list(self, tokens: list[Token], *, ordered: bool, source: Source | None, depth: int = 0) -> list[str]:
        lines: list[str] = []
        item_index = 1
        i = 0
        while i < len(tokens):
            if tokens[i].type == "list_item_open":
                end = self._find_matching(tokens, i)
                marker = f"{item_index}." if ordered else "•"
                marker_prefix = ("  " * depth) + marker
                item_text = self._render_inner(tokens[i + 1 : end], source=source, list_depth=depth + 1).strip()
                wrapped = wrap_rendered(item_text, max(10, self.options.width - visible_width(marker_prefix) - 1))
                for line_no, line in enumerate(wrapped or [""]):
                    prefix = marker_prefix if line_no == 0 else " " * visible_width(marker_prefix)
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
                output.append(self._render_text(token.content))
            elif token.type == "softbreak":
                output.append("\n")
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
            elif token.type == "s_open":
                end = self._find_inline_close(tokens, i, "s_close")
                output.append(ESC + "[9m" + self._render_inline(tokens[i + 1 : end], source=source) + ESC + "[29m")
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
        command = ["kitten", "icat", "--align", "left", "--transfer-mode", "detect", "--stdin", "no", str(path)]
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

    def _fg_bg(self, fg_name: str, bg_name: str) -> str:
        fg = hex_to_rgb(self.theme.colors.get(fg_name, "#ffffff"))
        bg = hex_to_rgb(self.theme.colors.get(bg_name, "#000000"))
        return f"{ESC}[38;2;{fg[0]};{fg[1]};{fg[2]}m{ESC}[48;2;{bg[0]};{bg[1]};{bg[2]}m"

    def _underline(self, name: str, *, style: int) -> str:
        color = hex_to_rgb(self.theme.colors.get(name, "#ffffff"))
        return f"{ESC}[58;2;{color[0]};{color[1]};{color[2]}m{ESC}[4:{style}m"

    def _link_style(self) -> str:
        color = hex_to_rgb(self.theme.colors.get("link", "#5fafff"))
        underline = hex_to_rgb(self.theme.colors.get("link_underline", "#5fafff"))
        return f"{ESC}[38;2;{color[0]};{color[1]};{color[2]}m{ESC}[58;2;{underline[0]};{underline[1]};{underline[2]}m{ESC}[4:1m"

    def _render_text(self, text: str) -> str:
        return render_text_features(
            text,
            checked_style=self._color("h4"),
            unchecked_style=self._color("muted"),
            date_style=self._color("date"),
            muted_style=self._color("muted"),
            major_number_style=self._color("number_major"),
            path_style=self._color("code_type"),
            link_style=self._link_style(),
        )


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


def render_text_features(
    text: str,
    *,
    checked_style: str,
    unchecked_style: str,
    date_style: str,
    muted_style: str,
    major_number_style: str,
    path_style: str,
    link_style: str,
) -> str:
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
        pieces.append(render_non_url_text(text[pos:start], checked_style, unchecked_style, date_style, muted_style, major_number_style, path_style))
        pieces.append(link_escape(url, url, link_style))
        pieces.append(render_non_url_text(trailing, checked_style, unchecked_style, date_style, muted_style, major_number_style, path_style))
        pos = match.end("url")
    pieces.append(render_non_url_text(text[pos:], checked_style, unchecked_style, date_style, muted_style, major_number_style, path_style))
    return "".join(pieces)


def render_non_url_text(
    text: str,
    checked_style: str,
    unchecked_style: str,
    date_style: str,
    muted_style: str,
    major_number_style: str,
    path_style: str,
) -> str:
    text = render_task_markers(text, checked_style, unchecked_style)
    text = colorize_dates(text, date_style)
    text = colorize_large_numbers(text, muted_style, major_number_style)
    return colorize_paths(text, path_style)


def render_task_markers(text: str, checked_style: str, unchecked_style: str) -> str:
    def replace(match: re.Match[str]) -> str:
        prefix = match.group("prefix")
        checked = match.group("mark").lower() == "x"
        if prefix.lstrip().startswith(("-", "*")):
            prefix = prefix.replace("-", "•", 1).replace("*", "•", 1)
        box = "✅" if checked else "⬜"
        style = checked_style if checked else unchecked_style
        return f"{prefix}{style}{box}{RESET} "

    return TASK_RE.sub(replace, text)


def colorize_dates(text: str, style: str) -> str:
    return DATE_RE.sub(lambda m: style + m.group(0) + RESET, text)


def colorize_large_numbers(text: str, muted_style: str, major_style: str) -> str:
    def replace(match: re.Match[str]) -> str:
        value = match.group(0)
        if len(value) > 6:
            millions = value[:-6]
            middle = value[-6:-3]
            last = value[-3:]
            return f"{major_style}{ESC}[1m{millions}{RESET}{middle}{muted_style}{last}{RESET}"
        return value[:-3] + muted_style + value[-3:] + RESET

    return LARGE_NUMBER_RE.sub(replace, text)


def colorize_paths(text: str, style: str) -> str:
    return TEXT_PATH_RE.sub(lambda m: style + m.group(1) + RESET, text)


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


def truncate_rendered(value: str, width: int) -> str:
    if visible_width(value) <= width:
        return value
    atoms = rendered_atoms(value)
    output: list[str] = []
    used = 0
    for atom, atom_width in atoms:
        if atom_width == 0:
            output.append(atom)
            continue
        if used + atom_width >= width:
            output.append("…")
            break
        output.append(atom)
        used += atom_width
    return "".join(output)


def fit_widths(raw_widths: list[int], available: int) -> list[int]:
    widths = raw_widths[:]
    if sum(widths) <= available:
        return widths
    minimum = 6
    while sum(widths) > available and max(widths) > minimum:
        idx = max(range(len(widths)), key=widths.__getitem__)
        widths[idx] -= 1
    return [max(3, width) for width in widths]
