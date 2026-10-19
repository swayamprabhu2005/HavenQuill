"""Live Story Sanctuary — Voice dictation, Fast Whisper transcription, and Agentic RAG flow."""

import streamlit as st
from storybook.services.agentic_rag_service import agentic_rag_service
from storybook.services.transcription_service import transcription_service
from storybook.services.story_service import StoryService
from storybook.services.outline_service import OutlineService
from storybook.services.scene_service import SceneService
from storybook.config import config


def render_live_scribe_view(
    project_id: str,
    story_service: StoryService,
    outline_service: OutlineService,
    scene_service: SceneService,
) -> None:
    """Render the soothing, continuous story dictation and Agentic RAG live writing room."""
    project = story_service.get_project(project_id)
    if not project:
        st.error("Project not found.")
        return

    # Calming Header
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #F5F7F5 0%, #EBF1ED 100%); padding: 24px 30px; border-radius: 12px; margin-bottom: 25px; border-left: 5px solid #4A7C59;">
            <h2 style="font-family: Georgia, serif; color: #2D4A34; margin: 0; font-size: 1.9rem;">
                🌿 Live Story Sanctuary & Flow
            </h2>
            <p style="color: #4A6B53; margin: 6px 0 0 0; font-size: 1.05rem;">
                Speak freely or type in peaceful intervals. Fast Whisper transcribes your voice, 
                and Gemini shapes each paragraph into story prose with Agentic RAG rolling memory.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Word threshold configuration
    col_cfg1, col_cfg2, col_cfg3 = st.columns([2, 2, 2])
    with col_cfg1:
        target_words = st.selectbox(
            "Segment Target (Word Limit):",
            [300, 500, 1000],
            index=0,
            help="When your spoken or typed draft approaches this limit, finalize and craft with Gemini.",
        )
    with col_cfg2:
        engine_label = {
            "faster_whisper": "Fast Whisper (Local CPU / No Key Needed)",
            "groq": "Groq Whisper (Cloud / Ultra-Fast)",
            "gemini": "Gemini Multimodal Speech",
            "mock": "Mock Engine (Offline Demo)",
            "none": "Manual Typing Only",
        }.get(config.transcription_provider, config.transcription_provider.upper())
        st.info(f"🎙️ **Transcriber:** {engine_label}")
    with col_cfg3:
        st.success(f"🤖 **Prose AI:** {config.ai_provider.upper()} ({config.gemini_model if config.ai_provider == 'gemini' else config.groq_model})")

    st.divider()

    # Retrieve all segments
    all_segments = agentic_rag_service.segment_repo.list_by_project(project_id)
    committed_segments = [s for s in all_segments if s.status == "processed"]
    active_segment = agentic_rag_service.get_or_create_active_segment(project_id)

    # Render Stream of Committed Parts (Book Pages Style)
    if committed_segments:
        st.subheader("📖 The Continuous Story Stream")
        for seg in committed_segments:
            with st.container(border=True):
                st.markdown(
                    f"""
                    <div style="background-color: #F8FAF9; padding: 10px 16px; border-radius: 8px; border-left: 4px solid #3E7B54; margin-bottom: 12px;">
                        <span style="font-weight: 600; color: #2D5A3A;">✓ [Committed to Story Canon — Part {seg.segment_index}]</span>
                        <span style="color: #666; font-size: 0.85rem; float: right;">Raw Draft: {seg.word_count} words &bull; {seg.created_at[:16]}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                col_raw, col_prose = st.columns([1, 2])
                with col_raw:
                    st.caption("🎙️ **Author's Spoken / Raw Input:**")
                    st.markdown(f"<small style='color: #555;'><i>\"{seg.raw_input}\"</i></small>", unsafe_allow_html=True)
                with col_prose:
                    st.caption("✨ **Gemini Crafted Story Prose:**")
                    st.markdown(f"<div style='font-family: Georgia, serif; line-height: 1.7; font-size: 1.05rem;'>{seg.generated_prose}</div>", unsafe_allow_html=True)

            st.markdown(
                """
                <div style="text-align: center; margin: 15px 0;">
                    <span style="color: #A0B2A6; font-size: 1.2rem;">&bull; &bull; &bull;</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ACTIVE SEGMENT WORKSPACE
    st.markdown(f"### ✍️ Part {active_segment.segment_index}: Active Creative Segment")
    st.caption("Record voice notes or type below. When ready or when you say **'para end'**, transform it into story prose.")

    # Native Browser Audio Recording & Upload
    tab_rec, tab_upload = st.tabs(["🔴 Microphone Dictation", "📁 Audio File Upload"])
    audio_captured = None
    audio_filename = f"part_{active_segment.segment_index}.wav"

    with tab_rec:
        if hasattr(st, "audio_input"):
            mic_data = st.audio_input(f"Click to record voice for Part {active_segment.segment_index}:", key=f"mic_{active_segment.id}")
            if mic_data:
                audio_captured = mic_data.read()
                st.audio(audio_captured, format="audio/wav")
        else:
            st.info("Browser microphone: Upload an audio clip in the tab to the right.")

    with tab_upload:
        uploaded_audio = st.file_uploader(
            "Upload voice clip",
            type=["wav", "mp3", "m4a", "ogg"],
            key=f"upload_{active_segment.id}",
        )
        if uploaded_audio:
            audio_captured = uploaded_audio.read()
            audio_filename = uploaded_audio.name
            st.audio(audio_captured)

    # Transcribe Button
    if audio_captured and st.button(f"⚡ Transcribe with Fast Whisper", key=f"trans_btn_{active_segment.id}", type="primary"):
        with st.spinner("Transcribing speech with Fast Whisper..."):
            try:
                transcript_text, prov_used = transcription_service.transcribe_audio(audio_captured, filename=audio_filename)
                # Check for verbal keyword 'para end'
                has_kw, cleaned_text = agentic_rag_service.check_keyword_boundary(transcript_text)
                agentic_rag_service.append_text_to_active_segment(project_id, cleaned_text)
                if has_kw:
                    st.success(f"Detected keyword boundary! Appended to Part {active_segment.segment_index} and ready to craft.")
                else:
                    st.success(f"Transcribed via **{prov_used.upper()}** and appended to Part {active_segment.segment_index}!")
                st.rerun()
            except Exception as e:
                st.error(f"Transcription error: {e}")

    # Editable Segment Text Area
    curr_words = len(active_segment.raw_input.split()) if active_segment.raw_input else 0
    progress_ratio = min(1.0, curr_words / target_words)

    st.progress(progress_ratio, text=f"Segment Length: {curr_words} / {target_words} words ({int(progress_ratio * 100)}%)")

    raw_edit = st.text_area(
        f"Raw Thoughts for Part {active_segment.segment_index} (Editable / Dictated):",
        value=active_segment.raw_input or "",
        height=140,
        placeholder="Type notes or dictate using the recorder above. You can also say 'para end' to mark boundaries.",
        key=f"raw_edit_{active_segment.id}",
    )

    if raw_edit != (active_segment.raw_input or ""):
        if st.button("💾 Save Text Edits", key=f"save_raw_{active_segment.id}"):
            active_segment.raw_input = raw_edit
            active_segment.word_count = len(raw_edit.split())
            agentic_rag_service.segment_repo.update(active_segment)
            st.success("Draft text saved!")
            st.rerun()

    # Agentic Context Preview & Token Saving Telemetry
    rag_preview = agentic_rag_service.build_agentic_rag_context(project_id, active_segment)
    saved_tokens = rag_preview["estimated_words_saved"] * 1.3  # approx token ratio
    st.markdown(
        f"""
        <div style="background-color: #F1F6F2; padding: 10px 16px; border-radius: 8px; font-size: 0.9rem; color: #2E5338; margin: 12px 0;">
            🛡️ <b>Agentic RAG Credit Protection Active:</b> 
            Rolling recap bridge ready. Saving ~<b>{int(saved_tokens):,} tokens</b> by distilling previous committed parts instead of re-sending full history.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Transform & Rethink Action Buttons
    col_btn_gen, col_btn_rethink = st.columns(2)
    with col_btn_gen:
        if st.button(f"✨ Transform Part {active_segment.segment_index} with Gemini", key=f"proc_gemini_{active_segment.id}", type="primary", use_container_width=True):
            if not active_segment.raw_input.strip():
                st.warning("Please dictate or type thoughts into the active segment first.")
            else:
                with st.spinner(f"Crafting polished story prose for Part {active_segment.segment_index}..."):
                    try:
                        res = agentic_rag_service.process_segment_with_ai(project_id, active_segment.id)
                        st.success(f"Part {active_segment.segment_index} committed via **{res.provider_name.upper()}**!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Prose generation error: {e}")

    with col_btn_rethink:
        with st.popover("🔄 Rethink Active Part with Gemini"):
            rethink_notes = st.text_input("Special revision guidance (Optional):", placeholder="e.g. Heighten the suspense, more sensory details")
            if st.button("Confirm Rethink", key=f"rethink_btn_{active_segment.id}"):
                with st.spinner("Rethinking segment with Gemini..."):
                    try:
                        res = agentic_rag_service.rethink_segment(project_id, active_segment.id, feedback=rethink_notes)
                        st.success(f"Rethought via {res.provider_name.upper()}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Rethink error: {e}")

    # Transfer to Project Chapters
    if committed_segments:
        st.markdown("---")
        with st.expander("📦 Commit Live Flow to Project Chapters & Book View"):
            st.caption("Merge all committed parts from this live session into a chapter for the Book View.")
            target_ch_title = st.text_input("Chapter Title:", value=f"Live Session Chapter ({len(committed_segments)} parts)")
            if st.button("Convert to Book Chapter", type="primary"):
                # Combine all committed prose into a chapter
                full_prose = "\n\n".join(s.generated_prose for s in committed_segments if s.generated_prose)
                ch = outline_service.create_chapter(project_id, title=target_ch_title, summary="Drafted in Live Sanctuary Session")
                ch.prose = full_prose
                outline_service.update_chapter(ch)
                st.success(f"Created '{target_ch_title}' in Book View! Open Book View to read.")
