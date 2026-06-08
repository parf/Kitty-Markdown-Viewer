#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys
import zipapp


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build" / "zipapp"
DIST = ROOT / "dist"
DEPENDENCIES = [
    "markdown-it-py>=3",
    "requests>=2",
    "wcwidth>=0.2",
]


def main() -> int:
    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--target",
            str(BUILD),
            "--upgrade",
            "--no-compile",
            *DEPENDENCIES,
        ],
        check=True,
    )
    shutil.copytree(ROOT / "src" / "kitty_markdown_viewer", BUILD / "kitty_markdown_viewer")
    (BUILD / "__main__.py").write_text(
        "from kitty_markdown_viewer.cli import main\nraise SystemExit(main())\n",
        encoding="utf-8",
    )
    DIST.mkdir(exist_ok=True)
    zipapp.create_archive(BUILD, target=DIST / "kitty-md", interpreter="/usr/bin/env python3")
    (DIST / "kitty-md").chmod(0o755)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
