from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
import shlex
import subprocess
import sys

from .config import ensure_defaults, load_config
from .fetch import fetch_markdown, is_fetch_url
from .renderer import MarkdownRenderer, Source
from .themes import resolve_theme


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cat-md", description="Render Markdown with kitty terminal features.")
    parser.add_argument("inputs", nargs="*", help="Markdown file, URL, or '-' for stdin.")
    parser.add_argument("--width", type=int, help="Render width in terminal cells.")
    parser.add_argument("--schema", "--theme", choices=["detect", "dark", "light"], dest="schema", help="Theme schema.")
    parser.add_argument("--config", type=Path, help="Config file path.")
    parser.add_argument("--init-config", action="store_true", help="Create default config/theme files and exit; refuses to overwrite.")
    parser.add_argument("--table-style", choices=["unicode", "plain"], help="Table style.")
    pager = parser.add_mutually_exclusive_group()
    pager.add_argument("--pager", action="store_true", dest="pager", help="Page output when stdout is a terminal.")
    pager.add_argument("--no-pager", action="store_false", dest="pager", help="Write directly to stdout.")
    parser.add_argument("--pager-command", help='Pager command. Default: "less -r".')
    parser.set_defaults(pager=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.inputs and sys.stdin.isatty():
        parser.print_help()
        return 0
    if args.init_config:
        try:
            ensure_defaults(args.config, refuse_existing=True)
        except FileExistsError as exc:
            print(f"cat-md: {exc}", file=sys.stderr)
            return 1
        return 0

    config = load_config(args.config)
    if args.table_style:
        config = replace(config, table_style=args.table_style)
    if args.pager is not None:
        config = replace(config, pager=args.pager)
    if args.pager_command:
        config = replace(config, pager_command=args.pager_command)
    theme = resolve_theme(config, args.schema)
    renderer = MarkdownRenderer(config, theme, width=args.width)

    try:
        chunks: list[str] = []
        for text, source in read_inputs(args.inputs, config.fetch_timeout_seconds):
            chunks.append(renderer.render(text, source=source))
        return write_output("".join(chunks), config)
    except Exception as exc:
        print(f"cat-md: {exc}", file=sys.stderr)
        return 1


def read_inputs(inputs: list[str], timeout: float):
    if not inputs:
        yield sys.stdin.read(), Source()
        return
    for item in inputs:
        if item == "-":
            yield sys.stdin.read(), Source()
        elif is_fetch_url(item):
            fetched = fetch_markdown(item, timeout=timeout)
            yield fetched.text, Source(url=fetched.source_url)
        else:
            path = Path(item).expanduser()
            yield path.read_text(encoding="utf-8"), Source(path=path)


def write_output(output: str, config) -> int:
    if not config.pager or not is_stdout_tty():
        sys.stdout.write(output)
        return 0

    command = shlex.split(config.pager_command)
    if not command:
        sys.stdout.write(output)
        return 0
    try:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, text=True)
        process.communicate(output)
    except (BrokenPipeError, OSError):
        sys.stdout.write(output)
    return 0


def is_stdout_tty() -> bool:
    isatty = getattr(sys.stdout, "isatty", None)
    return bool(isatty and isatty())


if __name__ == "__main__":
    raise SystemExit(main())
