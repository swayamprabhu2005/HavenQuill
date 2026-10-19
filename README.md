# 📖 Storybook Studio

**Storybook Studio** is a private, local-first personal AI-assisted story-writing and storybook application. It allows you to speak your ideas, type rough drafts, paste notes, or import existing manuscripts, and turn them into structured stories with chapters, scenes, characters, locked canon facts, and publication-ready exports.

---

## 🌟 Key Features

1. **Voice & Audio Input**: Browser-based microphone recording or audio file upload (WAV, MP3, M4A, OGG) with preview, playback, and transcript editing before saving.
2. **Text Input & Manuscript Import**: Freeform text editor, draft preservation, and full import support for `.txt`, `.md`, `.pdf`, and `.docx` manuscripts.
3. **AI-Assisted Story Development**: Generates loglines, short & detailed synopses, thematic motifs, character goals, dramatic conflicts, turning points, open questions, and assumptions.
4. **Structured Outlining**: Generates multi-chapter outlines, character arcs, revelations, and setup/payoff tracking with section-by-section regeneration.
5. **Scene Management & Drafting**: Detailed scene cards with POV, locations, time markers, emotional shifts, dramatic beats, reordering, duplicate, split, merge, and prose drafting/rewriting.
6. **Future Image & Comic Compatibility**: Natively stores visual panel metadata (`camera_framing`, `mood_atmosphere`, `visual_summary`, `characters_present`) ready for Phase 2 image and comic pipelines.
7. **Story Bible & Canon Locking**: Manage characters, locations, timeline events, and lock critical facts (`is_locked`) with automatic contradiction warnings.
8. **Book View**: A distraction-reduced book reader with cover page, table of contents, font controls (size & style), reading progress, word count estimation, and inline prose editing.
9. **Multi-Format Exports & Backups**:
   - Professional PDF book via ReportLab (with title page, table of contents, page numbers, clean margins)
   - Microsoft Word `.docx` manuscript
   - Markdown manuscript
   - Full structured JSON export
   - Safe self-contained ZIP project backup & restore with ID conflict protection
10. **Three-Tier AI Provider System**:
    - **Mock Provider**: 100% offline, zero API keys required, deterministic structured output for development and automated testing.
    - **Google Gemini**: Primary cloud provider using the official modern `google-genai` SDK.
    - **Groq**: High-speed fallback provider using the official `groq` SDK.
    - **Configurable Fallback Policy**: Automatically routes temporary rate limits (429) from Gemini to Groq when enabled.

---

## 🛠️ Windows Installation & Setup Guide

### Prerequisites
- Windows 10 or 11
- Python 3.10 or 3.11 installed and added to `PATH`
- Standard audio microphone (for voice recording)

### 1. Clone or Open Workspace
Open PowerShell in the project directory:
```powershell
cd d:\MyFiles\Story-Generator
```

### 2. Create and Activate Virtual Environment
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell restricts script execution, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

### 3. Install Dependencies
```powershell
.\.venv\Scripts\pip.exe install -r requirements.txt
```

---

## 🚀 Exact Application Launch Command

Run the application with Streamlit:
```powershell
.\.venv\Scripts\streamlit.exe run app.py
```
Or with Python:
```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The application will launch and open in your default browser at `http://localhost:8501`.

---

## 🔑 AI Provider Configuration

Storybook Studio works out of the box with **Mock Provider** without any API keys. When you are ready to use cloud AI engines:

### 1. Google Gemini Setup (Primary Provider)
1. Obtain an API key from [Google AI Studio](https://aistudio.google.com/apikey).
2. Open **Settings** in the Storybook Studio sidebar or edit `.env`:
   ```env
   AI_PROVIDER=gemini
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   ```
3. Supported models: `gemini-2.5-flash`, `gemini-3.8-flash`, etc.

### 2. Groq Setup (Fallback Provider)
1. Obtain an API key from [Groq Console](https://console.groq.com/keys).
2. Open **Settings** in the Storybook Studio sidebar or edit `.env`:
   ```env
   GROQ_API_KEY=your_actual_groq_api_key_here
   GROQ_MODEL=llama-3.3-70b-versatile
   ```
3. Supported models: `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, etc.

### 3. Provider Fallback Policy
In the **Settings** view, toggle **Enable Automatic Fallback (Gemini ➔ Groq)**.
- If Gemini encounters temporary quota or rate limits (HTTP 429), Storybook Studio automatically completes the request using Groq.
- Fallback will **not** trigger on invalid keys or malformed requests, ensuring errors are never masked silently.

---

## 🎙️ Voice & Audio Dictation

1. From the Dashboard, click **Voice & Audio Capture**.
2. **Microphone Recording**: Click the native browser microphone recorder to dictate your story ideas.
3. **Audio File Upload**: Upload any `.wav`, `.mp3`, `.m4a`, or `.ogg` recording.
4. **Transcription**:
   - Use `mock` for instant offline testing.
   - Configure `gemini` or `groq` (Whisper API) under **Settings** for cloud transcription.
   - Always review and edit your transcript before clicking **Save as Source Draft**.

---

## 📦 Backups and Safe Restore

- **Export Archive**: In the Dashboard, click **Backup & Restore ➔ Export Project Archive** to download a self-contained `.zip` package.
- **Safe Restore**:
  - The restore engine validates the archive and previews title, genre, chapter count, and character count before applying changes.
  - Automatically avoids ID collisions by generating fresh identifiers when restoring duplicates, or optionally overwriting if explicitly selected.
  - **Secrets are strictly excluded**: Backup ZIP archives reject and omit API keys and credentials.

---

## 🧪 Running Automated Tests

Run the full pytest suite:
```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

The test suite covers:
- SQLite database creation, schema version, and WAL mode
- Project data isolation and cascading deletions
- Source draft preservation separate from prose
- Version history snapshot recording
- Chapter and scene reordering, splitting, and merging
- Pydantic structured output validation
- MockProvider end-to-end workflow (100% offline)
- Missing API key and malformed response error handling for Gemini and Groq
- Fallback policy execution on temporary 429 errors
- PDF book generation with ReportLab
- DOCX export with python-docx
- Markdown manuscript export
- Backup ZIP creation, preview, and conflict resolution
- Secret exclusion from exports

---

## 🔧 Troubleshooting Guide

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **Streamlit does not open** | Port 8501 is in use or firewall blocks local traffic. | Run `.\.venv\Scripts\streamlit.exe run app.py --server.port 8502` |
| **`Gemini API key is not configured`** | `GEMINI_API_KEY` is blank in `.env`. | Go to **Settings** in the sidebar and enter your key, or select `mock` provider. |
| **`Groq API key is not configured`** | `GROQ_API_KEY` is blank in `.env`. | Enter your Groq key in **Settings** or disable auto-fallback. |
| **Microphone not recording in browser** | Browser permissions blocked. | Allow microphone access in your browser address bar settings, or use the **Upload Audio File** tab. |
| **PDF export font warnings** | Special Unicode glyphs in text. | Standard punctuation is normalized automatically; ReportLab uses Times-Roman and Helvetica. |
| **Database locked error** | Another process is holding an exclusive lock. | The database uses SQLite WAL mode to prevent locks. Ensure no external DB browser holds exclusive locks. |

---

## 📂 Project Structure

```
d:\MyFiles\Story-Generator\
├── app.py                     # Streamlit application entry point
├── requirements.txt           # Python dependencies
├── pytest.ini                 # Pytest configuration
├── .env.example               # Safe environment configuration template
├── .env                       # Local environment configuration (git ignored)
├── .gitignore                 # Excludes .venv, data, logs, and secrets
├── README.md                  # Comprehensive manual and installation guide
│
├── storybook/                 # Core application package
│   ├── config.py              # Configuration manager & key masking
│   ├── database.py            # SQLite connection, schema, WAL mode
│   ├── models.py              # Pydantic models & structured schemas
│   ├── repositories.py        # Database CRUD repositories
│   │
│   ├── providers/             # AI generation providers
│   │   ├── base.py            # BaseAIProvider abstract interface
│   │   ├── mock_provider.py   # 100% offline mock story engine
│   │   ├── gemini_provider.py # Google GenAI SDK integration
│   │   ├── groq_provider.py   # Groq SDK integration
│   │   └── provider_manager.py# Routing & fallback coordinator
│   │
│   ├── services/              # Application business logic
│   │   ├── story_service.py   # Project lifecycle & development
│   │   ├── outline_service.py # Chapter outlines & ordering
│   │   ├── scene_service.py   # Scene breakdown, drafting & reorder
│   │   ├── character_service.py# Story bible & canon locking
│   │   ├── continuity_service.py# Narrative consistency reviewer
│   │   ├── transcription_service.py# Voice capture & speech-to-text
│   │   ├── export_service.py  # PDF, MD, DOCX, JSON exports
│   │   └── backup_service.py  # Self-contained project ZIP archives
│   │
│   ├── ui/                    # Streamlit views
│   │   ├── dashboard.py       # Creative workspace dashboard
│   │   ├── project_editor.py  # Multi-step story creation studio
│   │   ├── scene_view.py      # Scene cards & visual panel metadata
│   │   ├── book_view.py       # Book reader & inline prose editor
│   │   ├── story_bible_view.py# Characters, locations, canon facts
│   │   └── settings_view.py   # AI providers & keys manager
│   │
│   └── utils/
│       └── sample_project.py  # Seedable fictional demo project
│
├── tests/                     # Automated test suite (28 tests)
│   ├── conftest.py
│   ├── test_database.py
│   ├── test_models.py
│   ├── test_providers.py
│   ├── test_provider_manager.py
│   ├── test_services.py
│   └── test_exports_and_backups.py
│
├── docs/                      # Architectural specifications
│   ├── ARCHITECTURE.md        # Technical design and architecture
│   └── SCENE_EXPORT_SCHEMA.md # Future image & comic panel schema
│
└── data/                      # Auto-created runtime storage (git ignored)
    ├── storybook.db           # SQLite database
    ├── backups/               # Backup archives
    ├── exports/               # Exported files
    └── audio/                 # Captured audio recordings
```
