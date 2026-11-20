"""A string-keyed hash table that resolves collisions with linked buckets."""


class HashTable:
    def __init__(self, initial_capacity: int = 8, max_load_factor: float = 0.75):
        if not isinstance(initial_capacity, int) or isinstance(initial_capacity, bool):
            raise TypeError("initial_capacity must be an integer")
        if initial_capacity < 1:
            raise ValueError("initial_capacity must be positive")
        if not isinstance(max_load_factor, (int, float)) or isinstance(max_load_factor, bool):
            raise TypeError("max_load_factor must be numeric")
        if max_load_factor <= 0:
            raise ValueError("max_load_factor must be positive")

        self._buckets = [[] for _ in range(initial_capacity)]
        self._size = 0
        self._max_load_factor = float(max_load_factor)

    @property
    def capacity(self) -> int:
        return len(self._buckets)

    @property
    def load_factor(self) -> float:
        return self._size / self.capacity

    @property
    def strategy_name(self) -> str:
        return "연결 리스트"

    def hash_index(self, key: str) -> int:
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        result = 0
        for character in key:
            result = (result * 31 + ord(character)) % self.capacity
        return result

    def put(self, key: str, value: str) -> None:
        index = self.hash_index(key)
        bucket = self._buckets[index]
        for position, (existing_key, _) in enumerate(bucket):
            if existing_key == key:
                bucket[position] = (key, value)
                return

        bucket.append((key, value))
        self._size += 1
        if self.load_factor > self._max_load_factor:
            self._resize(self.capacity * 2)

    def get(self, key: str) -> str:
        index = self.hash_index(key)
        for existing_key, value in self._buckets[index]:
            if existing_key == key:
                return value
        raise KeyError(key)

    def contains(self, key: str) -> bool:
        index = self.hash_index(key)
        for existing_key, _ in self._buckets[index]:
            if existing_key == key:
                return True
        return False

    def probe_count(self, key: str) -> int:
        index = self.hash_index(key)
        for probes, (existing_key, _) in enumerate(self._buckets[index], start=1):
            if existing_key == key:
                return probes
        return len(self._buckets[index])

    def items(self) -> tuple[tuple[str, str], ...]:
        return tuple(entry for bucket in self._buckets for entry in bucket)

    def slots(self) -> tuple[tuple[tuple[str, str], ...], ...]:
        return tuple(tuple(bucket) for bucket in self._buckets)

    def __len__(self) -> int:
        return self._size

    def _resize(self, new_capacity: int) -> None:
        old_items = self.items()
        self._buckets = [[] for _ in range(new_capacity)]
        for key, value in old_items:
            self._buckets[self.hash_index(key)].append((key, value))
