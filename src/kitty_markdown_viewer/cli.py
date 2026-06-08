from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
import sys

from .config import ensure_defaults, load_config
from .fetch import fetch_markdown, is_fetch_url
from .renderer import MarkdownRenderer, Source
from .themes import resolve_theme


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kitty-md", description="Render Markdown with kitty terminal features.")
    parser.add_argument("inputs", nargs="*", help="Markdown file, URL, or '-' for stdin.")
    parser.add_argument("--width", type=int, help="Render width in terminal cells.")
    parser.add_argument("--schema", "--theme", choices=["detect", "dark", "light"], dest="schema", help="Theme schema.")
    parser.add_argument("--config", type=Path, help="Config file path.")
    parser.add_argument("--init-config", action="store_true", help="Create default config/theme files and exit; refuses to overwrite.")
    parser.add_argument("--table-style", choices=["unicode", "plain"], help="Table style.")
    parser.add_argument("--image-width", type=int, help="Maximum image width in terminal cells.")
    parser.add_argument("--image-height", type=int, help="Maximum image height in terminal cells.")
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
            print(f"kitty-md: {exc}", file=sys.stderr)
            return 1
        return 0

    config = load_config(args.config)
    if args.table_style:
        config = replace(config, table_style=args.table_style)
    if args.image_width is not None:
        config = replace(config, image_max_width=args.image_width)
    if args.image_height is not None:
        config = replace(config, image_max_height=args.image_height)
    theme = resolve_theme(config, args.schema)
    renderer = MarkdownRenderer(config, theme, width=args.width)

    try:
        for text, source in read_inputs(args.inputs, config.fetch_timeout_seconds):
            sys.stdout.write(renderer.render(text, source=source))
    except Exception as exc:
        print(f"kitty-md: {exc}", file=sys.stderr)
        return 1
    return 0


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


if __name__ == "__main__":
    raise SystemExit(main())
