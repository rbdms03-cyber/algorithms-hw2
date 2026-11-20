"""URL shortening backed by the project's custom hash table."""

from urllib.parse import urlsplit

from src.base62 import encode
from src.hash_table import HashTable


class Shortener:
    def __init__(self):
        self._url_to_code = HashTable()
        self._code_to_url = HashTable()
        self._next_id = 1

    @property
    def tables(self) -> tuple[HashTable, HashTable]:
        return self._url_to_code, self._code_to_url

    def shorten(self, url: str) -> str:
        if not isinstance(url, str):
            raise TypeError("url must be a string")
        normalized_url = url.strip()
        if not self._is_valid_url(normalized_url):
            raise ValueError("url must be an absolute HTTP or HTTPS URL")

        if self._url_to_code.contains(normalized_url):
            return self._url_to_code.get(normalized_url)

        code = encode(self._next_id)
        self._next_id += 1
        self._url_to_code.put(normalized_url, code)
        self._code_to_url.put(code, normalized_url)
        return code

    def expand(self, code: str) -> str:
        return self._code_to_url.get(code)

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        if not url:
            return False
        if any(ord(character) < 32 or ord(character) == 127 for character in url):
            return False
        try:
            parts = urlsplit(url)
            hostname = parts.hostname
            parts.port
        except ValueError:
            return False
        return parts.scheme.lower() in ("http", "https") and bool(hostname)
