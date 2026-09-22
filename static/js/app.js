/* ================================================================
   To-Do — Frontend Logic
   ================================================================ */

const API = "/api";
let currentFilter = "all";
let currentLabel = null;
let editingId = null;
let pendingDuration = null;

// ── DOM refs ──────────────────────────────────────────────────────
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const landing       = $("#landing");
const landingEnter  = $("#landingEnter");
const appShell      = $("#appShell");
const taskInput     = $("#taskInput");
const addBtn        = $("#addBtn");
const ocrInput      = $("#ocrInput");
const taskList      = $("#taskList");
const statusBar     = $("#statusBar");
const subtitle      = $("#subtitle");
const taskCountBadge= $("#taskCountBadge");
const clearBtn      = $("#clearCompleted");
const sidebarNav    = $("#sidebarNav");
const hamburger     = $("#hamburger");
const sidebar       = $("#sidebar");
const sidebarOverlay= $("#sidebarOverlay");
const themeSelect   = $("#themeSelect");
const modeToggle    = $("#modeToggle");
const inputLabelSelect = $("#inputLabelSelect");
const durationBtn   = $("#durationBtn");
const durationLabel = $("#durationLabel");
const durationModal = $("#durationModal");
const durationInput = $("#durationInput");
const durationCancel= $("#durationCancel");
const durationSave  = $("#durationSave");
const editModal     = $("#editModal");
const editInput     = $("#editInput");
const editLabel     = $("#editLabel");
const editDuration  = $("#editDuration");
const editSave      = $("#editSave");
const editCancel    = $("#editCancel");
const ocrModal      = $("#ocrModal");
const ocrTaskList   = $("#ocrTaskList");
const ocrLabel      = $("#ocrLabel");
const ocrCancel     = $("#ocrCancel");
const ocrAddSelected= $("#ocrAddSelected");
const toasts        = $("#toasts");

const LABELS = ["Default", "Personal", "Shopping", "Wishlist", "Work", "Events", "Tasks", "Meetings"];
const PALETTES = ["blush", "ocean", "forest", "sunset", "lavender", "midnight"];
const EMPTY = {
    all:       "Your task list is empty. Add something above.",
    active:    "Everything is done. Well played.",
    completed: "No completed tasks yet.",
};

// ── Init ──────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    initLanding();
    initTheme();
    initPalette();
    buildSidebar();
    buildLabelOptions();
    bindEvents();
    refresh();
    setInterval(pollReminders, 30000);
    registerSW();
});

// ── Landing ───────────────────────────────────────────────────────
function initLanding() {
    const seen = localStorage.getItem("landing_seen");
    if (seen) {
        landing.style.display = "none";
        appShell.hidden = false;
        return;
    }
    landingEnter.addEventListener("click", () => {
        localStorage.setItem("landing_seen", "1");
        landing.classList.add("exiting");
        setTimeout(() => {
            landing.style.display = "none";
            appShell.hidden = false;
        }, 500);
    });
}

// ── PWA ───────────────────────────────────────────────────────────
function registerSW() {
    if ("serviceWorker" in navigator) {
        navigator.serviceWorker.register("/static/sw.js").catch(() => {});
    }
}

// ── Theme (light/dark) ───────────────────────────────────────────
function initTheme() {
    const saved = localStorage.getItem("theme") || "light";
    document.documentElement.dataset.theme = saved;
}

function toggleTheme() {
    const next = document.documentElement.dataset.theme === "light" ? "dark" : "light";
    document.documentElement.dataset.theme = next;
    localStorage.setItem("theme", next);
}

// ── Palette ───────────────────────────────────────────────────────
function initPalette() {
    const saved = localStorage.getItem("palette") || "blush";
    document.documentElement.dataset.palette = saved;
    if (themeSelect) themeSelect.value = saved;
}

function setPalette(name) {
    document.documentElement.dataset.palette = name;
    localStorage.setItem("palette", name);
}

// ── Sidebar ───────────────────────────────────────────────────────
function buildSidebar() {
    sidebarNav.innerHTML = "";

    const sectionLabel = document.createElement("h3");
    sectionLabel.className = "sidebar-section-title";
    sectionLabel.textContent = "Lists";
    sidebarNav.appendChild(sectionLabel);

    const allBtn = makeNavBtn("All tasks", null, currentLabel === null);
    sidebarNav.appendChild(allBtn);
    LABELS.forEach((label) => {
        sidebarNav.appendChild(makeNavBtn(label, label, currentLabel === label));
    });
}

function makeNavBtn(text, label, active) {
    const btn = document.createElement("button");
    btn.className = "nav-item" + (active ? " active" : "");

    const dot = document.createElement("span");
    dot.className = "nav-dot";

    const span = document.createElement("span");
    span.textContent = text;

    btn.append(dot, span);
    btn.addEventListener("click", () => {
        currentLabel = label;
        subtitle.textContent = label || "All tasks";
        buildSidebar();
        refresh();
        closeSidebar();
    });
    return btn;
}

function openSidebar() {
    sidebar.classList.add("open");
    sidebarOverlay.classList.add("active");
}
function closeSidebar() {
    sidebar.classList.remove("open");
    sidebarOverlay.classList.remove("active");
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
        toast("Completed tasks cleared", "info");
    });

    hamburger.addEventListener("click", openSidebar);
    sidebarOverlay.addEventListener("click", closeSidebar);

    if (themeSelect) {
        themeSelect.addEventListener("change", () => setPalette(themeSelect.value));
    }
    modeToggle.addEventListener("click", toggleTheme);

    ocrInput.addEventListener("change", handleOCR);

    // Duration modal
    durationBtn.addEventListener("click", () => {
        durationModal.hidden = false;
        durationInput.value = pendingDuration || "";
        $$(".dur-preset").forEach(b => b.classList.remove("selected"));
        durationInput.focus();
    });
    durationCancel.addEventListener("click", () => { durationModal.hidden = true; });
    durationModal.addEventListener("click", (e) => { if (e.target === durationModal) durationModal.hidden = true; });
    $$(".dur-preset").forEach((btn) => {
        btn.addEventListener("click", () => {
            $$(".dur-preset").forEach(b => b.classList.remove("selected"));
            btn.classList.add("selected");
            durationInput.value = btn.dataset.min;
        });
    });
    durationInput.addEventListener("input", () => {
        $$(".dur-preset").forEach(b => {
            b.classList.toggle("selected", b.dataset.min === durationInput.value);
        });
    });
    durationSave.addEventListener("click", () => {
        const val = parseInt(durationInput.value);
        if (val > 0) {
            pendingDuration = val;
            durationLabel.textContent = val >= 60 ? `${val/60}h` : `${val}m`;
            durationBtn.classList.add("has-value");
        } else {
            pendingDuration = null;
            durationLabel.textContent = "Duration";
            durationBtn.classList.remove("has-value");
        }
        durationModal.hidden = true;
    });

    // Edit modal
    editSave.addEventListener("click", saveEdit);
    editCancel.addEventListener("click", () => { editModal.hidden = true; });
    editModal.addEventListener("click", (e) => { if (e.target === editModal) editModal.hidden = true; });
    editInput.addEventListener("keydown", (e) => { if (e.key === "Enter") saveEdit(); });

    // OCR modal
    ocrCancel.addEventListener("click", () => { ocrModal.hidden = true; });
    ocrModal.addEventListener("click", (e) => { if (e.target === ocrModal) ocrModal.hidden = true; });
    ocrAddSelected.addEventListener("click", addOCRSelected);
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
    taskCountBadge.textContent = stats.total;
    statusBar.querySelector(".status-text").textContent =
        `${stats.done} of ${stats.total} done`;
}

// ── Task Row ──────────────────────────────────────────────────────
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

    const meta = document.createElement("div");
    meta.className = "task-meta";

    if (task.label && task.label !== "Default") {
        const label = document.createElement("span");
        label.className = "task-label";
        label.textContent = task.label;
        meta.appendChild(label);
    }

    if (task.duration_minutes) {
        const dur = document.createElement("span");
        dur.className = "task-duration";
        const mins = task.duration_minutes;
        dur.textContent = mins >= 60 ? `${mins/60}h` : `${mins}m`;
        meta.appendChild(dur);
    }

    if (task.created_at) {
        const time = document.createElement("span");
        time.className = "task-time";
        time.textContent = formatTimeAgo(task.created_at);
        meta.appendChild(time);
    }

    body.appendChild(text);
    if (meta.children.length > 0) body.appendChild(meta);

    body.addEventListener("dblclick", () => openEdit(task));

    const actions = document.createElement("div");
    actions.className = "task-actions";

    const editBtn = document.createElement("button");
    editBtn.className = "task-btn";
    editBtn.title = "Edit";
    editBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>';
    editBtn.addEventListener("click", () => openEdit(task));

    const delBtn = document.createElement("button");
    delBtn.className = "task-btn delete";
    delBtn.title = "Delete";
    delBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>';
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

    actions.append(editBtn, delBtn);
    row.append(check, body, actions);
    return row;
}

// ── Add task ──────────────────────────────────────────────────────
async function addTask() {
    const text = taskInput.value.trim();
    if (!text) return;
    const body = { text, label: inputLabelSelect.value || "Default" };
    if (pendingDuration) body.duration_minutes = pendingDuration;
    await api("POST", "/tasks", body);
    taskInput.value = "";
    pendingDuration = null;
    durationLabel.textContent = "Duration";
    durationBtn.classList.remove("has-value");
    taskInput.focus();
    refresh();
    toast("Task added", "success");
}

// ── Edit task ─────────────────────────────────────────────────────
function openEdit(task) {
    editingId = task.id;
    editInput.value = task.text;
    editLabel.value = task.label;
    editDuration.value = task.duration_minutes || "";
    editModal.hidden = false;
    editInput.focus();
    editInput.select();
}

async function saveEdit() {
    if (editingId === null) return;
    const text = editInput.value.trim();
    if (!text) return;
    const body = { text, label: editLabel.value };
    const dur = parseInt(editDuration.value);
    if (dur > 0) body.duration_minutes = dur;
    else body.duration_minutes = null;
    await api("PUT", `/tasks/${editingId}`, body);
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

    const lines = result.lines || [];
    if (lines.length === 0) {
        toast("No text found in image", "error");
        return;
    }

    if (lines.length === 1) {
        taskInput.value = lines[0];
        taskInput.focus();
        toast("Text extracted — press Enter to add", "success");
    } else {
        showOCRModal(lines);
    }
}

function showOCRModal(lines) {
    ocrTaskList.innerHTML = "";
    lines.forEach((line, i) => {
        const item = document.createElement("div");
        item.className = "ocr-task-item";

        const check = document.createElement("input");
        check.type = "checkbox";
        check.id = `ocr-${i}`;
        check.checked = true;

        const label = document.createElement("label");
        label.htmlFor = `ocr-${i}`;
        label.textContent = line;

        item.append(check, label);
        ocrTaskList.appendChild(item);
    });
    ocrModal.hidden = false;
}

async function addOCRSelected() {
    const checks = ocrTaskList.querySelectorAll("input[type=checkbox]:checked");
    const texts = Array.from(checks).map((c) => {
        const label = ocrTaskList.querySelector(`label[for="${c.id}"]`);
        return label ? label.textContent : "";
    }).filter(Boolean);

    if (texts.length === 0) {
        toast("No tasks selected", "error");
        ocrModal.hidden = true;
        return;
    }

    await api("POST", "/tasks/batch", { texts, label: ocrLabel.value || "Default" });
    ocrModal.hidden = true;
    refresh();
    toast(`${texts.length} task${texts.length > 1 ? "s" : ""} added`, "success");
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
        if (!shownReminders.has(t.id)) {
            shownReminders.add(t.id);
            toast(`Reminder: ${t.text}`, "info");
            if ("Notification" in window && Notification.permission === "granted") {
                new Notification("To-Do Reminder", { body: t.text });
            }
        }
    });
    setTimeout(() => shownReminders.clear(), 60000);
}

// ── Helpers ───────────────────────────────────────────────────────
function formatTimeAgo(ts) {
    const diff = (Date.now() / 1000) - ts;
    if (diff < 60) return "just now";
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
    return new Date(ts * 1000).toLocaleDateString();
}

function toast(msg, type = "info") {
    const el = document.createElement("div");
    el.className = `toast ${type}`;
    el.textContent = msg;
    toasts.appendChild(el);
    setTimeout(() => {
        el.style.opacity = "0";
        setTimeout(() => el.remove(), 300);
    }, 3000);
}
