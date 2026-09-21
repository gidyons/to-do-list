# To-Do List Application

A high-performance, beautifully designed To-Do list application built with Python (Flask) and modern web technologies. Features AI-powered OCR for instant task entry from images, adaptive dark/light theming, task labels, reminders, and PWA support.

## Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Team & Contributions](#team--contributions)
- [Technology Stack](#technology-stack)
- [Deployment](#deployment)
- [License](#license)

## Features

| Feature | Description |
|---|---|
| **CRUD Operations** | Create, read, update, and delete tasks with a clean interface |
| **Task Labels** | Categorize tasks as Default, Personal, Shopping, Wishlist, Work, Events, Tasks, or Meetings |
| **AI / OCR** | Extract text from images (photos of notes, whiteboards, documents) and instantly create tasks |
| **Dark / Light Mode** | Adaptive theming with smooth transitions, persisted in localStorage |
| **Reminders** | Set time-based reminders with browser notification support |
| **Filtering** | View All, Active, or Completed tasks; filter by label |
| **PWA** | Installable as a Progressive Web App for a native-like experience |
| **Responsive** | Works seamlessly on desktop, tablet, and mobile devices |

## Getting Started

### Prerequisites

- Python 3.10+
- Tesseract OCR engine (for the OCR feature)

```bash
# Ubuntu / Debian
sudo apt install tesseract-ocr

# macOS
brew install tesseract
```

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/to-do-list.git
cd to-do-list

# Install Python dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The server starts at `http://localhost:5000`.

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `TODO_FILE` | `~/.todo_tasks.json` | Path to the JSON data file |
| `PORT` | `5000` | Server port |
| `FLASK_DEBUG` | `0` | Set to `1` for debug mode |

## Project Structure

```
to-do-list/
├── app.py                  # Flask application & REST API
├── todo.py                 # Core data model & persistence layer
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── templates/
│   └── index.html          # Main HTML template
└── static/
    ├── css/
    │   └── style.css       # Full UI styling (light + dark themes)
    ├── js/
    │   └── app.js          # Frontend logic (API calls, rendering, OCR)
    ├── img/                # App icons (PWA)
    ├── manifest.json       # PWA manifest
    └── sw.js               # Service worker for offline support
```

## API Reference

All endpoints are prefixed with `/api`.

### Tasks

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/tasks?filter=all&label=Work` | List tasks (optional filter/label) |
| `POST` | `/api/tasks` | Create a task — body: `{ "text", "label?", "reminder?" }` |
| `GET` | `/api/tasks/:id` | Get a single task |
| `PUT` | `/api/tasks/:id` | Update a task — body: `{ "text?", "done?", "label?", "reminder?" }` |
| `DELETE` | `/api/tasks/:id` | Delete a task |
| `POST` | `/api/tasks/clear-completed` | Remove all completed tasks |

### Other

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/stats` | Get done/total counts and available labels |
| `POST` | `/api/ocr` | Extract text from image — body: `{ "image": "<base64>" }` |
| `GET` | `/api/reminders` | Poll for due reminders |

## Team & Contributions

This project was developed collaboratively by four team members, each responsible for a specialized workstream:

### Omotoyosi — Logic & Security

**Responsibilities:** Task Creation and Reading (CRUD), API Key Management (Gmail, AI)

- Designed and implemented the core data model (`todo.py`) — `Task` dataclass and `TodoStore` persistence layer
- Built the full REST API in `app.py` with proper error handling, input validation, and status codes
- Implemented the OCR integration pipeline using Tesseract, including base64 image decoding and error recovery
- Designed the reminder system with timed polling and browser notification delivery
- Managed API key configuration and environment variable handling for secure credential storage

### Gideon — Data Integrity

**Responsibilities:** Task Updating/Editing and Deletion (CRUD)

- Implemented the task update logic — text editing, label reassignment, done-state toggling, and reminder management
- Built the delete and clear-completed endpoints with atomic operations to prevent data corruption
- Ensured JSON file persistence is atomic (save on every mutation) to prevent data loss
- Added task filtering (by status and by label) with correct edge-case handling
- Verified data integrity across the full CRUD lifecycle through the `counts()`, `get()`, and `filtered()` methods

### Victor — DevOps & Distribution

**Responsibilities:** GitHub Repository Setup, Vercel Deployment, PWA Packaging

- Set up the GitHub repository with proper `.gitignore`, branch structure, and collaboration workflows
- Configured the project for Vercel deployment (serverless-compatible Flask app)
- Built the PWA layer: `manifest.json`, service worker (`sw.js`) with cache-first strategy for static assets
- Created the `requirements.txt` for reproducible builds
- Structured the project for easy CI/CD integration

### Ibukun — Experience Design

**Responsibilities:** Frontend (UI) Development, Landing Page, Task Labels, Visual Polish

- Designed and built the complete frontend (`index.html`, `style.css`, `app.js`)
- Created the modern, "delectable" UI with a warm pink/rose color palette and clean typography
- Implemented the sidebar navigation with task label categories
- Built the dark/light mode system with CSS custom properties and smooth transitions
- Designed the edit modal, toast notifications, empty states, and loading indicators
- Ensured full responsive design for mobile, tablet, and desktop viewports
- Added micro-interactions: slide-in animations, hover effects, checkbox accents, button press feedback

## Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3, Flask |
| **Frontend** | HTML5, CSS3 (Custom Properties), Vanilla JavaScript |
| **OCR / AI** | Tesseract OCR (pytesseract) + Pillow |
| **Storage** | JSON file (`~/.todo_tasks.json`) |
| **PWA** | Service Worker, Web App Manifest |
| **Deployment** | Vercel (serverless) |
| **Version Control** | Git, GitHub |

## Deployment

### Vercel

This project is configured for Vercel deployment. Push to the connected GitHub repository and Vercel will automatically build and deploy.

For local testing of the production build:

```bash
pip install gunicorn
gunicorn app:app
```

### Manual

```bash
export PORT=8000
python app.py
```

## License

This project is open source. See the repository for license details.
