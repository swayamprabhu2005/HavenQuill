# HavenQuill — Phase 2: Future LoRA Image Pipeline

This orphan branch (`lora-docs`) contains research, documentation, and roadmap guides for the future Phase 2 image generation and character-consistency pipeline.

It is maintained separately from the `main` branch so the core HavenQuill story and screenplay studio remains clean, lightweight, and independent of heavy machine learning and diffusion dependencies.

---

## Overview

The goal of Phase 2 is to take structured story and screenplay exports from HavenQuill (character profiles, scene descriptions, mood, and framing) and generate character-consistent comic panels using custom Low-Rank Adaptation (LoRA) adapters with diffusion models.

### Key Concepts
- **Character LoRA**: Parameter-efficient adapter weights trained on an original character's visual sheet to lock in facial features, hairstyle, and attire across different camera angles and expressions.
- **Style LoRA**: Trained separately after character consistency is achieved to apply a cohesive illustration style without entangling identity.
- **Decoupled Architecture**: HavenQuill provides text and scene JSON metadata. Image generation runs independently via an `ImageProvider` abstraction, and typography/speech bubbles are laid out in software rather than generated directly by the diffusion model.

---

## Planned Hardware & Environment

- **Target Local Hardware**: Laptop with NVIDIA RTX 4060 GPU (8 GB VRAM), 16 GB RAM, and 512 GB SSD.
- **Cloud Training**: Google Colab (GPU runtime) paired with Google Drive for checkpoint storage and evaluation grids.
- **Recommended Model Baseline**: Stable Diffusion 1.5 with Hugging Face Diffusers (conservative resolution, batch size 1, gradient checkpointing, and mixed precision to fit comfortably within 8 GB VRAM).

---

## Step-by-Step Implementation Roadmap

1. **Prerequisite**: Keep Phase 1 story and screenplay generation fully stable and tested on `main`.
2. **Character Sheet Creation**: Create multi-angle reference sheets (front, side, three-quarter, expressions, poses) for original characters.
3. **Dataset Curation & Captions**:
   - Collect high-quality, varied images with strict rights and licensing.
   - Write descriptive captions using a unique trigger token (e.g., `ohwx_character`).
4. **LoRA Fine-Tuning**:
   - Run small test runs and save checkpoints.
   - Evaluate identity preservation on held-out test prompts before committing to long training runs.
5. **HavenQuill Integration**:
   - Implement an `ImageProvider` interface (`generate_panel()`, `load_adapter()`).
   - Assemble panels into comic pages and overlay dialogue and captions.

---

## Reference Document

For the comprehensive, unabridged technical guide—including training hyperparameters, memory optimizations, troubleshooting out-of-memory errors, licensing and safety rules, and copyable prompts:

📄 **`Future LoRA Training Guide.docx`** (included in this branch)
