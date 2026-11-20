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


if __name__ == "__main__":
    unittest.main()
