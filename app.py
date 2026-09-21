"""Flask web application for the To-Do list.

Run with::

    python app.py

The server exposes a REST API for task CRUD and serves the single-page frontend.
OCR image-to-text conversion is handled via Tesseract.
"""

from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from PIL import Image
import pytesseract

from todo import FILTERS, Task, TodoStore

app = Flask(__name__)
store = TodoStore()

LABELS = ["Default", "Personal", "Shopping", "Wishlist", "Work", "Events", "Tasks", "Meetings"]


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# REST API — Tasks
# ---------------------------------------------------------------------------

@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    mode = request.args.get("filter", "all")
    label = request.args.get("label", None)
    tasks = store.filtered(mode, label)
    return jsonify([t.to_dict() for t in tasks])


VALID_LABELS = set(LABELS)

@app.route("/api/tasks", methods=["POST"])
def create_task():
    data = request.get_json(force=True)
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Task text is required"}), 400
    label = data.get("label", "Default")
    if label not in VALID_LABELS:
        label = "Default"
    reminder = data.get("reminder")
    task = store.add(text, label=label, reminder=reminder)
    return jsonify(task.to_dict()), 201


@app.route("/api/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id: int):
    task = store.get(task_id)
    if task is None:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task.to_dict())


@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id: int):
    data = request.get_json(force=True)
    task = store.get(task_id)
    if task is None:
        return jsonify({"error": "Task not found"}), 404
    if "text" in data:
        store.edit(task_id, data["text"])
    if "done" in data:
        if bool(data["done"]) != task.done:
            store.toggle(task_id)
    if "label" in data:
        label = data["label"]
        if label in VALID_LABELS:
            store.update_label(task_id, label)
        else:
            store.update_label(task_id, "Default")
    if "reminder" in data:
        store.update_reminder(task_id, data["reminder"])
    return jsonify(store.get(task_id).to_dict())


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id: int):
    if store.remove(task_id):
        return jsonify({"ok": True})
    return jsonify({"error": "Task not found"}), 404


@app.route("/api/tasks/clear-completed", methods=["POST"])
def clear_completed():
    store.clear_completed()
    return jsonify({"ok": True})


@app.route("/api/stats", methods=["GET"])
def stats():
    done, total = store.counts()
    label_counts = {}
    for label in LABELS:
        label_counts[label] = len(store.filtered("all", label))
    return jsonify({"done": done, "total": total, "labels": LABELS, "label_counts": label_counts})


# ---------------------------------------------------------------------------
# OCR — Image to Text
# ---------------------------------------------------------------------------

@app.route("/api/ocr", methods=["POST"])
def ocr_extract():
    data = request.get_json(force=True)
    image_b64 = data.get("image")
    if not image_b64:
        return jsonify({"error": "No image data provided"}), 400

    try:
        if "," in image_b64:
            image_b64 = image_b64.split(",", 1)[1]
        img_bytes = base64.b64decode(image_b64)
        if len(img_bytes) > 2 * 1024 * 1024:
            return jsonify({"error": "Image too large (max 2MB)"}), 400
        img = Image.open(__import__("io").BytesIO(img_bytes))
        text = pytesseract.image_to_string(img).strip()
        return jsonify({"text": text})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Reminders — check for due reminders
# ---------------------------------------------------------------------------

@app.route("/api/reminders", methods=["GET"])
def check_reminders():
    due = store.get_due_reminders()
    return jsonify([t.to_dict() for t in due])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
