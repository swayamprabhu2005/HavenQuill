"""Story Structure and Scene Management View."""

import streamlit as st
from typing import List
from storybook.models import Scene, Chapter, SceneBreakdownResponse
from storybook.services.scene_service import SceneService
from storybook.services.outline_service import OutlineService
from storybook.services.story_service import StoryService
from storybook.services.export_service import export_service


def render_scene_view(
    project_id: str,
    story_service: StoryService,
    outline_service: OutlineService,
    scene_service: SceneService,
) -> None:
    """Render the detailed chapter/scene structural cards, drafting, and future visual panels."""
    project = story_service.get_project(project_id)
    if not project:
        st.error("Project not found.")
        return

    st.title(f"🎬 Scene & Story Architecture — {project.title}")
    st.caption("Manage scene cards, generate chapter breakdowns, draft narrative prose, and configure future visual panel metadata.")

    chapters = outline_service.list_chapters(project_id)
    if not chapters:
        st.info("No chapters created yet. Please create chapters in the Project Studio or generate an outline first.")
        if st.button("Go to Project Studio"):
            st.session_state["active_nav"] = "Project Studio"
            st.rerun()
        return

    # Action Toolbar
    col_act1, col_act2, col_act3 = st.columns(3)
    with col_act1:
        if st.button("➕ Add New Chapter", use_container_width=True):
            new_ch = outline_service.create_chapter(project_id, title=f"Chapter {len(chapters) + 1}")
            st.rerun()

    with col_act2:
        # Export Scene Structure JSON
        json_data = export_service.export_json(project_id)
        st.download_button(
            label="📤 Export Scenes (JSON)",
            data=str(json_data),
            file_name=f"{project.title.lower().replace(' ', '_')}_scenes.json",
            mime="application/json",
            use_container_width=True,
        )

    with col_act3:
        md_text = export_service.export_markdown(project_id)
        st.download_button(
            label="📄 Export Outline (MD)",
            data=md_text,
            file_name=f"{project.title.lower().replace(' ', '_')}_outline.md",
            mime="text/markdown",
            use_container_width=True,
        )

    st.divider()

    # Search and Filter
    search_query = st.text_input("🔍 Search scenes by title, summary, or character:", placeholder="Type to filter...")

    # Render each chapter with its scenes
    for ch_idx, chapter in enumerate(chapters, start=1):
        scenes = scene_service.list_scenes_by_chapter(chapter.id)

        # Apply search filter
        if search_query.strip():
            sq = search_query.lower()
            scenes = [
                s for s in scenes
                if sq in s.title.lower() or sq in s.summary.lower() or any(sq in c.lower() for c in s.characters_present)
            ]

        with st.expander(f"📖 Chapter {chapter.order_index}: {chapter.title} ({len(scenes)} scenes)", expanded=True):
            st.markdown(f"*{chapter.summary or 'No summary provided.'}*")

            # Chapter Actions
            c_btn1, c_btn2 = st.columns([1, 1])
            with c_btn1:
                if st.button(f"⚡ Generate Scene Breakdown (AI)", key=f"breakdown_btn_{chapter.id}"):
                    with st.spinner(f"Generating scene breakdown for '{chapter.title}'..."):
                        try:
                            exec_res = scene_service.generate_scene_breakdown_proposal(chapter.id, num_scenes=3)
                            st.session_state[f"pending_breakdown_{chapter.id}"] = exec_res.data
                            st.rerun()
                        except Exception as e:
                            st.error(f"Scene breakdown failed: {e}")

            with c_btn2:
                if st.button(f"➕ Add Scene Manually", key=f"add_sc_{chapter.id}"):
                    scene_service.create_scene(chapter.id, title=f"Scene {len(scenes) + 1}")
                    st.rerun()

            # Pending AI breakdown preview
            if f"pending_breakdown_{chapter.id}" in st.session_state:
                p_breakdown: SceneBreakdownResponse = st.session_state[f"pending_breakdown_{chapter.id}"]
                st.info(f"**AI Breakdown Preview ({len(p_breakdown.scenes)} scenes proposed):**")
                for p_sc in p_breakdown.scenes:
                    st.write(f"• **{p_sc.title}**: {p_sc.summary} *(POV: {p_sc.pov})*")

                b_col1, b_col2 = st.columns(2)
                with b_col1:
                    if st.button(f"✅ Approve & Append Scenes", key=f"app_app_{chapter.id}", type="primary"):
                        scene_service.apply_scenes_to_chapter(chapter.id, p_breakdown, overwrite_existing=False)
                        del st.session_state[f"pending_breakdown_{chapter.id}"]
                        st.rerun()
                with b_col2:
                    if st.button(f"⚠️ Replace Existing Scenes", key=f"app_rep_{chapter.id}"):
                        scene_service.apply_scenes_to_chapter(chapter.id, p_breakdown, overwrite_existing=True)
                        del st.session_state[f"pending_breakdown_{chapter.id}"]
                        st.rerun()

            st.write("")

            # Render Scene Cards
            if not scenes:
                st.caption("No scenes in this chapter yet.")
            else:
                for sc in scenes:
                    _render_scene_card(sc, scene_service, chapter)


def _render_scene_card(scene: Scene, scene_service: SceneService, chapter: Chapter) -> None:
    """Render an individual interactive scene card with full controls."""
    with st.container(border=True):
        col_header, col_reorder = st.columns([5, 1])
        with col_header:
            st.markdown(f"#### 🎬 Scene {scene.order_index}: {scene.title}")
            st.caption(
                f"**POV:** {scene.pov or 'Unassigned'} | "
                f"**Location:** {scene.location_name or 'Unspecified'} | "
                f"**Time:** {scene.time_marker or 'Unspecified'} | "
                f"**Status:** `{scene.status.upper()}`"
            )
        with col_reorder:
            b_up, b_down = st.columns(2)
            with b_up:
                if st.button("⬆️", key=f"sc_up_{scene.id}", help="Move scene up"):
                    scene_service.move_scene(scene.id, "up")
                    st.rerun()
            with b_down:
                if st.button("⬇️", key=f"sc_down_{scene.id}", help="Move scene down"):
                    scene_service.move_scene(scene.id, "down")
                    st.rerun()

        # Scene Details & Edit Form
        with st.expander("📝 View / Edit Scene Metadata & Future Visual Panel Notes", expanded=False):
            with st.form(f"edit_sc_form_{scene.id}"):
                sc_title = st.text_input("Scene Title", value=scene.title)
                sc_summary = st.text_area("Scene Summary", value=scene.summary, height=80)

                m1, m2, m3 = st.columns(3)
                with m1:
                    sc_pov = st.text_input("POV", value=scene.pov)
                with m2:
                    sc_loc = st.text_input("Location", value=scene.location_name or "")
                with m3:
                    sc_time = st.text_input("Time Marker", value=scene.time_marker)

                sc_chars = st.text_input(
                    "Characters Present (comma-separated)",
                    value=", ".join(scene.characters_present),
                )
                sc_purpose = st.text_input("Narrative Purpose", value=scene.purpose)
                sc_shift = st.text_input("Emotional Shift", value=scene.emotional_shift)

                # Future Image / Comic Generation Metadata (Phase 1 Ready)
                st.markdown("**🎨 Future Image & Comic Generation Metadata (Optional in Phase 1)**")
                v1, v2 = st.columns(2)
                with v1:
                    sc_camera = st.text_input("Camera / Framing Notes", value=scene.camera_framing or "")
                with v2:
                    sc_mood = st.text_input("Atmosphere / Lighting", value=scene.mood_atmosphere or "")
                sc_visual_sum = st.text_area("Visual Scene Description (Prompt ready)", value=scene.visual_summary or "", height=60)

                if st.form_submit_button("Save Scene Changes"):
                    scene.title = sc_title.strip()
                    scene.summary = sc_summary.strip()
                    scene.pov = sc_pov.strip()
                    scene.location_name = sc_loc.strip()
                    scene.time_marker = sc_time.strip()
                    scene.purpose = sc_purpose.strip()
                    scene.emotional_shift = sc_shift.strip()
                    scene.characters_present = [c.strip() for c in sc_chars.split(",") if c.strip()]
                    scene.camera_framing = sc_camera.strip()
                    scene.mood_atmosphere = sc_mood.strip()
                    scene.visual_summary = sc_visual_sum.strip()
                    scene_service.update_scene(scene)
                    st.success("Scene metadata saved!")
                    st.rerun()

        # Scene Prose Drafting & AI Operations
        tab_prose, tab_ai = st.tabs(["📖 Scene Prose", "✨ AI Writing Tools"])

        with tab_prose:
            prose_edit = st.text_area(
                "Prose Content:",
                value=scene.prose or "",
                height=150,
                key=f"prose_text_{scene.id}",
                placeholder="Write or draft your scene prose here...",
            )
            if prose_edit != (scene.prose or ""):
                if st.button("💾 Save Prose", key=f"save_prose_btn_{scene.id}", type="primary"):
                    scene.prose = prose_edit
                    scene_service.update_scene(scene)
                    st.success("Prose saved!")
                    st.rerun()

        with tab_ai:
            col_ai1, col_ai2 = st.columns(2)
            with col_ai1:
                st.markdown("**Draft Scene from Outline:**")
                draft_inst = st.text_input("Drafting Instructions (Optional)", key=f"dr_inst_{scene.id}", placeholder="e.g. Focus on dialogue and tension")
                if st.button("⚡ Draft Prose (AI)", key=f"draft_btn_{scene.id}"):
                    with st.spinner("Drafting scene prose..."):
                        try:
                            exec_res = scene_service.draft_scene_prose(scene.id, instructions=draft_inst)
                            st.success(f"Prose drafted via **{exec_res.provider_name.upper()}**!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Drafting error: {e}")

            with col_ai2:
                st.markdown("**Rewrite / Refine Prose:**")
                rw_inst = st.text_input("Rewrite Instructions", key=f"rw_inst_{scene.id}", placeholder="e.g. Make it more suspenseful")
                rw_tone = st.text_input("Tone Adjustment", key=f"rw_tone_{scene.id}", placeholder="e.g. Poetic, Noir")
                if st.button("✨ Rewrite Prose (AI)", key=f"rw_btn_{scene.id}"):
                    if not scene.prose:
                        st.warning("Write or draft some prose first before rewriting.")
                    else:
                        with st.spinner("Rewriting prose..."):
                            try:
                                exec_res = scene_service.rewrite_scene_prose(scene.id, instructions=rw_inst, tone=rw_tone)
                                st.success(f"Prose rewritten via **{exec_res.provider_name.upper()}**!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Rewriting error: {e}")

        # Scene Management Actions (Duplicate, Split, Delete)
        st.markdown("---")
        a1, a2, a3 = st.columns(3)
        with a1:
            if st.button("📋 Duplicate Scene", key=f"dup_{scene.id}"):
                scene_service.duplicate_scene(scene.id)
                st.rerun()
        with a2:
            with st.popover("✂️ Split Scene"):
                split_title = st.text_input("Second Scene Title", value=f"{scene.title} (Part 2)", key=f"spl_tit_{scene.id}")
                if len(scene.prose or "") > 20:
                    split_idx = st.slider("Split Character Position", 0, len(scene.prose), len(scene.prose) // 2, key=f"spl_idx_{scene.id}")
                    if st.button("Confirm Split", key=f"spl_btn_{scene.id}"):
                        scene_service.split_scene(scene.id, split_idx, split_title)
                        st.rerun()
                else:
                    st.caption("Scene prose is too short to split.")
        with a3:
            if st.button("🗑️ Delete Scene", key=f"del_sc_btn_{scene.id}"):
                scene_service.delete_scene(scene.id)
                st.rerun()
