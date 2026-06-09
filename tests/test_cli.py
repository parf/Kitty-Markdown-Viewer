from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path
import io
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from kitty_markdown_viewer.cli import main


class CliTests(unittest.TestCase):
    def test_cli_file_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            md = root / "doc.md"
            md.write_text("# Hello\n", encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = main(["--config", str(root / "config.toml"), "--schema", "dark", str(md)])
            self.assertEqual(code, 0)
            self.assertIn("\x1b]66;s=4;Hello\x07", stdout.getvalue())

    def test_cli_dash_stdin(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stdout = io.StringIO()
            with mock.patch.object(sys, "stdin", io.StringIO("# From stdin\n")):
                with redirect_stdout(stdout):
                    code = main(["--config", str(root / "config.toml"), "--schema", "dark", "-"])
            self.assertEqual(code, 0)
            self.assertIn("From stdin", stdout.getvalue())

    def test_cli_no_args_tty_shows_help(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stdout = io.StringIO()
            stdin = io.StringIO("")
            stdin.isatty = lambda: True  # type: ignore[method-assign]
            with mock.patch.object(sys, "stdin", stdin):
                with redirect_stdout(stdout):
                    code = main(["--config", str(root / "config.toml")])
            self.assertEqual(code, 0)
            self.assertIn("usage: cat-md", stdout.getvalue())

    def test_cli_pages_interactive_stdout_by_default(self) -> None:
        class TtyStdout(io.StringIO):
            def isatty(self) -> bool:
                return True

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            md = root / "doc.md"
            md.write_text("# Hello\n", encoding="utf-8")
            stdout = TtyStdout()
            process = mock.Mock()
            process.communicate.return_value = ("", "")
            with mock.patch.object(sys, "stdout", stdout):
                with mock.patch("kitty_markdown_viewer.cli.subprocess.Popen", return_value=process) as popen:
                    code = main(["--config", str(root / "config.toml"), "--schema", "dark", str(md)])
        self.assertEqual(code, 0)
        popen.assert_called_once_with(["less", "-r"], stdin=subprocess.PIPE, text=True)
        self.assertIn("\x1b]66;s=4;Hello\x07", process.communicate.call_args.args[0])
        self.assertEqual(stdout.getvalue(), "")

    def test_cli_no_pager_writes_to_interactive_stdout(self) -> None:
        class TtyStdout(io.StringIO):
            def isatty(self) -> bool:
                return True

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            md = root / "doc.md"
            md.write_text("# Hello\n", encoding="utf-8")
            stdout = TtyStdout()
            with mock.patch.object(sys, "stdout", stdout):
                with mock.patch("kitty_markdown_viewer.cli.subprocess.Popen") as popen:
                    code = main(["--config", str(root / "config.toml"), "--schema", "dark", "--no-pager", str(md)])
        self.assertEqual(code, 0)
        popen.assert_not_called()
        self.assertIn("\x1b]66;s=4;Hello\x07", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
