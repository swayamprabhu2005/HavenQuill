# 🌿 Storybook Studio (HavenScribe)
### *A Private, Local-First AI Story-Writing & Creative Sanctuary*

**Storybook Studio** is a private, local-first personal AI-assisted story-writing and storybook application designed with a soothing, anxiety-free atmosphere. It allows you to speak your thoughts, type rough drafts, paste notes, or import existing manuscripts, and gently develop them into cohesive stories with chapters, scenes, characters, locked canon facts, and publication-ready exports.

---

## ⚡ Quick Start: Single-Click Windows Launch

To launch the entire application with one click on Windows, double-click:
```bat
run.bat
```
`run.bat` automatically:
1. Checks for a Python installation.
2. Creates and configures the isolated `.venv` virtual environment if needed.
3. Installs or updates dependencies from `requirements.txt`.
4. Copies `.env.example` to `.env` if no `.env` exists.
5. Displays direct links to generate your Gemini and Groq API keys.
6. Launches the application in your default browser at `http://localhost:8501`.

---

## 🔑 Direct Links to Generate API Keys

Storybook Studio works **100% offline out-of-the-box with the Mock Provider** (no API keys required). When you are ready to enable cloud AI models, generate your keys here:

| Provider | Purpose | Direct Key Generation Link | Recommended Default Model |
| :--- | :--- | :--- | :--- |
| **Google Gemini** | Primary AI Prose & Reasoning Engine | [Google AI Studio API Keys](https://aistudio.google.com/apikey) | `gemini-2.5-flash` |
| **Groq Cloud** | High-Speed Fallback Engine | [Groq Console API Keys](https://console.groq.com/keys) | `llama-3.3-70b-versatile` |

Paste your keys directly into `.env` or navigate to **Settings** in the application sidebar.

---

## 🎙️ Spoken Dictation: Fast Whisper vs. Audio Recording

### Clarification: What is Fast Whisper?
- **Faster-Whisper is strictly for Transcribing (Speech-to-Text)**: It is a CTranslate2 reimplementation of OpenAI's Whisper model that decodes audio bytes into text on your local CPU up to 4x faster with 8-bit quantization. It does **not** record audio from your microphone hardware.
- **Audio Recording**: Handled natively and privately by your browser's Web Audio microphone via Streamlit's `st.audio_input` or by uploading audio files (`.wav`, `.mp3`, `.m4a`, `.ogg`). The recorded audio is decoded locally by Faster-Whisper with zero telemetry or cloud transmission.

---

## 🛡️ Agentic RAG Rolling Memory Engine & Credit Protection

When generating a story across multiple spoken or typed sections, sending thousands of words of past transcripts into Gemini on every turn wastes API credits, burns through token limits, and triggers HTTP 429 rate limits.

Storybook Studio solves this with its **Agentic RAG Rolling Memory Engine**:
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
   Committed parts are sealed and cannot be accidentally overwritten.
6. **Rethink with Gemini**: Modify or refine the active segment by providing author feedback without re-sending or altering previous committed parts.

---

## 🎨 Soothing & Anxiety-Free Visual Design

Writing should be peaceful and reflective. The interface is styled with a natural, calming sanctuary theme:
- **Linen Background**: `#FAF8F5` replaces harsh stark whites with soft book paper.
- **Forest Sage Accents**: `#386641` buttons and borders promote focus and tranquility.
- **Soft Border Radii & Warm Shadows**: Rounded, card-like containers inspired by physical stationery.
- **Readable Typography**: High-contrast, gentle serifs and sans-serifs for effortless reading and editing.

---

## 🌟 Key Features

1. **Live Story Sanctuary**: Continuous streaming dictation and typing with Fast Whisper transcription, word targets, keyword boundary detection, and Gemini transformation.
2. **Text Input & Manuscript Import**: Freeform text editor, draft preservation, and full import support for `.txt`, `.md`, `.pdf`, and `.docx` manuscripts.
3. **AI-Assisted Story Development**: Generates loglines, synopses, thematic motifs, character goals, dramatic conflicts, and turning points.
4. **Structured Outlines & Scenes**: Generates multi-chapter outlines with scene breakdown, POV tracking, emotional shifts, dramatic beats, and reordering.
5. **Future Image & Comic Compatibility**: Natively stores visual panel metadata (`camera_framing`, `mood_atmosphere`, `visual_summary`, `characters_present`) ready for future image generation without rebuilding the engine.
6. **Story Bible & Canon Locking**: Manage characters, locations, timeline events, and lock critical facts (`is_locked`) with automatic contradiction warnings.
7. **Book View**: A distraction-reduced book reader with cover page, table of contents, font controls, reading progress, and inline prose editing.
8. **Multi-Format Exports & Safe Backups**:
   - Professional PDF book via ReportLab (with title page, table of contents, page numbers, clean margins)
   - Microsoft Word `.docx` manuscript
   - Markdown manuscript
   - Full structured JSON export
   - Safe self-contained ZIP project backup & restore with ID conflict protection and secret exclusion.
9. **Three-Tier AI Provider System**:
   - **Mock Provider**: 100% offline, zero API keys required, deterministic structured output for development and automated testing.
   - **Google Gemini**: Primary cloud provider using the official modern `google-genai` SDK.
   - **Groq**: High-speed fallback provider using the official `groq` SDK with automatic rate-limit failover.

---

## 💡 Recommended Platform Names

If you want to brand your platform or personal website, here are four curated names:

1. **HavenScribe** *(Recommended)*: Evokes a safe, tranquil harbor for writers to record their raw thoughts and watch them blossom into literature.
2. **Storybook Sanctuary**: Highlights the private, peaceful retreat feel with zero distractions and calming aesthetic.
3. **AuraStory**: Represents the gentle, radiant flow of spoken words evolving into written chapters.
4. **WhisperQuill**: Captures the synergy between fast voice dictation (Whisper) and timeless storytelling craftsmanship (Quill).

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
Or simply run `run.bat`!

---

## 🧪 Automated Test Suite

Run the full pytest suite (33 tests covering all database, models, providers, fallback logic, Agentic RAG, and exports):
```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

### Test Coverage Highlights:
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
├── run.bat                    # Single-click Windows launcher
├── requirements.txt           # Python dependencies (faster-whisper, google-genai, groq, etc.)
├── pytest.ini                 # Pytest configuration
├── .env.example               # Environment template with recommended models
├── .env                       # Local API keys (git-ignored)
├── .gitignore                 # Excludes .venv, data, logs, and secrets
├── README.md                  # Comprehensive manual and installation guide
│
├── storybook/                 # Core application package
│   ├── config.py              # Configuration manager & key masking
│   ├── database.py            # SQLite connection, schema, WAL mode, story_segments
│   ├── models.py              # Pydantic models & structured schemas
│   ├── repositories.py        # Database CRUD repositories (including StorySegmentRepository)
│   │
│   ├── providers/             # AI generation providers
│   │   ├── base.py            # BaseAIProvider abstract interface
│   │   ├── mock_provider.py   # 100% offline mock story engine
│   │   ├── gemini_provider.py # Google GenAI SDK integration
│   │   ├── groq_provider.py   # Groq SDK integration
│   │   └── provider_manager.py# Routing & fallback coordinator
│   │
│   ├── services/              # Application business logic
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
│   │   ├── live_scribe_view.py# Live Story Sanctuary (Voice & Agentic RAG)
│   │   ├── project_editor.py  # Multi-step story creation studio
│   │   ├── scene_view.py      # Scene cards & visual panel metadata
│   │   ├── book_view.py       # Book reader & inline prose editor
│   │   ├── story_bible_view.py# Characters, locations, canon facts
│   │   └── settings_view.py   # AI providers & keys manager
│   │
│   └── utils/
│       └── sample_project.py  # Seedable fictional demo project
│
├── tests/                     # Automated test suite (33 passing tests)
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
    ├── backups/               # Backup archives
    ├── exports/               # Exported files
    └── audio/                 # Captured audio recordings
```
