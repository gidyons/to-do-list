# To-Do List — Session Summary

## Running Locally

### Prerequisites
- Python 3.12+
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract)
- pip packages: `flask`, `pytesseract`, `Pillow`

### Start
```bash
cd /home/gamp/Public/to-do-list
python3 app.py
```
Server: `http://localhost:5000`

### Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `TODO_FILE` | `$HOME/.todo_tasks.json` | Data file path |
| `PORT` | `5000` | Server port |
| `FLASK_DEBUG` | `0` | Debug mode |

### API Endpoints
- `GET /api/tasks?filter=all&label=Work` — List tasks
- `POST /api/tasks` — Create task (text, label, duration_minutes, reminder)
- `POST /api/tasks/batch` — Create multiple tasks (texts[], label)
- `GET /api/tasks/<id>` — Get task
- `PUT /api/tasks/<id>` — Update task (text, done, label, duration_minutes, reminder)
- `DELETE /api/tasks/<id>` — Delete task
- `POST /api/tasks/clear-completed` — Clear completed
- `GET /api/stats` — Statistics with label_counts
- `GET /api/reminders` — Due reminders
- `POST /api/ocr` — OCR extract (returns text + lines[])

---

## What Changed in This Session

### Backend — `todo.py`
- **`Task` dataclass**: Added `completed_at` (auto-set on toggle) and `duration_minutes` (expected completion time)
- **`add_many()`**: New method for batch task creation (used by OCR)
- **`update_duration()`**: New method to set duration on existing tasks
- **`toggle()`**: Now auto-sets `completed_at` timestamp when task is marked done
- **`load()`**: Robust error handling for corrupt JSON

### Backend — `app.py`
- **`/api/tasks/batch`** (POST): Batch create multiple tasks from OCR lines
- **`duration_minutes`** support: Accepted on create and update endpoints
- **OCR endpoint**: Returns both raw `text` and parsed `lines[]` array
- **Label validation**: All endpoints validate against `VALID_LABELS`
- **Stats**: Returns `label_counts` object with per-label task counts

### Frontend — `index.html`
- **Landing page**: Beautiful splash screen with animated dots, "Get Started" button. Shown once, hidden after (stored in localStorage)
- **Sidebar redesign**: Logo, "Lists" section with label nav, "Settings" section with theme palette selector and light/dark mode toggle
- **Mobile hamburger**: Opens sidebar with overlay backdrop on mobile
- **Input area**: Added label selector dropdown and duration button with presets (5m/15m/30m/1h/2h)
- **Duration modal**: Quick-select presets or custom minutes input
- **OCR modal**: Multi-task review — shows all extracted lines with checkboxes, select/deselect before batch-adding
- **Edit modal**: Now includes duration field
- **Task rows**: Show duration badge and relative timestamp ("2h ago")

### Frontend — `style.css` (complete rewrite)
- **6 theme palettes**: Blush (default), Ocean, Forest, Sunset, Lavender, Midnight
- Each palette has full **light + dark** mode variants (12 total themes)
- **Fluid edges**: All `border-radius` uses 16px (cards), 10px (buttons), 6px (inputs)
- **Blended colors**: No gradients — soft backgrounds, subtle borders, translucent accent colors (`--accent-soft: rgba(...)`)
- **Animations**: Landing page float-in, task slide-in, modal slide-up, toast slide-in, dot pulse, button scale
- **CSS custom properties**: Every color is a variable — switching palettes is instant
- **Mobile responsive**: Sidebar slides in/out with backdrop overlay, hamburger visible below 768px

### Frontend — `app.js` (major rewrite)
- **Landing page logic**: First-visit splash, skip if `landing_seen` in localStorage
- **Theme palette picker**: 6 palettes stored in localStorage, applied via `data-palette` attribute
- **Light/dark mode**: Toggle stored in localStorage, applied via `data-theme` attribute
- **Duration picker**: Quick presets (5m, 15m, 30m, 1h, 2h) or custom minutes, sent with task creation
- **OCR multi-task**: If OCR returns 1 line → fill input. If multiple → open review modal with checkboxes for selective batch-add
- **Relative timestamps**: `formatTimeAgo()` shows "just now", "5m ago", "2h ago", "3d ago"
- **PWA registration**: Registers service worker on page load

### PWA
- **manifest.json**: Updated with proper structure, SVG icons, orientation, categories
- **sw.js**: Fixed caching to work locally (try/catch on install, proper GET-only filtering)
- **SVG icons**: Created checkmark icons (192x192, 512x512) as inline SVG files

---

## How to Use

1. Run `python3 app.py` → visit `http://localhost:5000`
2. Click "Get Started" on the landing page (shown once)
3. Use the sidebar hamburger to switch between label lists
4. Change theme palette in sidebar Settings → Theme dropdown
5. Toggle light/dark mode with the sun/moon button
6. Add tasks with optional label and duration (click the clock icon)
7. Upload an image for OCR — single line fills input, multiple lines open a review modal
8. Edit tasks by double-clicking or clicking the edit icon — includes duration field
9. Task timestamps show relative time ("2m ago", "1h ago")

---

## Deployment

### Local (works as PWA)
The app works as a PWA locally — install it from the browser's address bar ("Install app" prompt).

### Vercel
```bash
npm i -g vercel && vercel
```
Set env vars in dashboard. Note: filesystem persistence limited on free tier.

### Docker
```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y tesseract-ocr
WORKDIR /app
COPY . .
RUN pip install flask pytesseract pillow
CMD ["python3", "app.py"]
```

### Railway / Render / DigitalOcean
Same Flask app, persistent file storage available.
