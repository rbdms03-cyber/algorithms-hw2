import unittest

from src.hash_table import HashTable


class HashTableTests(unittest.TestCase):
    def test_collisions_overwrite_and_missing_key(self):
        table = HashTable(initial_capacity=4)
        colliding_keys = [f"key-{number}" for number in range(100)]
        first_key = colliding_keys[0]
        second_key = next(
            key
            for key in colliding_keys[1:]
            if table.hash_index(key) == table.hash_index(first_key)
        )

        table.put(first_key, "first")
        table.put(second_key, "second")
        self.assertEqual(table.get(first_key), "first")
        self.assertEqual(table.get(second_key), "second")
        self.assertTrue(table.contains(first_key))
        self.assertFalse(table.contains("missing"))
        self.assertEqual(len(table), 2)

        table.put(first_key, "updated")
        self.assertEqual(table.get(first_key), "updated")
        self.assertEqual(len(table), 2)
        with self.assertRaises(KeyError):
            table.get("missing")

    def test_resize_preserves_entries_and_grows_capacity(self):
        table = HashTable(initial_capacity=4)
        for number in range(4):
            table.put(f"key-{number}", str(number))

        self.assertGreater(table.capacity, 4)
        self.assertEqual(len(table), 4)
        for number in range(4):
            self.assertEqual(table.get(f"key-{number}"), str(number))

    def test_empty_table_and_slots_snapshot(self):
        table = HashTable(initial_capacity=3)
        self.assertEqual(len(table), 0)
        self.assertEqual(table.load_factor, 0)
        self.assertEqual(len(table.slots()), table.capacity)
        table.put("key", "value")
        self.assertEqual(sum(len(bucket) for bucket in table.slots()), 1)

    def test_rejects_non_string_key(self):
        table = HashTable()
        with self.assertRaises(TypeError):
            table.put(1, "value")
        with self.assertRaises(TypeError):
            table.get(1)


if __name__ == "__main__":
    unittest.main()
