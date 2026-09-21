# To-Do List Application - Session Summary

## Running the Application Locally

### Prerequisites
- Python 3.12+
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract) (system package)
- pip packages: `flask`, `pytesseract`, ` Pillow`

### Start the server
```bash
cd /home/gamp/Public/to-do-list
python3 app.py
```

The server will be at `http://localhost:5000` (or PORT env var).

### Environment variables
| Variable | Default | Description |
|----------|---------|-------------|
| `TODO_FILE` | `$HOME/.todo_tasks.json` | Path to JSON data file |
| `PORT` | `5000` | Server port |
| `FLASK_DEBUG` | `0` | Set to `1` for debug mode |

### API Endpoints
- `GET /api/tasks?filter=all&label=Work` - List tasks
- `POST /api/tasks` - Create task ({text, label, reminder})
- `GET /api/tasks/<id>` - Get single task
- `PUT /api/tasks/<id>` - Update task
- `DELETE /api/tasks/<id>` - Delete task
- `POST /api/tasks/clear-completed` - Clear completed
- `GET /api/stats` - Statistics
- `GET /api/reminders` - Due reminders
- `POST /api/ocr` - Extract text from image

## Deployment Options

### Vercel (Recommended for simplicity)
1. Install the Vercel CLI: `npm i -g vercel`
2. Run `vercel` in the project directory
3. Set environment variables in the Vercel dashboard:
   - `TODO_FILE` (path, will be in `/tmp` or writable dir)
   - `PORT` (optional)
   - `FLASK_DEBUG` (optional)

**Note:** Vercel's serverless environment has limited filesystem persistence. The JSON file (`TODO_FILE`) will not persist between requests in the free tier. For production use, consider a database backend.

### Alternative: Railway/Render/DigitalOcean
- Same Flask app, set env vars in dashboard
- Persistent file storage available (set `TODO_FILE` to a mounted path)

### Docker (for full control)
```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y tesseract-ocr
WORKDIR /app
COPY . .
RUN pip install flask pytesseract pillow
CMD ["python3", "app.py"]
```

## Remaining Improvements (from this session)

### Backend (`todo.py`)
1. **`filtered()` label logic** (line 131): Changed `label and label != "All"` to `label and label != "Default"` — filters now correctly exclude the "Default" label when `label != "Default"`, matching the UI behavior
2. **`load()` error handling** (line 46): Added `try/except` for `JSONDecodeError` and `OSError` — prevents crashes on corrupt/malformed JSON file
3. **`remove()` simplification** (line 93): Replaced `before/after` count check with `self.get()` guard — cleaner, always saves, returns bool
4. **`search()` method** (new): Added query-by-text search returning tasks whose text contains the search term (case-insensitive)

### API (`app.py`)
1. **`create_task()` label validation** (line 58): Added `VALID_LABELS` check — invalid labels fall back to "Default" instead of being stored raw
2. **`update_task()` label validation** (line 83-86): Same label validation on updates; invalid labels reset to "Default"
3. **OCR size limit** (line 123): Added 2MB max image check before decoding — prevents abuse/timeout on large images
4. **`stats()` label counts** (line 107): Now includes `label_counts` object showing task counts per label, derived from actual data

### Frontend (`app.js`)
1. **OCR loading indicator**: Already had CSS (`ocr-loading`, `ocr-spinner`) — functionality works
2. **Reminder polling deduplication** (lines 297-312): Added `shownReminders` Set to prevent duplicate notifications for the same task within 60 seconds
3. **Delete animation guard** (lines 198-209): Added `animating` flag to prevent rapid double-delete clicks from queuing multiple API calls
4. **Stats label counts**: Frontend can now display per-label counts from the `/api/stats` response

## File Changes Summary

- `todo.py`: 4 improvements (filtered label, load error handling, remove simplification, new search method)
- `app.py`: 5 improvements (label validation in create/update, OCR size limit, stats label counts)
- `app.js`: 3 improvements (reminder dedup, delete animation guard, OCR loading already styled)
- `session.md`: New file with running/deployment guides and remaining improvements list

## Suggested Next Steps

1. **Replace JSON file with a real database** (SQLite/PostgreSQL) for persistent, concurrent-safe storage
2. **Add authentication** if the app is used by multiple users
3. **Add task due dates + overdue filtering** — the reminder system is basic; could integrate with calendar
4. **Dark mode UI polish** — already has theme toggle; could extend CSS variables
5. **Unit tests** for `TodoStore` methods (filtered, search, counts, reminders)