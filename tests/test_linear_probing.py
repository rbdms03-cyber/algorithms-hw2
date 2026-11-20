import unittest

from src.linear_probing import LinearProbingHashTable


class LinearProbingTests(unittest.TestCase):
    def test_wraps_from_last_slot_to_zero(self):
        table = LinearProbingHashTable(initial_capacity=4, max_load_factor=1.0)
        keys = [f"key-{number}" for number in range(100)]
        home_last_slot = next(key for key in keys if table.hash_index(key) == 3)
        second_key = next(
            key
            for key in keys
            if key != home_last_slot and table.hash_index(key) == 3
        )

        table.put(home_last_slot, "last")
        table.put(second_key, "wrapped")
        self.assertEqual(table.slots()[3], ((home_last_slot, "last"),))
        self.assertEqual(table.slots()[0], ((second_key, "wrapped"),))
        self.assertEqual(table.get(second_key), "wrapped")
        self.assertEqual(table.probe_path(second_key), (3, 0))

    def test_full_table_lookup_terminates_and_new_item_grows(self):
        table = LinearProbingHashTable(initial_capacity=3, max_load_factor=1.0)
        for number in range(3):
            table.put(f"key-{number}", str(number))

        self.assertEqual(len(table), 3)
        table.put("key-0", "updated")
        self.assertEqual(table.capacity, 3)
        self.assertEqual(table.get("key-0"), "updated")
        self.assertEqual(table.probe_count("missing"), 3)
        self.assertFalse(table.contains("missing"))
        with self.assertRaises(KeyError):
            table.get("missing")

        table.put("extra", "value")
        self.assertGreater(table.capacity, 3)
        self.assertEqual(table.get("extra"), "value")
        for number in range(3):
            expected = "updated" if number == 0 else str(number)
            self.assertEqual(table.get(f"key-{number}"), expected)

    def test_resize_and_overwrite_preserve_public_interface(self):
        table = LinearProbingHashTable(initial_capacity=4)
        for number in range(4):
            table.put(f"key-{number}", str(number))
        capacity_after_resize = table.capacity
        table.put("key-0", "updated")

        self.assertGreater(capacity_after_resize, 4)
        self.assertEqual(table.get("key-0"), "updated")
        self.assertEqual(len(table), 4)
        self.assertTrue(table.contains("key-3"))
        self.assertEqual(sum(bool(slot) for slot in table.slots()), len(table))


if __name__ == "__main__":
    unittest.main()
