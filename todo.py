"""Core to-do list data model and persistence layer."""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

FILTERS = ("all", "active", "completed")

DEFAULT_FILE = Path.home() / ".todo_tasks.json"


@dataclass
class Task:
    id: int
    text: str
    done: bool = False
    label: str = "Default"
    created_at: float = field(default_factory=time.time)
    completed_at: float | None = None
    duration_minutes: float | None = None
    reminder: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class TodoStore:
    """JSON-file-backed task store with CRUD and filtering."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else Path(os.environ.get("TODO_FILE", str(DEFAULT_FILE)))
        self._tasks: list[Task] = []
        self._next_id: int = 1
        self.load()

    def load(self) -> None:
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
            except (json.JSONDecodeError, OSError):
                data = {"tasks": [], "next_id": 1}
            self._tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
            self._next_id = data.get("next_id", max((t.id for t in self._tasks), default=0) + 1)
        else:
            self._tasks = []
            self._next_id = 1

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(
                {"tasks": [t.to_dict() for t in self._tasks], "next_id": self._next_id},
                fh,
                indent=2,
                ensure_ascii=False,
            )

    def add(
        self,
        text: str,
        label: str = "Default",
        reminder: float | None = None,
        duration_minutes: float | None = None,
    ) -> Task:
        task = Task(
            id=self._next_id,
            text=text.strip(),
            label=label,
            reminder=reminder,
            duration_minutes=duration_minutes,
        )
        self._next_id += 1
        self._tasks.append(task)
        self.save()
        return task

    def add_many(self, texts: list[str], label: str = "Default") -> list[Task]:
        tasks = []
        for text in texts:
            t = text.strip()
            if not t:
                continue
            task = Task(id=self._next_id, text=t, label=label)
            self._next_id += 1
            self._tasks.append(task)
            tasks.append(task)
        if tasks:
            self.save()
        return tasks

    def get(self, task_id: int) -> Task | None:
        for t in self._tasks:
            if t.id == task_id:
                return t
        return None

    def edit(self, task_id: int, text: str) -> None:
        task = self.get(task_id)
        if task is None:
            raise ValueError(f"No task with id {task_id}")
        task.text = text.strip()
        self.save()

    def toggle(self, task_id: int) -> None:
        task = self.get(task_id)
        if task is not None:
            task.done = not task.done
            task.completed_at = time.time() if task.done else None
            self.save()

    def remove(self, task_id: int) -> bool:
        task = self.get(task_id)
        if task is None:
            return False
        self._tasks = [t for t in self._tasks if t.id != task_id]
        self.save()
        return True

    def clear_completed(self) -> bool:
        before = len(self._tasks)
        self._tasks = [t for t in self._tasks if not t.done]
        if len(self._tasks) < before:
            self.save()
            return True
        return False

    def update_label(self, task_id: int, label: str) -> None:
        task = self.get(task_id)
        if task is None:
            raise ValueError(f"No task with id {task_id}")
        task.label = label
        self.save()

    def update_reminder(self, task_id: int, reminder: float | None) -> None:
        task = self.get(task_id)
        if task is None:
            raise ValueError(f"No task with id {task_id}")
        task.reminder = reminder
        self.save()

    def update_duration(self, task_id: int, duration_minutes: float | None) -> None:
        task = self.get(task_id)
        if task is None:
            raise ValueError(f"No task with id {task_id}")
        task.duration_minutes = duration_minutes
        self.save()

    def filtered(self, mode: str = "all", label: str | None = None) -> list[Task]:
        tasks = self._tasks
        if mode == "active":
            tasks = [t for t in tasks if not t.done]
        elif mode == "completed":
            tasks = [t for t in tasks if t.done]
        if label and label != "Default":
            tasks = [t for t in tasks if t.label == label]
        return tasks

    def counts(self) -> tuple[int, int]:
        done = sum(1 for t in self._tasks if t.done)
        return done, len(self._tasks)

    def search(self, query: str) -> list[Task]:
        q = query.lower().strip()
        return [t for t in self._tasks if q in t.text.lower()]

    def get_due_reminders(self) -> list[Task]:
        now = time.time()
        return [t for t in self._tasks if t.reminder is not None and t.reminder <= now and not t.done]

    def all_tasks(self) -> list[Task]:
        return list(self._tasks)
