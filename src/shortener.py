"""URL shortening backed by the project's custom hash table."""

import csv
from pathlib import Path
from threading import RLock
from urllib.parse import urlsplit

from src.base62 import decode, encode
from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable

Table = HashTable | LinearProbingHashTable


class Shortener:
    def __init__(
        self,
        strategy: str = "chaining",
        storage_path: str | Path | None = None,
    ):
        if strategy == "chaining":
            table_factory = HashTable
        elif strategy == "linear":
            table_factory = LinearProbingHashTable
        else:
            raise ValueError("strategy must be 'chaining' or 'linear'")
        self._url_to_code = table_factory()
        self._code_to_url = table_factory()
        self._next_id = 1
        self._lock = RLock()
        self._storage_path = Path(storage_path) if storage_path is not None else None
        if self._storage_path is not None:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            self._load_saved_urls()

    @property
    def tables(self) -> tuple[Table, Table]:
        return self._url_to_code, self._code_to_url

    def shorten(self, url: str) -> str:
        if not isinstance(url, str):
            raise TypeError("url must be a string")
        normalized_url = url.strip()
        if not self._is_valid_url(normalized_url):
            raise ValueError("url must be an absolute HTTP or HTTPS URL")

        with self._lock:
            if self._url_to_code.contains(normalized_url):
                return self._url_to_code.get(normalized_url)

            code = encode(self._next_id)
            if self._storage_path is not None:
                with self._storage_path.open(
                    "a", encoding="utf-8", newline=""
                ) as storage_file:
                    csv.writer(storage_file).writerow((normalized_url, code))
            self._next_id += 1
            self._url_to_code.put(normalized_url, code)
            self._code_to_url.put(code, normalized_url)
            return code

    def expand(self, code: str) -> str:
        with self._lock:
            return self._code_to_url.get(code)

    def _load_saved_urls(self) -> None:
        if self._storage_path is None or not self._storage_path.exists():
            return

        with self._storage_path.open(
            "r", encoding="utf-8", newline=""
        ) as storage_file:
            for line_number, row in enumerate(csv.reader(storage_file), start=1):
                if len(row) != 2:
                    raise ValueError(
                        f"{self._storage_path}:{line_number}: expected URL and code"
                    )
                url, code = row
                if url != url.strip() or not self._is_valid_url(url):
                    raise ValueError(
                        f"{self._storage_path}:{line_number}: invalid URL"
                    )
                try:
                    identifier = decode(code)
                except ValueError as error:
                    raise ValueError(
                        f"{self._storage_path}:{line_number}: invalid short code"
                    ) from error
                if identifier < 1 or encode(identifier) != code:
                    raise ValueError(
                        f"{self._storage_path}:{line_number}: invalid short code"
                    )
                if self._url_to_code.contains(url) or self._code_to_url.contains(code):
                    raise ValueError(
                        f"{self._storage_path}:{line_number}: duplicate URL or code"
                    )
                self._url_to_code.put(url, code)
                self._code_to_url.put(code, url)
                self._next_id = max(self._next_id, identifier + 1)

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
