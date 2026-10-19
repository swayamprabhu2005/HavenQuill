# 🪶 HavenQuill
### *A Private, Local-First AI Story-Writing & Screenplay Sanctuary*

[![Repository](https://img.shields.io/badge/GitHub-HavenQuill-blue?logo=github)](https://github.com/swayamprabhu2005/HavenQuill-.git)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11-green?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/Privacy-100%25%20Local--First-teal)](#)
[![Tests](https://img.shields.io/badge/Tests-Passing%20(33%2F33)-brightgreen)](#-automated-test-suite)

**HavenQuill** is a private, local-first personal AI-assisted story-writing, storybook, and screenplay adaptation application designed with a soothing, anxiety-free atmosphere. It allows you to speak your thoughts, type rough drafts, paste notes, or import existing manuscripts, and gently develop them into cohesive stories with chapters, scenes, characters, locked canon facts, publication-ready book exports, and industry-standard screenplays.

---

## ⚡ Quick Start: Single-Click Windows Launch

To launch HavenQuill with one click on Windows, double-click:
```bat
run.bat
```
`run.bat` automatically:
1. Verifies your Python installation.
2. Creates and configures the isolated `.venv` virtual environment if needed.
3. **Installs & verifies `faster-whisper`** into your local `.venv`.
4. **Isolates all HuggingFace and Whisper model weights** strictly into the project subfolder (`data\whisper_models`), completely avoiding cluttering your `C:\` drive. If you ever delete the project folder, all models and environments are cleanly deleted with it!
5. Copies `.env.example` to `.env` if no `.env` exists.
6. Displays direct links to generate your Gemini and Groq API keys.
7. Launches the application in your default browser at `http://localhost:8501`.

---

## 🔑 Direct Links to Generate API Keys

HavenQuill works **100% offline out-of-the-box with the Mock Provider** (no API keys required). When you are ready to enable cloud AI models, generate your keys here:

| Provider | Purpose | Direct Key Generation Link | Recommended Default Model |
| :--- | :--- | :--- | :--- |
| **Google Gemini** | Primary AI Prose & Reasoning Engine | [Google AI Studio API Keys](https://aistudio.google.com/apikey) | `gemini-3.8-flash` |
| **Groq Cloud** | High-Speed AI Inference & Screenplay Engine | [Groq Console API Keys](https://console.groq.com/keys) | `qwen/qwen3.8-27b` |

Paste your keys directly into `.env` or navigate to **⚙️ Settings** in the application sidebar.

---

## 📖 Book View & 🎬 Screenplay Studio

HavenQuill defaults directly to **Book View** when you open or create a project, putting your literature front and center:

### 1. 📖 Book View (Default Primary Interface)
- **Distraction-Free Reading**: Clean book layout with typography controls (Georgia, Garamond, Times New Roman, Segoe UI; 16px–24px).
- **Inline Chapter Editing**: Edit chapter prose directly while reading.
- **One-Click PDF Export**: Download your complete formatted book as a publication-ready PDF with clean margins, title page, and table of contents right from the top toolbar.

### 2. 🎬 Script View (Screenplay & Incremental Adaptation)
- **Automatic Novel-to-Screenplay Adaptation**: Convert your entire book into standard Hollywood script format with uppercase sluglines (`INT. ARCHIVE - NIGHT`), character cues (`ELENA`), parentheticals `(whispering)`, and action lines.
- **Intelligent Incremental Continuation**:
  - If you've adapted half the book into a screenplay, and later write new chapters, HavenQuill tracks exactly which chapters were already converted.
  - When you click **Continue Script with New Chapters**, HavenQuill sends **both the existing script** (for formatting, tone, and character consistency) and the **new chapters** (in Markdown) to Gemini/Groq.
  - The AI seamlessly picks up from the last scene and unifies the script without restarting from scratch!
- **Professional Screenplay Exports**:
  - **Screenplay PDF**: Formatted in standard 12pt Courier with Hollywood-standard indentation and margins.
  - **Fountain (`.fountain`)**: Universal open-source screenplay markup.
  - **Plain Text / Markdown (`.txt`, `.md`)**.

---

## 🎙️ Spoken Dictation: Fast Whisper vs. Audio Recording

### What is Fast Whisper?
- **Faster-Whisper is strictly for Transcribing (Speech-to-Text)**: It is a CTranslate2 reimplementation of OpenAI's Whisper model that decodes audio bytes into text on your local CPU up to 4x faster with 8-bit quantization. It does **not** record audio from your microphone hardware.
- **Audio Recording**: Handled natively and privately by your browser's Web Audio microphone via Streamlit's `st.audio_input` or by uploading audio files (`.wav`, `.mp3`, `.m4a`, `.ogg`). The recorded audio is decoded locally by Faster-Whisper with zero telemetry or cloud transmission.
- **Workspace Model Isolation**: All model weights are stored in `data/whisper_models` inside the workspace and never in `C:\Users\<user>\.cache`.

---

## 🛡️ Agentic RAG Rolling Memory Engine & Credit Protection

When generating a story across multiple spoken or typed sections, sending thousands of words of past transcripts into Gemini on every turn wastes API credits, burns through token limits, and triggers HTTP 429 rate limits.

HavenQuill solves this with its **Agentic RAG Rolling Memory Engine**:
1. **Segmented Story Flow**: Spoken or typed input is gathered into an active segment.
2. **Word Target & Progress Tracker**: Select a target limit (300, 500, or 1,000 words). A progress bar visualizes how close your active part is to the target.
3. **Verbal Keyword Boundary Detection**: Saying *"para one end"*, *"para end"*, *"paragraph end"*, or *"next part"* automatically strips the keyword, seals the segment, and prepares it for transformation.
4. **Agentic RAG Context Packet**: When sent to Gemini, the engine compresses previous story history into:
   - **Locked Canon Facts**: Immutable world rules and character facts.
   - **Active Characters**: Names and core traits.
   - **Narrative Bridge**: The exact last 2 sentences of the immediately preceding committed part to ensure seamless prose flow.
   - **Rolling Story Recap**: A distilled multi-point recap of recent parts.
   - **Estimated Credit Savings**: Saves 80% to 90% of tokens on every request.
5. **Clear Canon Commitment Divider**: Once processed, a distinct visual divider appears:
   ```
   ✓ [Committed to Story Canon — Part 1]
   ```
   Committed parts are sealed into SQLite and cannot be accidentally overwritten.
6. **Rethink with Gemini**: Modify or refine the active segment by providing author feedback without re-sending or altering previous committed parts.

---

## 🎨 Soothing & Anxiety-Free Visual Design

Writing should be peaceful and reflective. The interface is styled with a natural, calming sanctuary theme:
- **Linen Background**: `#FAF8F5` replaces harsh stark whites with soft book paper.
- **Forest Sage Accents**: `#386641` buttons and borders promote focus and tranquility.
- **Soft Border Radii & Warm Shadows**: Rounded, card-like containers inspired by physical stationery.
- **Readable Typography**: High-contrast, gentle serifs and sans-serifs for effortless reading and editing.

---

## 🌟 Complete Feature Matrix

1. **📖 Book View (Default)**: Full book reading, typography styling, inline editing, and one-click PDF export.
2. **🎬 Screenplay Studio**: Novel-to-script adaptation, incremental continuation with existing script, Courier PDF, and Fountain export.
3. **🌿 Live Story Sanctuary**: Streaming dictation, Fast Whisper local CPU transcription, word targets, and Agentic RAG credit savings.
4. **📐 Scenes & Structure**: Detailed scene cards with POV, locations, emotional shifts, dramatic beats, and reordering.
5. **🎨 Future Image & Comic Compatibility**: Natively stores visual panel metadata (`camera_framing`, `mood_atmosphere`, `visual_summary`, `characters_present`) ready for future image generation pipelines.
6. **📜 Story Bible & Canon Locking**: Manage characters, locations, timeline events, and lock critical facts (`is_locked`) with automatic contradiction warnings.
7. **📦 Multi-Format Exports & Safe Backups**:
   - Professional PDF book via ReportLab
   - Hollywood Screenplay PDF in Courier
   - Microsoft Word `.docx` manuscript
   - Markdown manuscript & Fountain screenplay
   - Full structured JSON export
   - Safe self-contained ZIP project backup & restore with ID collision prevention and secret exclusion.
8. **Three-Tier AI Provider System**:
   - **Mock Provider**: 100% offline, zero API keys required, deterministic structured output for development and automated testing.
   - **Google Gemini**: Primary cloud provider using the official modern `google-genai` SDK (`gemini-3.8-flash`).
   - **Groq Cloud**: High-speed fallback provider using the official `groq` SDK (`qwen/qwen3.8-27b`).

---

## 🛠️ Windows Installation & Manual Setup

### Prerequisites
- Windows 10 or 11
- Python 3.10 or 3.11 installed and added to `PATH`
- Standard microphone

### 1. Open Terminal
```powershell
cd d:\MyFiles\Story-Generator
```

### 2. Set Up Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
.\.venv\Scripts\pip.exe install -r requirements.txt
```

### 4. Run the Application
```powershell
.\.venv\Scripts\streamlit.exe run app.py
```
Or simply double-click **`run.bat`**!

---

## 🧪 Automated Test Suite

Run the full pytest suite:
```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

All **33 automated unit tests** pass with 100% success across:
- **`test_agentic_rag.py`**: Segment CRUD, keyword boundary detection ("para one end"), Agentic context packet assembly, word/credit savings calculation, and segment rethink without touching history.
- **`test_database.py`**: SQLite WAL mode, cascading deletes, project isolation, and chapter/scene reordering.
- **`test_models.py`**: Pydantic schema validation, scene visual panel metadata for future image generation.
- **`test_providers.py` & `test_provider_manager.py`**: Mock provider offline workflows, missing API key handling, malformed response resilience, and automatic fallback routing.
- **`test_services.py`**: Story development, outline generation, scene drafting, story bible canon locking, and continuity audits.
- **`test_exports_and_backups.py`**: ReportLab PDF generation, python-docx exports, Markdown exports, ZIP backup creation, preview, and safe restore.

---

## 📂 Project Architecture

```
d:\MyFiles\Story-Generator\
├── app.py                     # Streamlit application entry point & soothing theme
├── run.bat                    # Single-click Windows launcher with local Whisper isolation
├── requirements.txt           # Python dependencies (faster-whisper, google-genai, groq, etc.)
├── pytest.ini                 # Pytest configuration
├── .env.example               # Environment template with recommended models
├── .env                       # Local API keys (git-ignored)
├── .gitignore                 # Excludes .venv, data, logs, secrets, and orphan docs
├── README.md                  # Comprehensive manual and installation guide
│
├── storybook/                 # Core HavenQuill package
│   ├── config.py              # Configuration manager & key masking
│   ├── database.py            # SQLite connection, schema, WAL mode, story_segments, scripts
│   ├── models.py              # Pydantic models & structured schemas (including Script)
│   ├── repositories.py        # Database CRUD repositories (including ScriptRepository)
│   │
│   ├── providers/             # AI generation providers
│   │   ├── base.py            # BaseAIProvider abstract interface
│   │   ├── mock_provider.py   # 100% offline mock story & screenplay engine
│   │   ├── gemini_provider.py # Google GenAI SDK integration (gemini-3.8-flash)
│   │   ├── groq_provider.py   # Groq SDK integration (qwen/qwen3.8-27b)
│   │   └── provider_manager.py# Routing & fallback coordinator
│   │
│   ├── services/              # Application business logic
│   │   ├── script_service.py  # Screenplay adaptation & incremental continuation
│   │   ├── agentic_rag_service.py # RAG rolling memory, boundary detection, credit saving
│   │   ├── story_service.py   # Project lifecycle & development
│   │   ├── outline_service.py # Chapter outlines & ordering
│   │   ├── scene_service.py   # Scene breakdown, drafting & reorder
│   │   ├── character_service.py# Story bible & canon locking
│   │   ├── continuity_service.py# Narrative consistency reviewer
│   │   ├── transcription_service.py# Faster-Whisper local CPU transcription
│   │   ├── export_service.py  # PDF, MD, DOCX, JSON exports
│   │   └── backup_service.py  # Self-contained project ZIP archives
│   │
│   ├── ui/                    # Streamlit views
│   │   ├── dashboard.py       # Creative workspace dashboard
│   │   ├── book_view.py       # Default Book Reader & inline prose editor
│   │   ├── script_view.py     # Screenplay Studio & incremental continuation
│   │   ├── live_scribe_view.py# Live Story Sanctuary (Voice & Agentic RAG)
│   │   ├── project_editor.py  # Multi-step story creation studio
│   │   ├── scene_view.py      # Scene cards & visual panel metadata
│   │   ├── story_bible_view.py# Characters, locations, canon facts
│   │   └── settings_view.py   # AI providers & keys manager
│   │
│   └── utils/
│       └── sample_project.py  # Seedable fictional demo project
│
├── tests/                     # Automated test suite
│   ├── test_agentic_rag.py    # Agentic RAG & Story Segment tests
│   ├── test_database.py       # SQLite database tests
│   ├── test_models.py         # Pydantic schema tests
│   ├── test_providers.py      # Provider tests
│   ├── test_provider_manager.py # Fallback & routing tests
│   ├── test_services.py       # Story & continuity services tests
│   └── test_exports_and_backups.py # Export & backup tests
│
├── docs/                      # Architectural specifications
│   ├── ARCHITECTURE.md        # Technical design and architecture
│   └── SCENE_EXPORT_SCHEMA.md # Future image & comic panel schema
│
└── data/                      # Auto-created runtime storage (git ignored)
    ├── storybook.db           # SQLite database
    ├── whisper_models/        # Isolated Faster-Whisper model cache (workspace only!)
    ├── backups/               # Backup archives
    ├── exports/               # Exported files
    └── audio/                 # Captured audio recordings
```
