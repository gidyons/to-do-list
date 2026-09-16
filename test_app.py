"""Smoke tests for the Tkinter front-end.

These need a working display (or Xvfb) and the ``tkinter`` module; they are
skipped automatically when neither is available, so ``python -m unittest``
still passes on a headless box without Python's Tk bindings.
"""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from todo import TodoStore

try:
    import tkinter
    from tkinter import ttk

    _probe = tkinter.Tk()
    _probe.destroy()
    DISPLAY_REASON = None
except Exception as exc:  # ImportError, tkinter.TclError, ...
    tkinter = None
    DISPLAY_REASON = f"Tk is unavailable here ({exc.__class__.__name__}: {exc})"


@unittest.skipIf(DISPLAY_REASON, DISPLAY_REASON or "")
class GuiTestCase(unittest.TestCase):
    def setUp(self):
        from app import TodoApp

        self._tmp = tempfile.TemporaryDirectory()
        self.store = TodoStore(Path(self._tmp.name) / "tasks.json")
        self.app = TodoApp(store=self.store)
        self.app.update()

    def tearDown(self):
        try:
            self.app.destroy()
        except tkinter.TclError:
            pass  # a test already closed the window
        self._tmp.cleanup()

    def type_and_add(self, text):
        self.app.entry.insert(0, text)
        self.app._on_add()
        return self.store.tasks[-1]

    def body_children(self):
        """Everything drawn in the list area, including the empty-state label."""
        return self.app.list_view.body.winfo_children()

    def visible_texts(self):
        """Text of the task rows currently on screen."""
        return [
            child.cget("text")
            for row in self.body_children()
            for child in row.winfo_children()
            if isinstance(child, ttk.Label)
        ]


class TestAdding(GuiTestCase):
    def test_adding_a_task_saves_it_and_clears_the_entry(self):
        task = self.type_and_add("buy milk")
        self.assertEqual(task.text, "buy milk")
        self.assertEqual(self.app.entry.get(), "")
        self.assertTrue(self.store.path.exists())
        self.assertEqual(self.visible_texts(), ["buy milk"])

    def test_blank_input_is_ignored(self):
        self.type_and_add("   ")
        self.assertEqual(len(self.store), 0)
        self.assertEqual(self.visible_texts(), [])

    def test_starts_with_an_empty_state_message(self):
        (label,) = self.body_children()
        self.assertIsInstance(label, ttk.Label)
        self.assertIn("Nothing to do yet", label.cget("text"))

    def test_empty_state_message_follows_the_filter(self):
        self.app.filter_mode.set("completed")
        self.app.refresh()
        (label,) = self.body_children()
        self.assertIn("No completed tasks yet", label.cget("text"))


class TestTogglingAndFiltering(GuiTestCase):
    def setUp(self):
        super().setUp()
        self.first = self.type_and_add("first")
        self.second = self.type_and_add("second")

    def test_toggling_marks_done_and_persists(self):
        self.app._on_toggle(self.first.id)
        self.assertTrue(self.store.get(self.first.id).done)
        self.assertTrue(TodoStore(self.store.path).get(self.first.id).done)

    def test_filter_shows_only_matching_tasks(self):
        self.app._on_toggle(self.first.id)
        self.app.filter_mode.set("active")
        self.app.refresh()
        self.assertEqual(self.visible_texts(), ["second"])
        self.app.filter_mode.set("completed")
        self.app.refresh()
        self.assertEqual(self.visible_texts(), ["first"])

    def test_toggling_from_a_filtered_view_is_consistent(self):
        self.app.filter_mode.set("active")
        self.app.refresh()
        self.app._on_toggle(self.first.id)
        self.assertEqual(self.visible_texts(), ["second"])
        self.assertTrue(self.store.get(self.first.id).done)

    def test_status_line_reports_progress(self):
        self.app._on_toggle(self.first.id)
        self.assertIn("1 of 2 done", self.app.status.cget("text"))

    def test_clear_completed_button_empties_finished_tasks(self):
        self.app._on_toggle(self.first.id)
        self.app._on_toggle(self.second.id)
        self.app._on_clear_completed()
        self.assertEqual(len(self.store), 0)
        self.assertIn("0 of 0 done", self.app.status.cget("text"))


class TestEditingAndDeleting(GuiTestCase):
    def test_editing_renames_the_task(self):
        task = self.type_and_add("teh milk")
        with mock.patch("app.simpledialog.askstring", return_value="the milk"):
            self.app._on_edit(task.id)
        self.assertEqual(self.store.get(task.id).text, "the milk")
        self.assertEqual(self.visible_texts(), ["the milk"])

    def test_cancelling_an_edit_changes_nothing(self):
        task = self.type_and_add("teh milk")
        with mock.patch("app.simpledialog.askstring", return_value=None):
            self.app._on_edit(task.id)
        self.assertEqual(self.store.get(task.id).text, "teh milk")

    def test_blank_edit_is_rejected(self):
        task = self.type_and_add("keep me")
        with mock.patch("app.simpledialog.askstring", return_value="   "):
            self.app._on_edit(task.id)
        self.assertEqual(self.store.get(task.id).text, "keep me")

    def test_editing_an_unknown_task_does_not_open_a_dialog(self):
        with mock.patch("app.simpledialog.askstring") as ask:
            self.app._on_edit(999)
        ask.assert_not_called()

    def test_deleting_removes_the_row(self):
        first = self.type_and_add("first")
        self.type_and_add("second")
        self.app._on_delete(first.id)
        self.assertEqual(self.visible_texts(), ["second"])

    def test_closing_saves(self):
        self.type_and_add("write me down")
        self.app._on_close()
        self.assertEqual(TodoStore(self.store.path).tasks[0].text, "write me down")


class TestRenderingWithPreloadedTasks(GuiTestCase):
    def test_existing_tasks_are_shown_on_start_up(self):
        from app import TodoApp

        self.store.add("from a previous session")
        second = TodoApp(store=self.store)
        try:
            second.update()
            self.assertEqual(
                [task.text for task in self.store],
                ["from a previous session"],
            )
            self.assertEqual(len(second.list_view.body.winfo_children()), 1)
        finally:
            second.destroy()


if __name__ == "__main__":
    unittest.main()
