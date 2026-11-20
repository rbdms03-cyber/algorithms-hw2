"""A string-keyed hash table that resolves collisions with linear probing."""


class LinearProbingHashTable:
    def __init__(self, initial_capacity: int = 8, max_load_factor: float = 0.75):
        if not isinstance(initial_capacity, int) or isinstance(initial_capacity, bool):
            raise TypeError("initial_capacity must be an integer")
        if initial_capacity < 1:
            raise ValueError("initial_capacity must be positive")
        if not isinstance(max_load_factor, (int, float)) or isinstance(max_load_factor, bool):
            raise TypeError("max_load_factor must be numeric")
        if not 0 < max_load_factor <= 1:
            raise ValueError("max_load_factor must be greater than 0 and at most 1")

        self._slots: list[tuple[str, str] | None] = [None] * initial_capacity
        self._size = 0
        self._max_load_factor = float(max_load_factor)

    @property
    def capacity(self) -> int:
        return len(self._slots)

    @property
    def load_factor(self) -> float:
        return self._size / self.capacity

    @property
    def strategy_name(self) -> str:
        return "선형 탐지"

    def hash_index(self, key: str) -> int:
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        result = 0
        for character in key:
            result = (result * 31 + ord(character)) % self.capacity
        return result

    def put(self, key: str, value: str) -> None:
        index = self.hash_index(key)
        for offset in range(self.capacity):
            position = (index + offset) % self.capacity
            entry = self._slots[position]
            if entry is None:
                self._slots[position] = (key, value)
                self._size += 1
                if self.load_factor > self._max_load_factor:
                    self._resize(self.capacity * 2)
                return
            if entry[0] == key:
                self._slots[position] = (key, value)
                return

        self._resize(self.capacity * 2)
        self.put(key, value)

    def get(self, key: str) -> str:
        index = self.hash_index(key)
        for offset in range(self.capacity):
            position = (index + offset) % self.capacity
            entry = self._slots[position]
            if entry is None:
                break
            if entry[0] == key:
                return entry[1]
        raise KeyError(key)

    def contains(self, key: str) -> bool:
        index = self.hash_index(key)
        for offset in range(self.capacity):
            position = (index + offset) % self.capacity
            entry = self._slots[position]
            if entry is None:
                return False
            if entry[0] == key:
                return True
        return False

    def probe_count(self, key: str) -> int:
        index = self.hash_index(key)
        for offset in range(self.capacity):
            position = (index + offset) % self.capacity
            entry = self._slots[position]
            if entry is None or entry[0] == key:
                return offset + 1
        return self.capacity

    def probe_path(self, key: str) -> tuple[int, ...]:
        index = self.hash_index(key)
        visited = []
        for offset in range(self.capacity):
            position = (index + offset) % self.capacity
            visited.append(position)
            entry = self._slots[position]
            if entry is None or entry[0] == key:
                break
        return tuple(visited)

    def items(self) -> tuple[tuple[str, str], ...]:
        return tuple(entry for entry in self._slots if entry is not None)

    def slots(self) -> tuple[tuple[tuple[str, str], ...], ...]:
        return tuple(() if entry is None else (entry,) for entry in self._slots)

    def __len__(self) -> int:
        return self._size

    def _resize(self, new_capacity: int) -> None:
        old_items = self.items()
        self._slots = [None] * new_capacity
        self._size = 0
        for key, value in old_items:
            self._insert_without_resize(key, value)

    def _insert_without_resize(self, key: str, value: str) -> None:
        index = self.hash_index(key)
        for offset in range(self.capacity):
            position = (index + offset) % self.capacity
            if self._slots[position] is None:
                self._slots[position] = (key, value)
                self._size += 1
                return
        raise RuntimeError("resized table has no free slot")
