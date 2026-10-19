# Scene Export Schema Specification (Phase 1 & Future Compatibility)

## Overview

Storybook Studio is designed local-first with Phase 1 focusing exclusively on text narrative, story architecture, scene breakdown, continuity tracking, and manuscript rendering.

Per project requirements, **image generation, comic panel generation, LoRA training, and video generation are explicitly excluded from Phase 1**. However, the scene records and export schema are designed from the foundation so that Phase 2 can generate image prompts and comic book panels directly from saved scenes without altering the database schema or rebuilding the story engine.

---

## Complete JSON Scene Export Schema

The root project export produces a JSON package containing metadata, the Story Bible, and ordered chapters with nested scene records.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StorybookStudioProjectExport",
  "type": "object",
  "required": ["schema_version", "project", "story_bible", "chapters"],
  "properties": {
    "schema_version": {
      "type": "string",
      "enum": ["1.0.0"]
    },
    "project": {
      "type": "object",
      "required": ["id", "title", "genre", "premise"],
      "properties": {
        "id": { "type": "string", "format": "uuid" },
        "title": { "type": "string" },
        "subtitle": { "type": "string" },
        "genre": { "type": "string" },
        "tone": { "type": "string" },
        "language": { "type": "string" },
        "intended_audience": { "type": "string" },
        "premise": { "type": "string" },
        "synopsis": { "type": "string" },
        "created_at": { "type": "string", "format": "date-time" },
        "updated_at": { "type": "string", "format": "date-time" }
      }
    },
    "story_bible": {
      "type": "object",
      "properties": {
        "characters": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["id", "canonical_name"],
            "properties": {
              "id": { "type": "string" },
              "canonical_name": { "type": "string" },
              "aliases_json": { "type": "array", "items": { "type": "string" } },
              "description": { "type": "string" },
              "traits_json": { "type": "array", "items": { "type": "string" } },
              "relationships_json": { "type": "object" },
              "locked_fields_json": { "type": "array", "items": { "type": "string" } }
            }
          }
        },
        "locations": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "id": { "type": "string" },
              "name": { "type": "string" },
              "description": { "type": "string" },
              "rules_json": { "type": "array", "items": { "type": "string" } }
            }
          }
        },
        "canon_facts": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "id": { "type": "string" },
              "category": { "type": "string" },
              "subject": { "type": "string" },
              "fact_text": { "type": "string" },
              "is_locked": { "type": "boolean" }
            }
          }
        }
      }
    },
    "chapters": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "order_index", "title", "scenes"],
        "properties": {
          "id": { "type": "string" },
          "order_index": { "type": "integer" },
          "title": { "type": "string" },
          "summary": { "type": "string" },
          "prose": { "type": "string" },
          "status": { "type": "string" },
          "scenes": {
            "type": "array",
            "items": { "$ref": "#/definitions/SceneRecord" }
          }
        }
      }
    }
  },
  "definitions": {
    "SceneRecord": {
      "type": "object",
      "required": [
        "id",
        "order_index",
        "title",
        "summary",
        "prose",
        "characters_present",
        "visual_metadata"
      ],
      "properties": {
        "id": { "type": "string", "format": "uuid" },
        "order_index": { "type": "integer" },
        "title": { "type": "string" },
        "summary": { "type": "string" },
        "prose": { "type": "string" },
        "purpose": { "type": "string" },
        "pov": { "type": "string" },
        "location_name": { "type": "string" },
        "time_marker": { "type": "string" },
        "characters_present": {
          "type": "array",
          "items": { "type": "string" }
        },
        "dramatic_conflict": { "type": "string" },
        "emotional_shift": { "type": "string" },
        "continuity": { "type": "object" },
        "status": { "type": "string" },

        "visual_metadata": {
          "type": "object",
          "description": "Schema contract for future image & comic panel generation engines (Phase 2)",
          "properties": {
            "camera_framing": {
              "type": "string",
              "description": "Cinematic framing (e.g. 'Close-up on hands', 'Dutch angle wide shot', 'Eye-level two-shot')"
            },
            "mood_atmosphere": {
              "type": "string",
              "description": "Lighting, weather, and color palette (e.g. 'Chiaroscuro amber lantern glow against cold stone shadows')"
            },
            "visual_summary": {
              "type": "string",
              "description": "Synthesized visual prompt describing the physical scene composition"
            },
            "character_visual_refs": {
              "type": "array",
              "items": { "type": "string" },
              "description": "List of character IDs or canonical names appearing in this visual panel"
            }
          }
        }
      }
    }
  }
}
```

---

## Phase 2 Future Pipeline Integration Notes

1. **Zero Schema Migration Required**: The SQLite `scenes` table already includes `camera_framing`, `mood_atmosphere`, `visual_summary`, and `characters_present`.
2. **Comic Panel Extraction**: A single scene record maps 1:1 to either a keyframe illustration or can be subdivided into panels using the dialogue and action beats preserved in `prose` and `visual_metadata`.
3. **Consistency**: Character visual consistency in Phase 2 can query `story_bible.characters[canonical_name].description` directly as an anchor prompt alongside `visual_metadata.camera_framing`.
