# To-Do List

A small desktop to-do list written in Python with Tkinter. No third-party
packages — just the standard library.

## Running it

```bash
python3 app.py
```

Tkinter ships with Python on Windows and macOS. On Debian/Ubuntu you may need
to install it first:

```bash
sudo apt install python3-tk
```

## What it does

- **Add** a task by typing and pressing Enter (or clicking *Add*).
- **Complete** a task with its checkbox — finished tasks are crossed out.
- **Edit** a task by double-clicking its text.
- **Delete** a task with the ✕ button, or remove all finished ones with
  *Clear completed*.
- **Filter** between All / Active / Completed tasks.
- The status line shows progress and where the tasks are stored.

Every change is saved immediately, so closing the window never loses work.

## Where tasks live

Tasks are stored as JSON in `~/.todo_tasks.json`:

```json
{
  "version": 1,
  "tasks": [
    { "id": 1, "text": "buy milk", "done": false, "created": "2026-09-16T10:30:00" }
  ]
}
```

Point the app at a different file with the `TODO_FILE` environment variable:

```bash
TODO_FILE=./work-tasks.json python3 app.py
```

Saves are atomic (written to a temporary file, then moved into place), so an
interrupted write can't truncate your list. If the file is ever unreadable,
the app moves it to `~/.todo_tasks.json.corrupt` and starts fresh rather than
overwriting it.

## Code layout

| File | Purpose |
| --- | --- |
| `todo.py` | `Task` and `TodoStore` — the data model and JSON persistence. No UI, so it runs anywhere. |
| `app.py` | The Tkinter window. Renders the store and turns clicks into store calls. |
| `test_todo.py` | Tests for the store. |
| `test_app.py` | Smoke tests that drive the real window; skipped when there's no display. |

## Tests

```bash
python3 -m unittest
```
