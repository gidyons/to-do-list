/* ================================================================
   To-Do List — Frontend Logic
   ================================================================ */

const API = "/api";
let currentFilter = "all";
let currentLabel = null;
let editingId = null;

// ── DOM refs ──────────────────────────────────────────────────────
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const taskInput   = $("#taskInput");
const addBtn      = $("#addBtn");
const ocrInput    = $("#ocrInput");
const taskList    = $("#taskList");
const statusBar   = $("#statusBar");
const subtitle    = $("#subtitle");
const clearBtn    = $("#clearCompleted");
const sidebarNav  = $("#sidebarNav");
const themeToggle = $("#themeToggle");
const editModal   = $("#editModal");
const editInput   = $("#editInput");
const editLabel   = $("#editLabel");
const editSave    = $("#editSave");
const editCancel  = $("#editCancel");
const menuBtn     = $("#menuBtn");
const sidebar     = $("#sidebar");
const toasts      = $("#toasts");

const LABELS = ["Default", "Personal", "Shopping", "Wishlist", "Work", "Events", "Tasks", "Meetings"];
const EMPTY = {
    all:       "Nothing to do yet — type a task above and press Enter.",
    active:    "All caught up. Nice.",
    completed: "No completed tasks yet.",
};

// ── Init ──────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    buildSidebar();
    buildLabelOptions();
    bindEvents();
    refresh();
    setInterval(pollReminders, 30000);
});

// ── Theme ─────────────────────────────────────────────────────────
function initTheme() {
    const saved = localStorage.getItem("theme") || "light";
    document.documentElement.dataset.theme = saved;
    updateThemeLabel(saved);
}

function toggleTheme() {
    const next = document.documentElement.dataset.theme === "light" ? "dark" : "light";
    document.documentElement.dataset.theme = next;
    localStorage.setItem("theme", next);
    updateThemeLabel(next);
}

function updateThemeLabel(theme) {
    const span = themeToggle.querySelector("span:last-child");
    const icon = themeToggle.querySelector(".theme-icon");
    span.textContent = theme === "light" ? "Dark mode" : "Light mode";
    icon.textContent = theme === "light" ? "\u263E" : "\u2600";
}

// ── Sidebar ───────────────────────────────────────────────────────
function buildSidebar() {
    sidebarNav.innerHTML = "";
    const allBtn = makeNavBtn("All lists", null, currentLabel === null);
    sidebarNav.appendChild(allBtn);
    LABELS.forEach((label) => {
        sidebarNav.appendChild(makeNavBtn(label, label, currentLabel === label));
    });
}

function makeNavBtn(text, label, active) {
    const btn = document.createElement("button");
    btn.className = "nav-item" + (active ? " active" : "");
    btn.textContent = text;
    btn.addEventListener("click", () => {
        currentLabel = label;
        subtitle.textContent = label || "All lists";
        buildSidebar();
        refresh();
    });
    return btn;
}

// ── Events ────────────────────────────────────────────────────────
function bindEvents() {
    addBtn.addEventListener("click", addTask);
    taskInput.addEventListener("keydown", (e) => { if (e.key === "Enter") addTask(); });

    $$(".filter-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            $$(".filter-btn").forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");
            currentFilter = btn.dataset.filter;
            refresh();
        });
    });

    clearBtn.addEventListener("click", async () => {
        await api("POST", "/tasks/clear-completed");
        refresh();
    });

    themeToggle.addEventListener("click", toggleTheme);

    ocrInput.addEventListener("change", handleOCR);

    editSave.addEventListener("click", saveEdit);
    editCancel.addEventListener("click", () => { editModal.hidden = true; });
    editModal.addEventListener("click", (e) => { if (e.target === editModal) editModal.hidden = true; });
    editInput.addEventListener("keydown", (e) => { if (e.key === "Enter") saveEdit(); });

    menuBtn.addEventListener("click", () => { sidebar.classList.toggle("open"); });
}

// ── API helper ────────────────────────────────────────────────────
async function api(method, path, body) {
    const opts = { method, headers: {} };
    if (body !== undefined) {
        opts.headers["Content-Type"] = "application/json";
        opts.body = JSON.stringify(body);
    }
    const res = await fetch(API + path, opts);
    return res.json();
}

// ── Refresh ───────────────────────────────────────────────────────
async function refresh() {
    const params = new URLSearchParams({ filter: currentFilter });
    if (currentLabel) params.set("label", currentLabel);
    const tasks = await api("GET", "/tasks?" + params);

    taskList.innerHTML = "";
    if (tasks.length === 0) {
        taskList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">&#128221;</div>
                <p>${EMPTY[currentFilter]}</p>
            </div>`;
    } else {
        tasks.forEach((t) => taskList.appendChild(makeRow(t)));
    }

    const stats = await api("GET", "/stats");
    statusBar.textContent = `${stats.done} of ${stats.total} done`;
}

function makeRow(task) {
    const row = document.createElement("div");
    row.className = "task-row";

    const check = document.createElement("input");
    check.type = "checkbox";
    check.className = "task-check";
    check.checked = task.done;
    check.addEventListener("change", async () => {
        await api("PUT", `/tasks/${task.id}`, { done: check.checked });
        refresh();
    });

    const body = document.createElement("div");
    body.className = "task-body";

    const text = document.createElement("div");
    text.className = "task-text" + (task.done ? " done" : "");
    text.textContent = task.text;

    const label = document.createElement("span");
    label.className = "task-label";
    label.textContent = task.label;

    body.appendChild(text);
    if (task.label && task.label !== "Default") body.appendChild(label);

    body.addEventListener("dblclick", () => openEdit(task));

    const actions = document.createElement("div");
    actions.className = "task-actions";

    const editBtn = document.createElement("button");
    editBtn.className = "task-btn";
    editBtn.innerHTML = "&#9998;";
    editBtn.title = "Edit";
    editBtn.addEventListener("click", () => openEdit(task));

    const delBtn = document.createElement("button");
    delBtn.className = "task-btn delete";
    delBtn.innerHTML = "&#10005;";
    delBtn.title = "Delete";
    let animating = false;
    delBtn.addEventListener("click", async () => {
        if (animating) return;
        animating = true;
        row.style.opacity = "0";
        row.style.transform = "translateX(20px)";
        setTimeout(async () => {
            await api("DELETE", `/tasks/${task.id}`);
            refresh();
            animating = false;
        }, 150);
    });

    actions.appendChild(editBtn);
    actions.appendChild(delBtn);
    row.append(check, body, actions);
    return row;
}

// ── Add task ──────────────────────────────────────────────────────
async function addTask() {
    const text = taskInput.value.trim();
    if (!text) return;
    await api("POST", "/tasks", { text, label: currentLabel || "Default" });
    taskInput.value = "";
    taskInput.focus();
    refresh();
    toast("Task added", "success");
}

// ── Edit task ─────────────────────────────────────────────────────
function openEdit(task) {
    editingId = task.id;
    editInput.value = task.text;
    editLabel.value = task.label;
    editModal.hidden = false;
    editInput.focus();
    editInput.select();
}

async function saveEdit() {
    if (editingId === null) return;
    const text = editInput.value.trim();
    if (!text) return;
    await api("PUT", `/tasks/${editingId}`, { text, label: editLabel.value });
    editModal.hidden = true;
    editingId = null;
    refresh();
    toast("Task updated", "info");
}

function buildLabelOptions() {
    editLabel.innerHTML = "";
    LABELS.forEach((l) => {
        const opt = document.createElement("option");
        opt.value = l;
        opt.textContent = l;
        editLabel.appendChild(opt);
    });
}

// ── OCR ───────────────────────────────────────────────────────────
async function handleOCR(e) {
    const file = e.target.files[0];
    if (!file) return;

    const loading = document.createElement("div");
    loading.className = "ocr-loading";
    loading.innerHTML = '<div class="ocr-spinner"></div> Extracting text...';
    taskList.prepend(loading);

    const b64 = await fileToBase64(file);
    const result = await api("POST", "/ocr", { image: b64 });

    loading.remove();
    ocrInput.value = "";

    if (result.error) {
        toast("OCR failed: " + result.error, "error");
        return;
    }
    if (result.text) {
        taskInput.value = result.text;
        taskInput.focus();
        toast("Text extracted — press Enter to add", "success");
    } else {
        toast("No text found in image", "error");
    }
}

function fileToBase64(file) {
    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.readAsDataURL(file);
    });
}

// ── Reminders ─────────────────────────────────────────────────────
const shownReminders = new Set();
async function pollReminders() {
    const due = await api("GET", "/reminders");
    due.forEach((t) => {
        const key = t.id;
        if (!shownReminders.has(key)) {
            shownReminders.add(key);
            toast(`Reminder: ${t.text}`, "info");
            if ("Notification" in window && Notification.permission === "granted") {
                new Notification("To-Do Reminder", { body: t.text });
            }
        }
    });
    // Reset after a full cycle to allow re-notification
    setTimeout(() => shownReminders.clear(), 60000);
}

// ── Toast ─────────────────────────────────────────────────────────
function toast(msg, type = "info") {
    const el = document.createElement("div");
    el.className = `toast ${type}`;
    el.textContent = msg;
    toasts.appendChild(el);
    setTimeout(() => { el.style.opacity = "0"; setTimeout(() => el.remove(), 300); }, 3000);
}
