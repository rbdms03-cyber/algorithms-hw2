import unittest

from src.base62 import decode, encode


class Base62Tests(unittest.TestCase):
    def test_zero_and_alphabet_boundaries(self):
        self.assertEqual(encode(0), "0")
        self.assertEqual(encode(61), "Z")
        self.assertEqual(encode(62), "10")

    def test_round_trip_large_integers(self):
        for number in (1, 35, 36, 61, 62, 3844, 2**128):
            with self.subTest(number=number):
                self.assertEqual(decode(encode(number)), number)

    def test_decode_is_case_sensitive(self):
        self.assertEqual(decode("a"), 10)
        self.assertEqual(decode("A"), 36)

    def test_rejects_invalid_values(self):
        for number in (-1, True):
            with self.subTest(number=number):
                with self.assertRaises((TypeError, ValueError)):
                    encode(number)

        for code in ("", "a-", "é"):
            with self.subTest(code=code):
                with self.assertRaises(ValueError):
                    decode(code)

        with self.assertRaises(TypeError):
            decode(1)


if __name__ == "__main__":
    unittest.main()
