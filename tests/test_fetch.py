from __future__ import annotations

import unittest

from kitty_markdown_viewer.fetch import is_fetch_url


class FetchTests(unittest.TestCase):
    def test_is_fetch_url(self) -> None:
        self.assertTrue(is_fetch_url("https://example.com/readme.md"))
        self.assertTrue(is_fetch_url("http://example.com/readme.md"))
        self.assertFalse(is_fetch_url("ftp://example.com/readme.md"))
        self.assertFalse(is_fetch_url("README.md"))


if __name__ == "__main__":
    unittest.main()

