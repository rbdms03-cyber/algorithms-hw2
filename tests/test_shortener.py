from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from src.shortener import Shortener


class ShortenerTests(unittest.TestCase):
    def test_shortens_expands_and_reuses_same_url(self):
        shortener = Shortener()
        first_code = shortener.shorten("https://example.com/a")
        self.assertEqual(first_code, "1")
        self.assertEqual(shortener.expand(first_code), "https://example.com/a")
        self.assertEqual(shortener.shorten("https://example.com/a"), first_code)

    def test_trims_url_and_rejects_invalid_url(self):
        shortener = Shortener()
        code = shortener.shorten("  https://example.com/path  ")
        self.assertEqual(shortener.expand(code), "https://example.com/path")

        for url in (
            "",
            "ftp://example.com",
            "https:///missing-host",
            "not a URL",
            "https://example.com/\r\nX-Injected: yes",
        ):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    shortener.shorten(url)

    def test_unknown_code_raises_key_error(self):
        with self.assertRaises(KeyError):
            Shortener().expand("unknown")

    def test_both_collision_strategies_share_shortener_behavior(self):
        for strategy in ("chaining", "linear"):
            with self.subTest(strategy=strategy):
                shortener = Shortener(strategy=strategy)
                first_url = "  https://example.com/a  "
                first_code = shortener.shorten(first_url)
                second_url = "https://example.com/b"
                second_code = shortener.shorten(second_url)

                self.assertEqual(first_code, "1")
                self.assertEqual(shortener.expand(first_code), first_url.strip())
                self.assertEqual(shortener.shorten(first_url), first_code)
                self.assertNotEqual(first_code, second_code)
                self.assertEqual(shortener.expand(second_code), second_url)

                with self.assertRaises(ValueError):
                    shortener.shorten("ftp://example.com")
                with self.assertRaises(KeyError):
                    shortener.expand("missing")

    def test_strategy_choice_is_distinct_and_keeps_shared_codes(self):
        shortener = Shortener(strategy="linear")
        url = "https://example.com/selected"

        linear_code = shortener.shorten(url, "linear")
        self.assertEqual(shortener.shorten(url, "chaining"), linear_code)
        chaining_table = shortener.tables_for("chaining")[0]
        linear_table = shortener.tables_for("linear")[0]
        self.assertEqual(chaining_table.strategy_name, "연결 리스트")
        self.assertEqual(linear_table.strategy_name, "선형 탐지")

        next_code = shortener.shorten("https://example.com/chaining", "chaining")
        self.assertEqual(chaining_table.get("https://example.com/chaining"), next_code)
        self.assertEqual(linear_table.get("https://example.com/chaining"), next_code)
        with self.assertRaises(ValueError):
            shortener.shorten("https://example.com/invalid", "unknown")

    def test_saved_urls_survive_restart_and_strategy_change(self):
        with TemporaryDirectory() as directory:
            storage_path = Path(directory) / "urls.csv"
            original = Shortener(storage_path=storage_path)
            first_url = "https://example.com/previous"
            first_code = original.shorten(first_url)
            second_url = "https://example.com/also-previous"
            second_code = original.shorten(second_url)

            restarted = Shortener(strategy="linear", storage_path=storage_path)

            self.assertEqual(restarted.expand(first_code), first_url)
            self.assertEqual(restarted.expand(second_code), second_url)
            self.assertEqual(restarted.shorten(first_url), first_code)
            self.assertEqual(restarted.shorten(second_url, "chaining"), second_code)
            self.assertEqual(
                restarted.shorten("https://example.com/new"),
                "3",
            )


if __name__ == "__main__":
    unittest.main()
