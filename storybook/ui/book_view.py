"""Book View providing a readable, elegant book-like reading and inline editing experience."""

import streamlit as st
import math
from storybook.services.story_service import StoryService
from storybook.services.outline_service import OutlineService
from storybook.services.scene_service import SceneService
from storybook.services.export_service import export_service


def render_book_view(
    project_id: str,
    story_service: StoryService,
    outline_service: OutlineService,
    scene_service: SceneService,
) -> None:
    """Render the readable book-like reader with typography controls and inline editing."""
    project = story_service.get_project(project_id)
    if not project:
        st.error("Project not found.")
        return

    chapters = outline_service.list_chapters(project_id)
    if not chapters:
        st.info("Your book has no chapters yet. Please add chapters in Project Studio or Scene View.")
        return

    # Reading & Typography Controls Toolbar
    with st.container(border=True):
        c_font, c_fam, c_distract, c_pdf = st.columns([2, 2, 2, 2])
        with c_font:
            font_size = st.select_slider(
                "Typography Size",
                options=["16px", "18px", "20px", "24px"],
                value="18px",
            )
        with c_fam:
            font_family = st.selectbox(
                "Font Style",
                options=["Georgia, serif", "'Times New Roman', serif", "'Segoe UI', sans-serif", "'Garamond', serif"],
                index=0,
            )
        with c_distract:
            distraction_free = st.toggle("Distraction-Free Mode", value=False)
        with c_pdf:
            st.write("&nbsp;")
            try:
                pdf_bytes = export_service.export_pdf(project_id)
                st.download_button(
                    label="📄 Export PDF Book",
                    data=pdf_bytes,
                    file_name=f"{project.title.lower().replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.caption("PDF generation ready")

    # Estimate word count & pages
    total_words = 0
    for ch in chapters:
        scenes = scene_service.list_scenes_by_chapter(ch.id)
        if scenes:
            for sc in scenes:
                total_words += len((sc.prose or "").split())
        else:
            total_words += len((ch.prose or "").split())

    est_pages = max(1, math.ceil(total_words / 250))

    if not distraction_free:
        st.caption(f"Estimated Length: **~{total_words:,} words** (~{est_pages} book pages)")

    # Chapter Navigation
    chapter_titles = ["📖 Title Page & Table of Contents"] + [f"Chapter {c.order_index}: {c.title}" for c in chapters]

    if "current_book_chapter_idx" not in st.session_state:
        st.session_state["current_book_chapter_idx"] = 0

    curr_idx = st.session_state["current_book_chapter_idx"]

    # Prev / Next navigation
    nav_col1, nav_col2, nav_col3 = st.columns([1, 4, 1])
    with nav_col1:
        if st.button("← Previous", disabled=(curr_idx == 0), use_container_width=True):
            st.session_state["current_book_chapter_idx"] = max(0, curr_idx - 1)
            st.rerun()

    with nav_col2:
        selected_nav = st.selectbox(
            "Jump to Chapter:",
            chapter_titles,
            index=curr_idx,
            label_visibility="collapsed",
        )
        new_nav_idx = chapter_titles.index(selected_nav)
        if new_nav_idx != curr_idx:
            st.session_state["current_book_chapter_idx"] = new_nav_idx
            st.rerun()

    with nav_col3:
        if st.button("Next →", disabled=(curr_idx >= len(chapter_titles) - 1), use_container_width=True):
            st.session_state["current_book_chapter_idx"] = min(len(chapter_titles) - 1, curr_idx + 1)
            st.rerun()

    # Progress bar
    progress_val = curr_idx / max(1, len(chapter_titles) - 1)
    st.progress(progress_val, text=f"Reading Progress: {int(progress_val * 100)}%")

    st.markdown("---")

    # Render Active Section
    if curr_idx == 0:
        # Title Page & Table of Contents
        st.markdown(
            f"""
            <div style="text-align: center; padding: 40px 20px; font-family: {font_family};">
                <h1 style="font-size: 2.8rem; margin-bottom: 10px; font-weight: 600;">{project.title}</h1>
                <p style="font-size: 1.3rem; color: #555; font-style: italic;">{project.subtitle or ''}</p>
                <div style="margin: 30px auto; width: 60px; height: 2px; background: #999;"></div>
                <p style="font-size: 1rem; color: #777;">
                    <b>Genre:</b> {project.genre} &nbsp;&bull;&nbsp; <b>Tone:</b> {project.tone}
                </p>
                <div style="max-width: 650px; margin: 40px auto; text-align: justify; line-height: 1.7; font-size: 1.05rem;">
                    <b>Synopsis:</b><br/>{project.synopsis or project.premise or 'No synopsis available.'}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("📑 Table of Contents")
        for i, ch in enumerate(chapters, start=1):
            with st.container(border=True):
                st.markdown(f"**Chapter {ch.order_index}: {ch.title}**")
                if ch.summary:
                    st.caption(ch.summary)
                if st.button(f"Read Chapter {ch.order_index}", key=f"read_ch_btn_{ch.id}"):
                    st.session_state["current_book_chapter_idx"] = i
                    st.rerun()

    else:
        # Chapter Reading Mode
        active_chapter = chapters[curr_idx - 1]
        scenes = scene_service.list_scenes_by_chapter(active_chapter.id)

        st.markdown(
            f"""
            <div style="text-align: center; margin-bottom: 25px; font-family: {font_family};">
                <h2 style="font-size: 2rem; margin-bottom: 5px;">{active_chapter.title}</h2>
                <p style="color: #666; font-style: italic;">{active_chapter.summary or ''}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if not scenes:
            # Inline edit for chapter prose
            st.markdown(f"<div style='font-family: {font_family}; font-size: {font_size}; line-height: 1.8;'>", unsafe_allow_html=True)
            prose_val = st.text_area(
                "Chapter Prose (Editable):",
                value=active_chapter.prose or "",
                height=300,
                key=f"ch_prose_edit_{active_chapter.id}",
            )
            st.markdown("</div>", unsafe_allow_html=True)

            if prose_val != (active_chapter.prose or ""):
                if st.button("💾 Save Changes", key=f"save_ch_book_{active_chapter.id}", type="primary"):
                    active_chapter.prose = prose_val
                    outline_service.update_chapter(active_chapter)
                    st.success("Chapter prose saved!")
                    st.rerun()
        else:
            for sc in scenes:
                st.markdown(f"### {sc.title}")
                if sc.summary:
                    st.caption(f"*{sc.summary}*")

                st.markdown(f"<div style='font-family: {font_family}; font-size: {font_size}; line-height: 1.8;'>", unsafe_allow_html=True)
                sc_prose_val = st.text_area(
                    f"Scene Prose (Editable)",
                    value=sc.prose or "",
                    height=200,
                    key=f"book_sc_prose_{sc.id}",
                    placeholder="Enter or edit prose here...",
                )
                st.markdown("</div>", unsafe_allow_html=True)

                if sc_prose_val != (sc.prose or ""):
                    if st.button("💾 Save Scene Prose", key=f"save_sc_book_{sc.id}", type="primary"):
                        sc.prose = sc_prose_val
                        scene_service.update_scene(sc)
                        st.success("Scene prose saved!")
                        st.rerun()

                st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
