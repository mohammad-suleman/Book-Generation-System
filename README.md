<<<<<<< HEAD
# Book-Generation-System
=======
# Book Generation System

An automated, AI-powered book generation platform built with **FastAPI** and **OpenAI GPT-4**. Upload a CSV with your book idea, and the system generates a complete book — outline, chapters, and compiled document — with human review gates at every step.

---

## Features

- **CSV Import** — Upload book title and notes via CSV to kick off generation
- **AI Outline Generation** — GPT-4 creates a detailed chapter-by-chapter outline
- **AI Chapter Writing** — Each chapter generated with context from previous chapters
- **Human-in-the-Loop** — Review and approve at every stage (outline, chapters, final draft)
- **Context Chaining** — Chapter summaries feed into subsequent chapters for continuity
- **Multi-Format Export** — Download as **.docx**, **.pdf**, or **.txt**
- **Markdown Cleanup** — Strips `##`, `**`, and other markdown from final output
- **Email Notifications** — SMTP alerts when outline/chapters are ready for review
- **Structured Logging** — Separate log files for app events, errors, and output
- **MySQL Database** — Full persistence with audit trail
- **Swagger API Docs** — Auto-generated at `/docs`

---

## Tech Stack

| Component | Technology |
|---|---|
| Backend | **FastAPI** (Python 3.10+) |
| AI Model | **OpenAI GPT-4** (gpt-4-0125-preview) |
| Database | **MySQL 8.0** + SQLAlchemy ORM |
| Migrations | **Alembic** |
| Frontend | Vanilla **HTML / CSS / JavaScript** |
| Document Gen | **python-docx** (DOCX), **fpdf2** (PDF), plain text (TXT) |
| Email | **aiosmtplib** (SMTP/SSL) |
| Validation | **Pydantic v2** |
| Retry Logic | **tenacity** (exponential backoff) |
| Logging | Python `logging` (3 log files) |

---

## Project Structure

```
├── .env.example          # Environment variable template
├── .gitignore            # Git ignore rules
├── alembic.ini           # Alembic migration config
├── alembic/              # Database migrations
├── requirements.txt      # Python dependencies
├── README.md             # This file
│
├── app/                  # Backend application
│   ├── main.py           # FastAPI entry point
│   ├── api/
│   │   ├── books.py      # Book import & outline endpoints
│   │   ├── chapters.py   # Chapter generation endpoints
│   │   └── final_draft.py # Compilation & download endpoints
│   ├── core/
│   │   ├── config.py     # Pydantic settings (loads .env)
│   │   ├── constants.py  # Enums, token limits, temperature
│   │   ├── database.py   # SQLAlchemy engine & session
│   │   └── logging_config.py # Logging setup (3 log files)
│   ├── models/
│   │   ├── book.py       # Book model
│   │   ├── outline.py    # Outline model
│   │   ├── chapter.py    # Chapter model
│   │   ├── final_draft.py # Final draft model
│   │   └── notification_log.py # Email log model
│   ├── schemas/          # Pydantic request/response schemas
│   │   ├── book.py
│   │   ├── outline.py
│   │   ├── chapter.py
│   │   └── final_draft.py
│   └── services/
│       ├── openai_service.py   # GPT-4 outline/chapter/summary generation
│       ├── csv_service.py      # CSV parsing & import
│       ├── document_service.py # DOCX/PDF/TXT compilation
│       ├── workflow_service.py # State machine & gating logic
│       ├── context_service.py  # Chapter summary chaining
│       └── email_service.py    # SMTP email notifications
│
├── frontend/             # Browser UI
│   ├── index.html        # 4-step workflow interface
│   ├── styles.css        # Modern gradient design
│   ├── app.js            # API integration & UI logic
│   ├── sample_books.csv  # Sample input (3 books)
│   └── sample_marketing.csv # Sample input (1 book)
│
├── logs/                 # Generated at runtime
│   ├── app_YYYY-MM-DD.log    # All application logs
│   ├── error_YYYY-MM-DD.log  # Errors only
│   └── output_YYYY-MM-DD.log # Book generation results
│
└── outputs/              # Generated book files (.docx, .pdf, .txt)
```

---

## Prerequisites

- **Python 3.10+**
- **MySQL 8.0+**
- **OpenAI API key** (with GPT-4 access)

---

## Installation

### 1. Clone the repository

```bash
git clone <repo-url>
cd "media @ marsons"
```

### 2. Create virtual environment

```bash
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Copy `.env.example` to `.env` and fill in your values:

```env
# OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-0125-preview

# MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-password
MYSQL_DATABASE=book_generation_db

# SMTP Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
NOTIFICATION_EMAIL=recipient@email.com

# App
DEBUG=true
OUTPUT_DIR=outputs
```

### 5. Create MySQL database

```sql
CREATE DATABASE book_generation_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 6. Run database migrations

```bash
alembic upgrade head
```

---

## Running the Application

### Start the backend (port 8000)

```bash
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

### Start the frontend (port 3000)

```bash
cd frontend
python -m http.server 3000
```

### Access

| Service | URL |
|---|---|
| Frontend UI | http://localhost:3000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Root | http://localhost:8000 |
| Health Check | http://localhost:8000/health |

---

## Workflow

The system follows a **5-stage state machine**:

```
INPUT → OUTLINE → CHAPTERS → COMPILATION → COMPLETED
```

### Step-by-step:

1. **Import** — Upload CSV with book title and notes
2. **Generate Outline** — AI creates chapter-by-chapter outline
3. **Approve Outline** — Review and approve (or add notes for regeneration)
4. **Generate Chapters** — AI writes each chapter sequentially with context chaining
5. **Compile & Download** — Compile into DOCX, PDF, or TXT

### Gating Logic

Each stage has approval gates controlled by `NotesStatus`:

| Status | Meaning |
|---|---|
| `no` | Paused, waiting for review |
| `yes` | Has notes, needs processing |
| `no_notes_needed` | Approved, proceed to next stage |

---

## API Endpoints

### Books & Outlines

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/books/import` | Import book from CSV |
| GET | `/api/books/{id}` | Get book details |
| POST | `/api/books/{id}/outline/generate` | Generate outline with AI |
| PUT | `/api/books/{id}/outline/notes` | Update outline notes/approval |

### Chapters

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/books/{id}/chapters/{num}/generate` | Generate chapter |
| GET | `/api/books/{id}/chapters` | List all chapters |
| PUT | `/api/books/{id}/chapters/{num}/notes` | Update chapter notes |

### Final Draft

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/books/{id}/compile` | Compile final draft |
| GET | `/api/books/{id}/final-draft/download?format=docx` | Download as DOCX |
| GET | `/api/books/{id}/final-draft/download?format=pdf` | Download as PDF |
| GET | `/api/books/{id}/final-draft/download?format=txt` | Download as TXT |
| GET | `/api/books/{id}/status` | Get book generation status |

---

## CSV Input Format

```csv
title,notes_on_outline_before,notes_on_outline_after,status_outline_notes
Digital Marketing Mastery,"Write a guide covering social media, SEO, email marketing...","",no
```

| Column | Required | Description |
|---|---|---|
| `title` | Yes | Book title |
| `notes_on_outline_before` | Yes | Instructions for outline generation |
| `notes_on_outline_after` | No | Post-generation review notes |
| `status_outline_notes` | No | Initial status (`no` default) |

---

## Logging

Three separate date-stamped log files in `logs/`:

| File | Content |
|---|---|
| `app_YYYY-MM-DD.log` | All application events (INFO+) |
| `error_YYYY-MM-DD.log` | Errors only with stack traces |
| `output_YYYY-MM-DD.log` | Book generation milestones (imports, outlines, chapters, compilations) |

---

## Configuration Constants

Defined in `app/core/constants.py`:

| Constant | Value | Description |
|---|---|---|
| `MAX_TOKENS_OUTLINE` | 4000 | Max tokens for outline generation |
| `MAX_TOKENS_CHAPTER` | 4096 | Max tokens per chapter (model limit) |
| `MAX_TOKENS_SUMMARY` | 500 | Max tokens for chapter summaries |
| `TEMPERATURE` | 0.01 | Low temperature for consistent output |
| `MAX_CONTEXT_CHAPTERS` | 10 | Max previous chapter summaries in context |

---

## Database Schema

5 tables managed by SQLAlchemy + Alembic:

| Table | Description |
|---|---|
| `books` | Book metadata and current stage |
| `outlines` | Generated outlines with notes |
| `chapters` | Individual chapters with content and summaries |
| `final_drafts` | Compiled document paths and review status |
| `notification_logs` | Email notification audit trail |

---

## Key Design Decisions

- **Context Chaining**: Each chapter receives summaries of all previous chapters to maintain narrative continuity
- **Markdown Cleanup**: AI output is stripped of `##`, `**`, `*` formatting before document compilation
- **Retry with Backoff**: OpenAI calls use `tenacity` with 3 retries and exponential wait (1-10s)
- **Token Limit**: GPT-4-0125-preview supports max 4096 completion tokens per request
- **State Machine**: Workflow enforces sequential generation — can't compile before all chapters are approved

---

## License

Private — Media @ Marsons
>>>>>>> 29ad653 (book geneation system)
