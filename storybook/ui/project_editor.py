"""Project Editor and Guided Story Development Workflow."""

import streamlit as st
from storybook.services.story_service import StoryService
from storybook.services.outline_service import OutlineService
from storybook.services.continuity_service import ContinuityService
from storybook.models import Project, OutlineResponse


def render_project_editor(
    project_id: str,
    story_service: StoryService,
    outline_service: OutlineService,
    continuity_service: ContinuityService,
) -> None:
    """Render the guided multi-step story development workspace."""
    project = story_service.get_project(project_id)
    if not project:
        st.error("Project not found.")
        return

    # Header
    col_t, col_b = st.columns([4, 1])
    with col_t:
        st.title(f"✍️ {project.title}")
        if project.subtitle:
            st.caption(f"*{project.subtitle}*")
    with col_b:
        if st.button("📖 Read in Book View", use_container_width=True):
            st.session_state["active_nav"] = "Book View"
            st.rerun()

    tabs = st.tabs([
        "1. Project Details",
        "2. Source Material & Drafts",
        "3. Story Development",
        "4. Chapter Outline",
        "5. Continuity Audit"
    ])

    # TAB 1: Project Details
    with tabs[0]:
        st.subheader("Step 1: Core Story Foundation")
        with st.form("edit_project_details"):
            title = st.text_input("Title", value=project.title)
            subtitle = st.text_input("Subtitle", value=project.subtitle or "")

            c1, c2, c3 = st.columns(3)
            with c1:
                genre = st.text_input("Genre", value=project.genre)
            with c2:
                tone = st.text_input("Tone", value=project.tone)
            with c3:
                language = st.text_input("Language", value=project.language)

            audience = st.text_input("Target Audience", value=project.intended_audience or "")
            premise = st.text_area("Premise", value=project.premise or "", height=120)
            synopsis = st.text_area("Synopsis", value=project.synopsis or "", height=120)

            if st.form_submit_button("Save Changes", type="primary"):
                project.title = title.strip() or project.title
                project.subtitle = subtitle.strip()
                project.genre = genre.strip()
                project.tone = tone.strip()
                project.language = language.strip()
                project.intended_audience = audience.strip()
                project.premise = premise.strip()
                project.synopsis = synopsis.strip()
                story_service.update_project(project)
                st.success("Project details updated!")
                st.rerun()

    # TAB 2: Source Material & Drafts
    with tabs[1]:
        st.subheader("Step 2: Captured Source Material & Original Notes")
        st.caption("All raw notes, voice dictations, and imports are permanently preserved here separately from AI prose.")

        # Quick entry form
        with st.expander("➕ Add New Raw Draft or Paste Notes", expanded=False):
            with st.form("add_raw_draft_form"):
                source_label = st.text_input("Source Label / Context", placeholder="e.g. Brainstorming session, Chapter notes")
                raw_content = st.text_area("Raw Text Content", height=150)
                if st.form_submit_button("Save Source Draft"):
                    if raw_content.strip():
                        story_service.save_source_draft(
                            project_id=project.id,
                            source_type="typed",
                            original_text=raw_content.strip(),
                            source_filename=source_label.strip(),
                        )
                        st.success("Draft saved!")
                        st.rerun()

        # Display saved drafts
        drafts = story_service.list_source_drafts(project.id)
        if not drafts:
            st.info("No source drafts saved yet. Paste rough ideas above or use Voice Capture.")
        else:
            for idx, d in enumerate(drafts, start=1):
                with st.expander(f"Draft #{idx}: {d.source_type.upper()} ({d.created_at[:10]} {d.source_filename or ''})"):
                    st.text_area(f"Content #{d.id}", value=d.original_text, height=120, disabled=True)
                    if st.button("🗑️ Delete Draft", key=f"del_draft_{d.id}"):
                        story_service.delete_source_draft(d.id)
                        st.rerun()

    # TAB 3: Story Development
    with tabs[2]:
        st.subheader("Step 3: AI-Assisted Narrative Development")
        st.caption("Synthesize your premise into loglines, full synopses, turning points, character goals, and thematic foundations.")

        col_dev_btn, col_dev_notes = st.columns([1, 2])
        with col_dev_btn:
            if st.button("⚡ Develop Story Narrative", type="primary", use_container_width=True):
                with st.spinner("Analyzing story premise, character arcs, and thematic structure..."):
                    try:
                        exec_res = story_service.develop_story(project.id)
                        st.success(f"Story developed via **{exec_res.provider_name.upper()}**!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Story development failed: {e}")

        # Display existing development package
        dev_data = project.metadata_json.get("story_development")
        if dev_data:
            st.markdown("### 🎯 Logline")
            st.info(f"**{dev_data.get('logline')}**")

            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.markdown("### 📜 Short Synopsis")
                st.write(dev_data.get("short_synopsis"))
            with col_s2:
                st.markdown("### 🎭 Main Conflict")
                st.write(dev_data.get("main_conflict"))

            st.markdown("### 📖 Detailed Synopsis")
            st.write(dev_data.get("detailed_synopsis"))

            col_t1, col_t2 = st.columns(2)
            with col_t1:
                st.markdown("### 🌟 Central Themes")
                for th in dev_data.get("themes", []):
                    st.markdown(f"- {th}")

                st.markdown("### 🎯 Main Character Goals")
                for goal in dev_data.get("main_character_goals", []):
                    st.markdown(f"- {goal}")

            with col_t2:
                st.markdown("### ⚡ Major Turning Points")
                for tp in dev_data.get("major_turning_points", []):
                    st.markdown(f"- {tp}")

                st.markdown("### 🏁 Proposed Ending")
                st.write(dev_data.get("proposed_ending"))

            with st.expander("❓ Open Questions & Assumptions", expanded=False):
                st.markdown("**Open Questions for Writer Approval:**")
                for q in dev_data.get("open_questions", []):
                    st.markdown(f"- *{q}*")
                st.markdown("**Assumptions Made:**")
                for a in dev_data.get("assumptions", []):
                    st.markdown(f"- {a}")
        else:
            st.info("Click **Develop Story Narrative** above to generate structured narrative architecture from your premise.")

    # TAB 4: Chapter Outline
    with tabs[3]:
        st.subheader("Step 4: Chapter Outline & Structure")
        st.caption("Generate a multi-chapter narrative outline, edit proposals, and convert them into chapter records.")

        col_out_cfg, col_out_act = st.columns([1, 2])
        with col_out_cfg:
            num_chapters = st.slider("Number of Chapters", min_value=3, max_value=12, value=5)
            if st.button("✨ Generate Outline Proposal", type="primary", use_container_width=True):
                with st.spinner("Generating outline proposals..."):
                    try:
                        exec_res = outline_service.generate_outline_proposal(project.id, num_chapters=num_chapters)
                        st.success(f"Outline generated via **{exec_res.provider_name.upper()}**!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Outline generation failed: {e}")

        # Display latest proposal if present
        prop_data = project.metadata_json.get("latest_outline_proposal")
        if prop_data:
            st.markdown("### 📋 Latest Outline Proposal (Pending Review)")
            for ch_prop in prop_data.get("chapters", []):
                with st.expander(f"Proposal: {ch_prop.get('title')}", expanded=True):
                    st.write(ch_prop.get("summary"))
                    st.caption(f"Character Arcs: {', '.join(ch_prop.get('character_arcs', []))}")
                    st.caption(f"Turning Point: {', '.join(ch_prop.get('turning_points', []))}")

            col_apply1, col_apply2 = st.columns(2)
            with col_apply1:
                if st.button("✅ Apply Proposal (Append as New Chapters)", type="primary"):
                    outline_obj = OutlineResponse.model_validate(prop_data)
                    outline_service.apply_outline_to_project(project.id, outline_obj, overwrite_existing=False)
                    st.success("Chapters created!")
                    st.rerun()
            with col_apply2:
                if st.button("⚠️ Replace All Existing Chapters with Proposal"):
                    outline_obj = OutlineResponse.model_validate(prop_data)
                    outline_service.apply_outline_to_project(project.id, outline_obj, overwrite_existing=True)
                    st.success("Existing chapters archived and replaced!")
                    st.rerun()

        st.divider()

        # Existing Chapters in Project
        chapters = outline_service.list_chapters(project.id)
        st.markdown(f"### 📚 Established Chapters ({len(chapters)})")
        if not chapters:
            st.info("No chapters created yet. Generate an outline above or create chapters manually.")
        else:
            for ch in chapters:
                with st.container(border=True):
                    col_ch_title, col_ch_act = st.columns([4, 1])
                    with col_ch_title:
                        new_title = st.text_input(f"Title (Ch #{ch.order_index})", value=ch.title, key=f"chtit_{ch.id}")
                        new_sum = st.text_area("Chapter Summary", value=ch.summary, key=f"chsum_{ch.id}", height=70)
                        if new_title != ch.title or new_sum != ch.summary:
                            if st.button("Save Chapter Edits", key=f"save_ch_{ch.id}"):
                                ch.title = new_title
                                ch.summary = new_sum
                                outline_service.update_chapter(ch)
                                st.success("Chapter updated!")
                                st.rerun()
                    with col_ch_act:
                        if st.button("🗑️ Delete", key=f"del_ch_{ch.id}"):
                            outline_service.delete_chapter(ch.id)
                            st.rerun()

    # TAB 5: Continuity Audit
    with tabs[4]:
        st.subheader("Step 5: Story Continuity & Consistency Audit")
        st.caption("AI detects contradictory world facts, character knowledge anachronisms, and timeline breaks.")

        if st.button("🔍 Run Full Continuity Audit", type="primary"):
            with st.spinner("Auditing canon facts, timeline events, and scene progression..."):
                try:
                    exec_res = continuity_service.audit_project_continuity(project.id)
                    st.success(f"Audit completed via **{exec_res.provider_name.upper()}**!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Audit failed: {e}")

        # Display audit result
        audit_data = project.metadata_json.get("latest_continuity_review")
        if audit_data:
            score = audit_data.get("consistency_score", 100)
            st.metric("Narrative Consistency Score", f"{score}/100")
            st.info(audit_data.get("summary", ""))

            issues = audit_data.get("issues", [])
            if not issues:
                st.success("🎉 No continuity discrepancies detected!")
            else:
                for idx, issue in enumerate(issues, start=1):
                    sev = issue.get("severity", "medium").upper()
                    box_type = "warning" if sev in ("HIGH", "MEDIUM") else "info"
                    with st.container(border=True):
                        st.markdown(f"**Issue #{idx}: [{sev}] {issue.get('category', '').replace('_', ' ').title()}**")
                        st.write(issue.get("description"))
                        if issue.get("suggested_fix"):
                            st.caption(f"💡 **Suggested Fix:** {issue.get('suggested_fix')}")
        else:
            st.info("Run a continuity audit to check for timeline discrepancies and canon violations.")
