"""Storage layer for the to-do list app.

Tasks live in a small JSON file so the GUI stays a thin layer on top of a
plain Python model that can also be used (and tested) on its own, with no
display attached.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

DEFAULT_FILENAME = ".todo_tasks.json"
#: Valid values for :meth:`TodoStore.filtered`.
FILTERS = ("all", "active", "completed")


def default_path() -> Path:
    """Return the JSON file to use, honouring the ``TODO_FILE`` env var."""
    override = os.environ.get("TODO_FILE")
    if override:
        return Path(override).expanduser()
    return Path.home() / DEFAULT_FILENAME


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass
class Task:
    """A single to-do item."""

    id: int
    text: str
    done: bool = False
    created: str = field(default_factory=_now)

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            id=int(data["id"]),
            text=str(data.get("text", "")).strip(),
            done=bool(data.get("done", False)),
            created=str(data.get("created") or _now()),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "done": self.done,
            "created": self.created,
        }


class TodoStore:
    """An in-memory task list backed by a JSON file."""

    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        self.path = Path(path) if path is not None else default_path()
        self.tasks: list[Task] = []
        self.load()

    # ------------------------------------------------------------------ load/save

    def load(self) -> None:
        """Read tasks from disk, starting empty if there is nothing to read."""
        self.tasks = []
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            items = raw["tasks"] if isinstance(raw, dict) else raw
            self.tasks = [Task.from_dict(item) for item in items]
        except (json.JSONDecodeError, OSError, TypeError, KeyError, ValueError) as exc:
            self._quarantine(exc)

    def save(self) -> None:
        """Write tasks to disk atomically, so a crash can't truncate the file."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "tasks": [task.to_dict() for task in self.tasks]}
        handle, tmp_name = tempfile.mkstemp(dir=self.path.parent, prefix=".todo-", suffix=".tmp")
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as stream:
                json.dump(payload, stream, indent=2, ensure_ascii=False)
                stream.write("\n")
            os.replace(tmp_name, self.path)
        except OSError:
            Path(tmp_name).unlink(missing_ok=True)
            raise

    def _quarantine(self, exc: Exception) -> None:
        """Move an unreadable file aside rather than silently overwriting it."""
        backup = self.path.with_name(self.path.name + ".corrupt")
        try:
            os.replace(self.path, backup)
        except OSError:
            backup = None
        print(f"Warning: could not read {self.path} ({exc}).", file=sys.stderr)
        if backup:
            print(f"The damaged file was moved to {backup}.", file=sys.stderr)

    # ------------------------------------------------------------------ queries

    def __len__(self) -> int:
        return len(self.tasks)

    def __iter__(self):
        return iter(self.tasks)

    def get(self, task_id: int) -> Task | None:
        return next((task for task in self.tasks if task.id == task_id), None)

    def filtered(self, mode: str = "all") -> list[Task]:
        """Return unfinished, finished, or all tasks in creation order."""
        if mode not in FILTERS:
            raise ValueError(f"unknown filter {mode!r}; expected one of {FILTERS}")
        if mode == "active":
            return [task for task in self.tasks if not task.done]
        if mode == "completed":
            return [task for task in self.tasks if task.done]
        return list(self.tasks)

    def counts(self) -> tuple[int, int]:
        """Return ``(completed, total)`` task counts."""
        return sum(task.done for task in self.tasks), len(self.tasks)

    def _next_id(self) -> int:
        return max((task.id for task in self.tasks), default=0) + 1

    # ------------------------------------------------------------------ mutations

    def add(self, text: str) -> Task:
        """Append a task. Blank text is rejected."""
        text = text.strip()
        if not text:
            raise ValueError("a task needs some text")
        task = Task(id=self._next_id(), text=text)
        self.tasks.append(task)
        return task

    def edit(self, task_id: int, text: str) -> Task | None:
        """Rename a task, keeping its position and completion state."""
        text = text.strip()
        if not text:
            raise ValueError("a task needs some text")
        task = self.get(task_id)
        if task is not None:
            task.text = text
        return task

    def toggle(self, task_id: int) -> Task | None:
        """Flip a task between done and not done."""
        task = self.get(task_id)
        if task is not None:
            task.done = not task.done
        return task

    def remove(self, task_id: int) -> bool:
        """Delete a task, reporting whether anything was removed."""
        remaining = [task for task in self.tasks if task.id != task_id]
        if len(remaining) == len(self.tasks):
            return False
        self.tasks = remaining
        return True

    def clear_completed(self) -> int:
        """Delete every finished task and return how many were removed."""
        before = len(self.tasks)
        self.tasks = [task for task in self.tasks if not task.done]
        return before - len(self.tasks)
