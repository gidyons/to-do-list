"""Tests for the to-do store. Run with ``python -m unittest``."""

import json
import tempfile
import unittest
from pathlib import Path

from todo import Task, TodoStore


class StoreTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "tasks.json"
        self.store = TodoStore(self.path)

    def tearDown(self):
        self._tmp.cleanup()

    def reload(self):
        """Return a fresh store reading the same file, to prove persistence."""
        return TodoStore(self.path)


class TestMutations(StoreTestCase):
    def test_add_assigns_increasing_ids(self):
        first = self.store.add("buy milk")
        second = self.store.add("walk dog")
        self.assertEqual((first.id, second.id), (1, 2))
        self.assertFalse(first.done)
        self.assertIsNotNone(first.created)

    def test_add_strips_whitespace(self):
        self.assertEqual(self.store.add("  tidy desk  ").text, "tidy desk")

    def test_add_rejects_blank_text(self):
        for text in ("", "   ", "\t\n"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.store.add(text)

    def test_toggle_flips_done(self):
        task = self.store.add("pay rent")
        self.assertTrue(self.store.toggle(task.id).done)
        self.assertFalse(self.store.toggle(task.id).done)

    def test_toggle_unknown_id_is_a_no_op(self):
        self.assertIsNone(self.store.toggle(999))

    def test_edit_renames_without_moving_task(self):
        first = self.store.add("one")
        self.store.add("two")
        self.store.edit(first.id, "  one (edited) ")
        self.assertEqual([task.text for task in self.store], ["one (edited)", "two"])
        self.assertEqual(self.store.get(first.id).text, "one (edited)")

    def test_edit_keeps_completion_state(self):
        task = self.store.add("one")
        self.store.toggle(task.id)
        self.assertTrue(self.store.edit(task.id, "one again").done)

    def test_edit_rejects_blank_text(self):
        task = self.store.add("one")
        with self.assertRaises(ValueError):
            self.store.edit(task.id, "   ")
        self.assertEqual(self.store.get(task.id).text, "one")

    def test_edit_unknown_id_is_a_no_op(self):
        self.assertIsNone(self.store.edit(42, "nope"))

    def test_remove_deletes_only_that_task(self):
        keep = self.store.add("keep")
        drop = self.store.add("drop")
        self.assertTrue(self.store.remove(drop.id))
        self.assertEqual([task.text for task in self.store], ["keep"])
        self.assertFalse(self.store.remove(drop.id))
        self.assertEqual(self.store.get(keep.id).text, "keep")

    def test_clear_completed_returns_count(self):
        a, b, c = (self.store.add(text) for text in ("a", "b", "c"))
        self.store.toggle(a.id)
        self.store.toggle(c.id)
        self.assertEqual(self.store.clear_completed(), 2)
        self.assertEqual([task.text for task in self.store], ["b"])
        self.assertEqual(self.store.clear_completed(), 0)
        self.assertIsNotNone(self.store.get(b.id))

    def test_ids_stay_unique_after_deletion(self):
        # Ids only have to be unique among the tasks that currently exist, so
        # removing the last task frees its id again.
        first = self.store.add("one")
        second = self.store.add("two")
        self.store.remove(first.id)
        third = self.store.add("three")
        self.assertNotIn(third.id, [task.id for task in self.store if task is not third])
        self.assertEqual(second.id, 2)


class TestQueries(StoreTestCase):
    def setUp(self):
        super().setUp()
        self.first = self.store.add("first")
        self.second = self.store.add("second")
        self.third = self.store.add("third")
        self.store.toggle(self.second.id)

    def test_filtered_all(self):
        self.assertEqual(len(self.store.filtered("all")), 3)

    def test_filtered_active(self):
        self.assertEqual([task.text for task in self.store.filtered("active")], ["first", "third"])

    def test_filtered_completed(self):
        self.assertEqual([task.text for task in self.store.filtered("completed")], ["second"])

    def test_filtered_defaults_to_all(self):
        self.assertEqual(len(self.store.filtered()), 3)

    def test_filtered_rejects_unknown_mode(self):
        with self.assertRaises(ValueError):
            self.store.filtered("later")

    def test_filtered_returns_a_copy(self):
        self.store.filtered("all").clear()
        self.assertEqual(len(self.store), 3)

    def test_counts_and_len(self):
        self.assertEqual(self.store.counts(), (1, 3))
        self.assertEqual(len(self.store), 3)


class TestPersistence(StoreTestCase):
    def test_save_and_reload_round_trip(self):
        task = self.store.add("persisted")
        self.store.toggle(task.id)
        self.store.save()

        reloaded = self.reload()
        self.assertEqual(len(reloaded), 1)
        self.assertEqual(reloaded.get(task.id).text, "persisted")
        self.assertTrue(reloaded.get(task.id).done)
        self.assertEqual(reloaded.get(task.id).created, task.created)

    def test_missing_file_loads_empty(self):
        self.assertEqual(len(TodoStore(self.path)), 0)
        self.assertFalse(self.path.exists())  # loading must not create the file

    def test_saved_file_is_human_readable_json(self):
        self.store.add("readable")
        self.store.save()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(data["tasks"][0]["text"], "readable")

    def test_save_creates_missing_directories(self):
        nested = Path(self._tmp.name) / "a" / "b" / "tasks.json"
        store = TodoStore(nested)
        store.add("deep")
        store.save()
        self.assertTrue(nested.exists())

    def test_corrupt_file_is_quarantined_not_overwritten(self):
        self.path.write_text("{not json", encoding="utf-8")
        store = TodoStore(self.path)  # should warn and start empty
        self.assertEqual(len(store), 0)
        backup = self.path.with_name(self.path.name + ".corrupt")
        self.assertTrue(backup.exists())
        self.assertEqual(backup.read_text(encoding="utf-8"), "{not json")

    def test_load_accepts_a_bare_task_list(self):
        self.path.write_text(json.dumps([{"id": 7, "text": "legacy"}]), encoding="utf-8")
        store = TodoStore(self.path)
        self.assertEqual([task.text for task in store], ["legacy"])

    def test_env_var_selects_the_file(self):
        import os
        from unittest import mock

        from todo import default_path

        with mock.patch.dict(os.environ, {"TODO_FILE": str(self.path)}):
            self.assertEqual(default_path(), self.path)


class TestTaskSerialisation(unittest.TestCase):
    def test_round_trip_through_dict(self):
        task = Task(id=3, text="hello", done=True, created="2026-01-02T03:04:05")
        self.assertEqual(Task.from_dict(task.to_dict()), task)

    def test_from_dict_fills_in_defaults(self):
        task = Task.from_dict({"id": "9", "text": "  padded  "})
        self.assertEqual(task.id, 9)
        self.assertEqual(task.text, "padded")
        self.assertFalse(task.done)
        self.assertTrue(task.created)


if __name__ == "__main__":
    unittest.main()
