"""Main Dashboard View for HavenQuill."""

import streamlit as st
from datetime import datetime
from storybook.models import Project
from storybook.services.story_service import StoryService
from storybook.services.transcription_service import transcription_service
from storybook.services.export_service import export_service
from storybook.services.backup_service import backup_service
from storybook.utils.sample_project import seed_sample_project_if_needed
from storybook.config import config


def render_dashboard(story_service: StoryService) -> None:
    """Render the creative dashboard and project hub."""
    # Ensure sample project is available on first launch
    seed_sample_project_if_needed()

    st.markdown(
        """
        <div style="padding: 10px 0px 20px 0px;">
            <h1 style="margin: 0; font-family: Georgia, serif; font-weight: normal; font-size: 2.4rem;">
                🪶 HavenQuill
            </h1>
            <p style="color: #6c757d; font-size: 1.05rem; margin-top: 5px;">
                Your private, local-first story & screenplay sanctuary.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Top Action Quick-Bar
    col_new, col_voice, col_import, col_backup = st.columns(4)
    with col_new:
        if st.button("✨ Create New Story", type="primary", use_container_width=True):
            st.session_state["active_view"] = "new_project_modal"
            st.rerun()

    with col_voice:
        if st.button("🎙️ Voice & Audio Capture", use_container_width=True):
            st.session_state["active_view"] = "voice_capture_hub"
            st.rerun()

    with col_import:
        if st.button("📥 Import Manuscript", use_container_width=True):
            st.session_state["active_view"] = "manuscript_import_hub"
            st.rerun()

    with col_backup:
        if st.button("📦 Backup & Restore", use_container_width=True):
            st.session_state["active_view"] = "backup_hub"
            st.rerun()

    st.divider()

    # Handle modals / sub-views triggered from top action bar
    active_subview = st.session_state.get("active_view", "dashboard")

    if active_subview == "new_project_modal":
        _render_new_project_form(story_service)
        return
    elif active_subview == "voice_capture_hub":
        _render_voice_capture_hub(story_service)
        return
    elif active_subview == "manuscript_import_hub":
        _render_manuscript_import_hub(story_service)
        return
    elif active_subview == "backup_hub":
        _render_backup_hub(story_service)
        return

    # Browse All Projects
    st.subheader("📚 Your Creative Projects")

    projects = story_service.list_projects()

    if not projects:
        st.info("No story projects found. Click **Create New Story** above or load the sample project to get started.")
        return

    for proj in projects:
        stats = story_service.get_project_stats(proj.id)
        is_sample = proj.metadata_json.get("is_sample", False)

        with st.container(border=True):
            col_info, col_stats, col_act = st.columns([5, 3, 2])

            with col_info:
                title_prefix = "🏷️ [Sample] " if is_sample else "📖 "
                st.markdown(f"### {title_prefix}{proj.title}")
                if proj.subtitle:
                    st.caption(f"*{proj.subtitle}*")
                synopsis_display = proj.synopsis or proj.premise or "No synopsis added yet."
                st.write(synopsis_display[:180] + ("..." if len(synopsis_display) > 180 else ""))

                # Tags
                st.markdown(
                    f"<small style='color: #666;'>Genre: <b>{proj.genre}</b> &bull; Tone: <b>{proj.tone}</b> &bull; Language: <b>{proj.language}</b></small>",
                    unsafe_allow_html=True,
                )

            with col_stats:
                st.write("**Story Progress**")
                st.write(f"• **{stats['chapter_count']}** Chapters")
                st.write(f"• **{stats['scene_count']}** Scenes")
                st.write(f"• **{stats['character_count']}** Characters")
                st.caption(f"Last updated: {proj.updated_at[:10]}")

                st.write("&nbsp;")
                if st.button("📖 Read Book", key=f"read_{proj.id}", type="primary", use_container_width=True):
                    st.session_state["selected_project_id"] = proj.id
                    st.session_state["active_nav"] = "📖 Book View"
                    st.rerun()

                if st.button("🎬 Script View", key=f"script_{proj.id}", use_container_width=True):
                    st.session_state["selected_project_id"] = proj.id
                    st.session_state["active_nav"] = "🎬 Script View"
                    st.rerun()

                if st.button("✍️ Studio", key=f"open_{proj.id}", use_container_width=True):
                    st.session_state["selected_project_id"] = proj.id
                    st.session_state["active_nav"] = "✍️ Story Studio"
                    st.rerun()


def _render_new_project_form(story_service: StoryService) -> None:
    """Guided form for creating a new story project."""
    st.subheader("✨ Create a New Story Project")
    st.caption("Step 1: Define the core creative foundation for your story.")

    with st.form("create_project_form"):
        title = st.text_input("Story Title*", placeholder="e.g. The Silver Compass")
        subtitle = st.text_input("Subtitle / Tagline (Optional)", placeholder="e.g. A Tale of Lost Stars")

        col1, col2, col3 = st.columns(3)
        with col1:
            genre = st.text_input("Genre", value="Speculative Fiction")
        with col2:
            tone = st.text_input("Tone", value="Atmospheric and Thoughtful")
        with col3:
            language = st.text_input("Language", value="English")

        audience = st.text_input("Intended Audience", placeholder="e.g. Young Adult, Mystery Lovers, General Fiction")
        premise = st.text_area(
            "Premise / Core Idea*",
            placeholder="What is the central concept, protagonist, and driving tension of this story?",
            height=120,
        )

        submitted = st.form_submit_button("Create Project", type="primary")
        if submitted:
            if not title.strip() or not premise.strip():
                st.error("Please provide both a Title and a Premise to initialize your story.")
            else:
                new_proj = story_service.create_project(
                    title=title,
                    subtitle=subtitle,
                    genre=genre,
                    tone=tone,
                    language=language,
                    intended_audience=audience,
                    premise=premise,
                )
                st.session_state["selected_project_id"] = new_proj.id
                st.session_state["active_nav"] = "📖 Book View"
                st.session_state["active_view"] = "dashboard"
                st.success(f"Project '{new_proj.title}' created successfully!")
                st.rerun()

    if st.button("← Cancel", use_container_width=False):
        st.session_state["active_view"] = "dashboard"
        st.rerun()


def _render_voice_capture_hub(story_service: StoryService) -> None:
    """Voice recording and audio transcription workspace."""
    st.subheader("🎙️ Voice & Audio Capture")
    st.caption("Speak your ideas or upload recordings. Review and edit the transcript before saving.")

    projects = story_service.list_projects()
    if not projects:
        st.warning("Please create at least one project before recording or capturing audio.")
        if st.button("← Back to Dashboard"):
            st.session_state["active_view"] = "dashboard"
            st.rerun()
        return

    project_map = {f"{p.title} ({p.genre})": p.id for p in projects}
    selected_label = st.selectbox("Assign Audio To Project:", list(project_map.keys()))
    target_project_id = project_map[selected_label]

    st.markdown("---")

    # Native Browser Audio Recording & Upload
    tab_record, tab_upload = st.tabs(["🔴 Microphone Recording", "📁 Upload Audio File"])
    audio_bytes = None
    audio_name = "recording.wav"

    with tab_record:
        st.markdown("**Record directly in your browser:**")
        # Streamlit 1.39+ native audio input component
        if hasattr(st, "audio_input"):
            rec_audio = st.audio_input("Click to record your voice:")
            if rec_audio:
                audio_bytes = rec_audio.read()
                audio_name = "mic_recording.wav"
                st.audio(audio_bytes, format="audio/wav")
        else:
            st.info("Browser microphone capture: Use the Upload tab to upload any WAV, MP3, or M4A recording.")

    with tab_upload:
        st.markdown("**Upload a voice memo or audio recording:**")
        uploaded_file = st.file_uploader(
            "Choose an audio file",
            type=["wav", "mp3", "m4a", "ogg"],
            help="Supported: WAV, MP3, M4A, OGG",
        )
        if uploaded_file:
            audio_bytes = uploaded_file.read()
            audio_name = uploaded_file.name
            st.audio(audio_bytes)

    st.markdown("---")

    # Transcription review area
    st.subheader("Review & Edit Transcript")
    if "working_transcript" not in st.session_state:
        st.session_state["working_transcript"] = ""

    col_btn, col_info = st.columns([1, 2])
    with col_btn:
        if audio_bytes and st.button("Transcribe Audio", type="primary"):
            with st.spinner("Processing speech transcription..."):
                try:
                    text, provider = transcription_service.transcribe_audio(audio_bytes, filename=audio_name)
                    st.session_state["working_transcript"] = text
                    st.success(f"Transcribed via provider: **{provider.upper()}**")
                except Exception as e:
                    st.error(f"Transcription failed: {e}")

    with col_info:
        st.caption(f"Configured Engine: **{config.transcription_provider.upper()}** (Cloud: {'Enabled' if config.enable_cloud_transcription else 'Disabled'})")

    edited_transcript = st.text_area(
        "Transcript (Review and refine before saving):",
        value=st.session_state.get("working_transcript", ""),
        height=180,
    )

    if st.button("💾 Save Transcript as Source Draft", type="primary"):
        if not edited_transcript.strip():
            st.error("Please enter or transcribe some text before saving.")
        else:
            draft = story_service.save_source_draft(
                project_id=target_project_id,
                source_type="audio",
                original_text=edited_transcript.strip(),
                transcript_text=edited_transcript.strip(),
                source_filename=audio_name,
            )
            st.success(f"Saved transcript draft to project! (Draft ID: {draft.id[:8]})")
            st.session_state["working_transcript"] = ""

    if st.button("← Back to Dashboard"):
        st.session_state["active_view"] = "dashboard"
        st.rerun()


def _render_manuscript_import_hub(story_service: StoryService) -> None:
    """Manuscript import tool supporting TXT, Markdown, PDF, and DOCX."""
    st.subheader("📥 Import Existing Manuscript or Draft")
    st.caption("Import text from .txt, .md, .pdf, or .docx files without losing your original content.")

    projects = story_service.list_projects()
    if not projects:
        st.warning("Please create a project first before importing a manuscript.")
        if st.button("← Back to Dashboard"):
            st.session_state["active_view"] = "dashboard"
            st.rerun()
        return

    project_map = {f"{p.title} ({p.genre})": p.id for p in projects}
    selected_label = st.selectbox("Import Into Project:", list(project_map.keys()))
    target_project_id = project_map[selected_label]

    uploaded_doc = st.file_uploader(
        "Select manuscript file",
        type=["txt", "md", "pdf", "docx"],
        help="Extract text from standard manuscripts, research notes, or outlines.",
    )

    if uploaded_doc:
        doc_bytes = uploaded_doc.read()
        try:
            extracted_text, detected_fmt = export_service.extract_text_from_file(uploaded_doc.name, doc_bytes)
            st.success(f"Extracted {len(extracted_text)} characters (Format: {detected_fmt.upper()}).")

            st.subheader("Preview Extracted Content")
            preview_text = st.text_area("Extracted Manuscript Preview:", value=extracted_text, height=250)

            col1, col2 = st.columns([1, 2])
            with col1:
                if st.button("Confirm & Save as Source Draft", type="primary"):
                    draft = story_service.save_source_draft(
                        project_id=target_project_id,
                        source_type=f"imported_{detected_fmt}",
                        original_text=preview_text,
                        source_filename=uploaded_doc.name,
                    )
                    st.success(f"Manuscript saved as source draft! (ID: {draft.id[:8]})")
        except Exception as e:
            st.error(f"Error parsing file: {e}")

    if st.button("← Back to Dashboard"):
        st.session_state["active_view"] = "dashboard"
        st.rerun()


def _render_backup_hub(story_service: StoryService) -> None:
    """Project backup and safe restore workspace."""
    st.subheader("📦 Project Backup & Safe Restore")
    st.caption("Export full self-contained project archives (ZIP) or restore saved projects safely.")

    tab_backup, tab_restore = st.tabs(["⬇️ Export Project Archive", "⬆️ Restore Project Archive"])

    with tab_backup:
        projects = story_service.list_projects()
        if not projects:
            st.info("No projects to back up.")
        else:
            project_map = {p.title: p.id for p in projects}
            chosen_proj_name = st.selectbox("Select Project to Back Up:", list(project_map.keys()))
            chosen_id = project_map[chosen_proj_name]

            zip_bytes = backup_service.create_project_backup(chosen_id)
            st.download_button(
                label=f"💾 Download {chosen_proj_name} Archive (.zip)",
                data=zip_bytes,
                file_name=f"{chosen_proj_name.lower().replace(' ', '_')}_backup.zip",
                mime="application/zip",
                type="primary",
            )
            st.info("Archive contains complete project JSON, characters, locations, canon facts, and markdown manuscript.")

    with tab_restore:
        st.markdown("**Restore a project from a HavenQuill ZIP archive:**")
        uploaded_zip = st.file_uploader("Upload .zip backup", type=["zip"])
        if uploaded_zip:
            zip_bytes = uploaded_zip.read()
            preview = backup_service.preview_backup(zip_bytes)

            if not preview.get("valid"):
                st.error(f"Invalid backup archive: {preview.get('error')}")
            else:
                st.success("Valid Project Archive Verified!")
                st.write(f"• **Title:** {preview['title']}")
                st.write(f"• **Genre:** {preview['genre']}")
                st.write(f"• **Chapters:** {preview['chapter_count']} | **Scenes:** {preview['scene_count']}")
                st.write(f"• **Characters:** {preview['character_count']}")

                overwrite = st.checkbox("Overwrite if project with same ID exists (otherwise imports as copy)")

                if st.button("Confirm and Restore Project", type="primary"):
                    restored = backup_service.restore_project(preview["data"], overwrite_existing=overwrite)
                    st.success(f"Project '{restored.title}' restored successfully!")
                    st.session_state["selected_project_id"] = restored.id
                    st.session_state["active_nav"] = "📖 Book View"
                    st.session_state["active_view"] = "dashboard"
                    st.rerun()

    if st.button("← Back to Dashboard"):
        st.session_state["active_view"] = "dashboard"
        st.rerun()
