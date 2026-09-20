"""A small desktop to-do list built with Tkinter.

Run it with::

    python app.py

Tasks are stored in ``~/.todo_tasks.json`` (override with the ``TODO_FILE``
environment variable). The window offers adding, completing, editing,
deleting and filtering tasks; every change is written to disk immediately.
"""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from tkinter import simpledialog, ttk

from todo import FILTERS, Task, TodoStore

FILTER_LABELS = {"all": "All", "active": "Active", "completed": "Completed"}
EMPTY_MESSAGES = {
    "all": "Nothing to do yet — type a task above and press Enter.",
    "active": "All caught up. Nice.",
    "completed": "No completed tasks yet.",
}


class ScrollableList(ttk.Frame):
    """A vertically scrolling frame that rows are rebuilt inside of."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        # Match the canvas to the theme so rows don't sit on a white rectangle.
        background = ttk.Style(self).lookup("TFrame", "background") or self.cget("background")
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0, background=background)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.body = ttk.Frame(self.canvas)  # rows are added here
        self._window = self.canvas.create_window((0, 0), window=self.body, anchor="nw")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.body.bind("<Configure>", self._on_body_resize)
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.canvas.bind_all(sequence, self._on_wheel)

    def _on_body_resize(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_resize(self, event: tk.Event) -> None:
        # Keep rows as wide as the visible canvas.
        self.canvas.itemconfigure(self._window, width=event.width)

    def _on_wheel(self, event: tk.Event) -> None:
        """Scroll with the wheel, but only while the pointer is over the list."""
        widget = self.winfo_containing(event.x_root, event.y_root)
        if widget is None:
            return
        own_path, widget_path = str(self), str(widget)
        if widget_path != own_path and not widget_path.startswith(own_path + "."):
            return
        if event.num == 4:
            step = -1
        elif event.num == 5:
            step = 1
        else:  # Windows / macOS report a delta instead of button numbers
            step = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(step, "units")

    def clear(self) -> None:
        """Remove every row; the caller rebuilds the ones it wants to show."""
        for child in self.body.winfo_children():
            child.destroy()


class TodoApp(tk.Tk):
    """Main application window."""

    def __init__(self, store: TodoStore | None = None) -> None:
        super().__init__()
        self.store = store or TodoStore()
        self.filter_mode = tk.StringVar(value="all")
        # Tk only stores the *name* of a variable, so the Python objects behind
        # the row checkbuttons must be kept alive here or they get collected.
        self._row_vars: dict[int, tk.BooleanVar] = {}

        self.title("My To-Do List")
        self.minsize(500, 600)
        self.geometry("600x700")

        self.bg_color = "#FFF5F7"
        self.card_color = "#FFFFFF"
        self.text_color = "#4A3038"
        self.muted_color = "#9A7A83"
        self.accent_color = "#D96C8A"

        self.configure(background=self.bg_color)

        base = tkfont.nametofont("TkDefaultFont").copy()
        base.configure(size=11)
        self.font_active = base
        self.font_done = base.copy()
        self.font_done.configure(overstrike=True)
        self.font_muted = base.copy()
        self.font_muted.configure(size=9)

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_area()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.refresh()
        self.after_idle(self.entry.focus_set)

    # ------------------------------------------------------------------ layout
    
    # sidebar
    def _build_sidebar(self) -> None:
        sidebar = tk.Frame(
            self,
            bg=self.card_color,
            width=200
        )
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)

        menu_button = tk.Button(
            sidebar,
            text="☰",
            font=("Arial", 16),
            bg=self.card_color,
            fg=self.text_color,
            relief="flat",
            borderwidth=0
        )
        menu_button.pack(
            anchor="w",
            padx=20,
            pady=(20, 25)
        )

        all_lists = tk.Label(
            sidebar,
            text="⌂  All lists",
            font=("Arial", 12, "bold"),
            bg=self.card_color,
            fg=self.text_color,
            anchor="w"
        )
        all_lists.pack(
            fill="x",
            padx=20,
            pady=(0, 20)
        )

        categories = [
            "Default",
            "Personal",
            "Shopping",
            "Wishlist",
            "Work",
            "Finished"
        ]

        for category in categories:
            item = tk.Label(
                sidebar,
                text=f"   {category}",
                font=("Arial", 11),
                bg=self.card_color,
                fg=self.text_color,
                anchor="w"
            )
            item.pack(
                fill="x",
                padx=20,
                pady=7
            )

        spacer = tk.Frame(
            sidebar,
            bg=self.card_color
        )
        spacer.pack(fill="both", expand=True)

        settings = tk.Label(
            sidebar,
            text="⚙  Settings",
            font=("Arial", 11),
            bg=self.card_color,
            fg=self.text_color,
            anchor="w"
        )
        settings.pack(
            fill="x",
            padx=20,
            pady=20
        )

    # main area
    def _build_main_area(self) -> None:
        main = tk.Frame(
            self,
            bg=self.bg_color
        )
        main.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=25,
            pady=20
        )

        main.columnconfigure(0, weight=1)
        main.rowconfigure(3, weight=1)
        main.rowconfigure(4, weight=0)

        # -----------------------------
        # Title
        # -----------------------------
        title = tk.Label(
            main,
            text="TASKS",
            font=("Arial", 20, "bold"),
            bg=self.bg_color,
            fg=self.text_color,
            anchor="w"
        )
        title.grid(
            row=0,
            column=0,
            sticky="w"
        )

        # -----------------------------
        # Subtitle
        # -----------------------------
        subtitle = tk.Label(
            main,
            text="All lists",
            font=("Arial", 11),
            bg=self.bg_color,
            fg=self.muted_color,
            anchor="w"
        )
        subtitle.grid(
            row=1,
            column=0,
            sticky="w",
            pady=(5, 15)
        )

        # -----------------------------
        # Add task area
        # -----------------------------
        input_frame = tk.Frame(
            main,
            bg=self.card_color,
            height=55
        )
        input_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(0, 15)
        )
        input_frame.grid_propagate(False)

        input_frame.columnconfigure(0, weight=1)
        input_frame.columnconfigure(1, weight=0)

        # Task input
        self.entry = tk.Entry(
            input_frame,
            font=("Arial", 11),
            bg=self.card_color,
            fg=self.text_color,
            relief="flat",
            borderwidth=0
        )
        self.entry.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(15, 5),
            pady=10
        )

        self.entry.bind("<Return>", self._on_add)

        # Add task button
        add_task_button = tk.Button(
            input_frame,
            text="ADD TASK",
            font=("Arial", 10, "bold"),
            bg=self.accent_color,
            fg="white",
            relief="flat",
            borderwidth=0,
            padx=15,
            pady=8,
            command=self._on_add
        )
        add_task_button.grid(
            row=0,
            column=1,
            padx=(5, 10),
            pady=8
        )

        # -----------------------------
        # Task list
        # -----------------------------
        self._build_list_in_main(main)

        # -----------------------------
        # Status
        # -----------------------------
        self.status = tk.Label(
            main,
            font=("Arial", 9),
            bg=self.bg_color,
            fg=self.muted_color,
            anchor="w"
        )
        self.status.grid(
            row=4,
            column=0,
            sticky="ew",
            pady=(10, 0)
        )

    def _build_list_in_main(self, main) -> None:
        self.list_view = ScrollableList(main)
        self.list_view.grid(
            row=3,
            column=0,
            sticky="nsew"
        )

    def _build_header(self) -> None:
        header = ttk.Frame(self, padding=(12, 12, 12, 6))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        self.entry = ttk.Entry(header, font=self.font_active)
        self.entry.grid(row=0, column=0, sticky="ew")
        self.entry.bind("<Return>", self._on_add)

        ttk.Button(header, text="Add", command=self._on_add).grid(row=0, column=1, padx=(6, 0))

    def _build_toolbar(self) -> None:
        toolbar = ttk.Frame(self, padding=(12, 0, 12, 6))
        toolbar.grid(row=1, column=0, sticky="ew")
        toolbar.columnconfigure(len(FILTERS), weight=1)

        for column, mode in enumerate(FILTERS):
            ttk.Radiobutton(
                toolbar,
                text=FILTER_LABELS[mode],
                value=mode,
                variable=self.filter_mode,
                command=self.refresh,
            ).grid(row=0, column=column, sticky="w", padx=(0, 6))

        self.clear_button = ttk.Button(
            toolbar, text="Clear completed", command=self._on_clear_completed
        )
        self.clear_button.grid(row=0, column=len(FILTERS), sticky="e")

    def _build_list_in_main(self, main) -> None:
        self.list_view = ScrollableList(main)
        self.list_view.grid(
            row=3,
            column=0,
            sticky="nsew"
    )
    
    def _build_status(self) -> None:
        self.status = ttk.Label(self, font=self.font_muted, anchor="w", padding=(12, 6))
        self.status.grid(row=3, column=0, sticky="ew")

    # ------------------------------------------------------------------ rendering

    def refresh(self) -> None:
        """Redraw the list from the store and update the status line."""
        self.list_view.clear()
        self._row_vars.clear()
        tasks = self.store.filtered(self.filter_mode.get())

        if tasks:
            for task in tasks:
                self._add_row(task)
        else:
            ttk.Label(
                self.list_view.body,
                text=EMPTY_MESSAGES[self.filter_mode.get()],
                font=self.font_muted,
                padding=16,
            ).pack(fill="x")

        done, total = self.store.counts()
        shown = f"  ·  showing {len(tasks)}" if self.filter_mode.get() != "all" else ""
        self.status.configure(text=f"{done} of {total} done{shown}  ·  saved to {self.store.path}")

    def _add_row(self, task: Task) -> None:
        row = ttk.Frame(self.list_view.body, padding=(6, 4))
        row.pack(fill="x", expand=True)
        row.columnconfigure(1, weight=1)

        variable = tk.BooleanVar(value=task.done)
        self._row_vars[task.id] = variable
        ttk.Checkbutton(
            row,
            variable=variable,
            command=lambda task_id=task.id: self._on_toggle(task_id),
        ).grid(row=0, column=0, padx=(0, 6))

        label = ttk.Label(
            row,
            text=task.text,
            font=self.font_done if task.done else self.font_active,
            anchor="w",
        )
        label.grid(row=0, column=1, sticky="ew")
        label.bind("<Double-Button-1>", lambda _event, task_id=task.id: self._on_edit(task_id))

        ttk.Button(
            row,
            text="✕",
            width=3,
            command=lambda task_id=task.id: self._on_delete(task_id),
        ).grid(row=0, column=2, padx=(6, 0))

    # ------------------------------------------------------------------ actions

    def _on_add(self, _event: tk.Event | None = None) -> None:
        text = self.entry.get()
        if not text.strip():
            return
        self.store.add(text)
        self.entry.delete(0, tk.END)
        self._commit()

    def _on_toggle(self, task_id: int) -> None:
        self.store.toggle(task_id)
        self._commit()

    def _on_edit(self, task_id: int) -> None:
        task = self.store.get(task_id)
        if task is None:
            return
        new_text = simpledialog.askstring("Edit task", "Task:", initialvalue=task.text, parent=self)
        if new_text is None or new_text.strip() == task.text:
            return
        try:
            self.store.edit(task_id, new_text)
        except ValueError:
            return
        self._commit()

    def _on_delete(self, task_id: int) -> None:
        self.store.remove(task_id)
        self._commit()

    def _on_clear_completed(self) -> None:
        if self.store.clear_completed():
            self._commit()

    def _commit(self) -> None:
        """Persist and redraw after any change."""
        self.store.save()
        self.refresh()

    def _on_close(self) -> None:
        try:
            self.store.save()
        finally:
            self.destroy()


def main() -> None:
    TodoApp().mainloop()


if __name__ == "__main__":
    main()
