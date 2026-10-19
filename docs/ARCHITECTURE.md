# Storybook Studio — Technical Architecture Document

## 1. System Vision & Philosophy

**Storybook Studio** is a private, local-first personal AI-assisted story-writing and storybook application. It empowers writers to capture voice or typed ideas, develop rich narrative architecture, manage chapters and scenes, maintain world continuity, read their manuscript in a book-like interface, and export publication-ready assets (PDF, DOCX, Markdown, JSON, ZIP backups).

### Core Architectural Tenets
1. **Local-First & Private**: Stories, drafts, world bible records, and audio stay strictly local on the author's machine in SQLite. No telemetry, no public sharing, and no mandatory cloud dependencies.
2. **Offline-Capable via MockProvider**: The application starts, functions, and passes all tests completely offline with zero API keys required.
3. **Pluggable AI with Controlled Fallback**: Google Gemini serves as the primary generative provider via the current official `google-genai` SDK; Groq acts as high-speed fallback. Fallback is optional, configurable, and transparent.
4. **Draft & Prose Isolation**: Raw drafts and transcripts are permanently preserved separately from AI-generated prose.
5. **Phase 1 Boundary & Future Visual Panel Compatibility**: Excludes heavy local models, image generation, and LoRA training, while ensuring scene records natively store visual metadata (`camera_framing`, `mood_atmosphere`, `visual_summary`) ready for Phase 2 image and comic pipelines.

---

## 2. System Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                            STREAMLIT USER INTERFACE                                |
|                                                                                   |
|  +-----------------+  +-------------------+  +--------------+  +---------------+  |
|  |  Dashboard Hub  |  |  Project Studio   |  |  Scene View  |  |   Book View   |  |
|  +-----------------+  +-------------------+  +--------------+  +---------------+  |
|  +-----------------+  +-------------------+  +--------------+  +---------------+  |
|  |   Story Bible   |  | Voice Capture Hub |  | Settings Hub |  | Backup/Export |  |
|  +-----------------+  +-------------------+  +--------------+  +---------------+  |
+------------------------------------------+----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                                 SERVICES LAYER                                    |
|                                                                                   |
|  [StoryService]   [OutlineService]   [SceneService]       [StoryBibleService]     |
|  [ExportService]  [BackupService]    [ContinuityService]  [TranscriptionService]  |
+-------------------+------------------------------------------+--------------------+
                    |                                          |
                    v                                          v
+-------------------------------------+   +-----------------------------------------+
|        AI PROVIDER MANAGER          |   |           DATA ACCESS LAYER             |
|                                     |   |                                         |
| +---------------------------------+ |   | [ProjectRepo]      [ChapterRepo]        |
| | BaseAIProvider (Abstract Interface) | |   | [SceneRepo]        [SourceDraftRepo]    |
| +---------------------------------+ |   | [StoryBibleRepo]   [VersionHistoryRepo] |
|                                     |   | [AIJobRepo]                             |
|  +---------------+ +--------------+ |   +--------------------+--------------------+
|  | MockProvider  | | Gemini (SDK) | |                        |
|  +---------------+ +--------------+ |                        v
|  +---------------+                  |   +-----------------------------------------+
|  | GroqProvider  |                  |   |        LOCAL SQLITE DATABASE            |
|  +---------------+                  |   | (Foreign Keys ON, WAL Mode, Migrations) |
+-------------------------------------+   +-----------------------------------------+
```

---

## 3. Data Model & Entity Specifications

The SQLite database operates with `PRAGMA foreign_keys = ON` and `PRAGMA journal_mode = WAL` for ACID compliance and non-blocking reads.

| Entity | Primary Key | Foreign Keys | Key Attributes |
| :--- | :--- | :--- | :--- |
| **`projects`** | `id` (UUID) | None | `title`, `subtitle`, `genre`, `tone`, `premise`, `synopsis`, `metadata_json` |
| **`source_drafts`**| `id` (UUID) | `project_id` ➔ `projects.id` | `source_type` (typed/audio/import), `original_text`, `transcript_text`, `source_filename` |
| **`chapters`** | `id` (UUID) | `project_id` ➔ `projects.id` | `order_index`, `title`, `summary`, `prose`, `status` |
| **`scenes`** | `id` (UUID) | `chapter_id` ➔ `chapters.id` | `order_index`, `title`, `summary`, `prose`, `pov`, `location_name`, `camera_framing`, `mood_atmosphere`, `visual_summary` |
| **`characters`** | `id` (UUID) | `project_id` ➔ `projects.id` | `canonical_name`, `aliases_json`, `description`, `traits_json`, `relationships_json`, `locked_fields_json` |
| **`locations`** | `id` (UUID) | `project_id` ➔ `projects.id` | `name`, `description`, `rules_json` |
| **`canon_facts`** | `id` (UUID) | `project_id` ➔ `projects.id` | `category`, `subject`, `fact_text`, `is_locked` (1/0) |
| **`story_events`** | `id` (UUID)| `project_id` ➔ `projects.id` | `order_index`, `time_marker`, `description`, `related_scene_ids_json` |
| **`version_history`**| `id` (UUID)| None | `entity_type`, `entity_id`, `content_snapshot_json`, `reason` |
| **`ai_jobs`** | `id` (UUID) | `project_id` ➔ `projects.id` | `job_type`, `input_snapshot_json`, `status`, `progress_message`, `result_json` |

---

## 4. AI Provider Architecture & Fallback Protocol

### 1. Unified Interface (`BaseAIProvider`)
Every provider implements identical signatures:
- `generate_text(prompt, system_instruction)`
- `generate_story_development(premise, genre, tone, audience, notes)` ➔ `StoryDevelopmentResponse`
- `generate_outline(premise, synopsis, num_chapters)` ➔ `OutlineResponse`
- `generate_scene_breakdown(chapter_title, chapter_summary, num_scenes)` ➔ `SceneBreakdownResponse`
- `draft_scene_prose(scene, context, instructions)` ➔ `str`
- `rewrite_scene(scene_prose, instructions, tone)` ➔ `SceneRewriteResponse`
- `extract_story_bible(text)` ➔ `StoryBibleExtractionResponse`
- `review_continuity(story_bible_facts, scene_summaries)` ➔ `ContinuityReviewResponse`

### 2. Provider Implementations
- **`MockProvider`**: Complete local simulation. Returns deterministic, rich sample outputs matching all Pydantic schemas. Identifies outputs with `[Mock Provider Output]`.
- **`GeminiProvider`**: Uses the official `google-genai` SDK (`from google import genai`). Utilizes `response_mime_type="application/json"` and `response_json_schema=Model.model_json_schema()` for native schema enforcement.
- **`GroqProvider`**: Uses the official `groq` SDK (`from groq import Groq`). Utilizes `response_format={"type": "json_object"}` with strict Pydantic validation.

### 3. Fallback Policy (`ProviderManager`)
- Automatic fallback is **disabled by default**.
- When enabled (`AI_AUTO_FALLBACK=true`):
  - If Gemini raises a temporary service error (HTTP 429, Rate Limit, 503, Quota Exhaustion, Timeout) AND Groq is configured, the request is automatically routed to Groq.
  - If Gemini raises an Authentication or Invalid Key error, the system **never falls back silently**; it explains the configuration issue directly to the user.
  - Telemetry (`ProviderExecutionResult`) logs `provider_name`, `model_name`, and `fallback_used`.

---

## 5. Security, Secrets, and Privacy

1. **Environment Separation**:
   - `.env` contains local secrets and is excluded via `.gitignore`.
   - `.env.example` contains only safe comments and placeholders.
   - If `.env` exists, it is preserved and never overwritten.
2. **Key Masking**:
   - The UI displays keys masked (e.g. `AIza...4xQ`). Keys are never printed in logs or displayed raw.
3. **Export Sanitation**:
   - PDF, DOCX, Markdown, and JSON exports explicitly omit credentials.
   - The backup ZIP generator inspects payloads to reject any secret substrings.
