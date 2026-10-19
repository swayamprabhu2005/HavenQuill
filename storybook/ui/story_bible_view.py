"""Story Bible View managing characters, locations, locked canon facts, and timeline."""

import streamlit as st
from storybook.models import Character, Location, CanonFact, StoryEvent, StoryBibleExtractionResponse
from storybook.services.character_service import StoryBibleService
from storybook.services.story_service import StoryService


def render_story_bible_view(
    project_id: str,
    story_service: StoryService,
    bible_service: StoryBibleService,
) -> None:
    """Render the story bible editor for characters, locations, canon facts, and lore."""
    project = story_service.get_project(project_id)
    if not project:
        st.error("Project not found.")
        return

    st.title(f"📖 Story Bible & Lore — {project.title}")
    st.caption("Organize characters, world locations, canonical locked facts, and historical timeline events.")

    # AI Extraction Toolbar
    with st.expander("⚡ Extract Story Bible from Manuscript / Drafts (AI)", expanded=False):
        drafts = story_service.list_source_drafts(project_id)
        if not drafts and not project.premise:
            st.info("Add some notes or source drafts in Project Studio first.")
        else:
            combined_text = "\n\n".join(d.original_text for d in drafts) or project.synopsis or project.premise
            st.caption(f"Source text size: {len(combined_text)} characters.")
            if st.button("Extract Entities with AI", type="primary"):
                with st.spinner("Extracting characters, locations, and canon facts..."):
                    try:
                        exec_res = bible_service.extract_story_bible_from_text(project_id, combined_text)
                        st.session_state[f"pending_bible_{project_id}"] = exec_res.data
                        st.success(f"Extracted entities via **{exec_res.provider_name.upper()}**!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Extraction failed: {e}")

        # Review pending extraction
        if f"pending_bible_{project_id}" in st.session_state:
            extraction: StoryBibleExtractionResponse = st.session_state[f"pending_bible_{project_id}"]
            st.info(f"**Extracted Entities Preview:** {len(extraction.characters)} Characters, {len(extraction.locations)} Locations, {len(extraction.canon_facts)} Canon Facts.")
            if st.button("✅ Approve & Merge into Story Bible", type="primary"):
                counts = bible_service.apply_extracted_story_bible(project_id, extraction)
                del st.session_state[f"pending_bible_{project_id}"]
                st.success(f"Added {counts['characters']} characters, {counts['locations']} locations, and {counts['facts']} canon facts!")
                st.rerun()

    st.divider()

    tabs = st.tabs(["👥 Characters", "🏰 Locations", "🔒 Canon Facts", "⏳ Timeline Events"])

    # 1. Characters Tab
    with tabs[0]:
        st.subheader("Dramatis Personae")
        characters = bible_service.list_characters(project_id)

        with st.expander("➕ Add New Character", expanded=False):
            with st.form("new_char_form"):
                c_name = st.text_input("Canonical Name*")
                c_aliases = st.text_input("Aliases / Nicknames (comma-separated)")
                c_desc = st.text_area("Physical Description & Background")
                c_traits = st.text_input("Key Traits (comma-separated)", placeholder="e.g. Brave, Cynical, Observant")
                if st.form_submit_button("Save Character"):
                    if c_name.strip():
                        aliases = [a.strip() for a in c_aliases.split(",") if a.strip()]
                        traits = [t.strip() for t in c_traits.split(",") if t.strip()]
                        bible_service.create_character(
                            project_id=project_id,
                            name=c_name,
                            description=c_desc,
                            aliases=aliases,
                            traits=traits,
                        )
                        st.success(f"Character '{c_name}' created!")
                        st.rerun()

        if not characters:
            st.info("No characters added yet.")
        else:
            for ch in characters:
                with st.container(border=True):
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.markdown(f"### {ch.canonical_name}")
                        if ch.aliases_json:
                            st.caption(f"Aliases: {', '.join(ch.aliases_json)}")
                        if ch.traits_json:
                            st.write(f"**Traits:** {', '.join(ch.traits_json)}")
                        st.write(ch.description or "No description provided.")
                    with col2:
                        if st.button("🗑️ Delete", key=f"del_char_{ch.id}"):
                            bible_service.delete_character(ch.id)
                            st.rerun()

    # 2. Locations Tab
    with tabs[1]:
        st.subheader("World Locations")
        locations = bible_service.list_locations(project_id)

        with st.expander("➕ Add New Location", expanded=False):
            with st.form("new_loc_form"):
                l_name = st.text_input("Location Name*")
                l_desc = st.text_area("Atmosphere, Sensory Details & Description")
                l_rules = st.text_input("World Rules / Constraints (comma-separated)", placeholder="e.g. No magic works here, High tides at night")
                if st.form_submit_button("Save Location"):
                    if l_name.strip():
                        rules = [r.strip() for r in l_rules.split(",") if r.strip()]
                        bible_service.create_location(
                            project_id=project_id,
                            name=l_name,
                            description=l_desc,
                            rules=rules,
                        )
                        st.success(f"Location '{l_name}' created!")
                        st.rerun()

        if not locations:
            st.info("No locations recorded yet.")
        else:
            for loc in locations:
                with st.container(border=True):
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.markdown(f"### {loc.name}")
                        st.write(loc.description or "No description.")
                        if loc.rules_json:
                            st.caption(f"**Rules:** {', '.join(loc.rules_json)}")
                    with col2:
                        if st.button("🗑️ Delete", key=f"del_loc_{loc.id}"):
                            bible_service.delete_location(loc.id)
                            st.rerun()

    # 3. Canon Facts Tab
    with tabs[2]:
        st.subheader("Canonical World Facts & Lock Safeguards")
        st.info(
            "🔒 **Canon Locking:** Mark essential facts as **Locked**. If future AI generation or editing "
            "attempts to violate or overwrite a locked fact, Storybook Studio will flag an explicit warning."
        )

        facts = bible_service.list_canon_facts(project_id)

        with st.expander("➕ Add New Canon Fact", expanded=False):
            with st.form("new_fact_form"):
                f_cat = st.selectbox("Category", ["world", "character", "plot", "timeline", "magic/tech"])
                f_subj = st.text_input("Subject / Topic", placeholder="e.g. The Great War, Elena's Chronometer")
                f_text = st.text_area("Canon Fact Statement*")
                f_lock = st.checkbox("Lock as Immutable Canon", value=True)
                if st.form_submit_button("Save Canon Fact"):
                    if f_text.strip():
                        bible_service.create_canon_fact(
                            project_id=project_id,
                            fact_text=f_text,
                            category=f_cat,
                            subject=f_subj,
                            is_locked=f_lock,
                        )
                        st.success("Canon fact saved!")
                        st.rerun()

        if not facts:
            st.info("No canon facts recorded yet.")
        else:
            for fact in facts:
                with st.container(border=True):
                    col_f_info, col_f_lock, col_f_del = st.columns([5, 2, 1])
                    with col_f_info:
                        lock_badge = "🔒 **[LOCKED]** " if fact.is_locked else "🔓 [Open] "
                        st.markdown(f"{lock_badge}**[{fact.category.upper()}] {fact.subject or ''}**")
                        st.write(fact.fact_text)
                    with col_f_lock:
                        new_lock_state = st.toggle("Lock Canon", value=fact.is_locked, key=f"lock_{fact.id}")
                        if new_lock_state != fact.is_locked:
                            fact.is_locked = new_lock_state
                            bible_service.update_canon_fact(fact)
                            st.rerun()
                    with col_f_del:
                        if st.button("🗑️", key=f"del_fact_{fact.id}", help="Delete fact"):
                            bible_service.delete_canon_fact(fact.id)
                            st.rerun()

    # 4. Timeline Events Tab
    with tabs[3]:
        st.subheader("Chronological Story Events")
        events = bible_service.list_story_events(project_id)

        with st.expander("➕ Add Timeline Event", expanded=False):
            with st.form("new_event_form"):
                e_marker = st.text_input("Time Marker", placeholder="e.g. 300 Years Ago, Midnight, Day 1")
                e_desc = st.text_area("Event Description*")
                if st.form_submit_button("Save Event"):
                    if e_desc.strip():
                        bible_service.create_story_event(
                            project_id=project_id,
                            description=e_desc,
                            time_marker=e_marker,
                            order_index=len(events) + 1,
                        )
                        st.success("Event added!")
                        st.rerun()

        if not events:
            st.info("No timeline events added yet.")
        else:
            for ev in events:
                with st.container(border=True):
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.markdown(f"**⏰ {ev.time_marker or f'Event #{ev.order_index}'}**")
                        st.write(ev.description)
                    with col2:
                        if st.button("🗑️", key=f"del_ev_{ev.id}"):
                            bible_service.delete_story_event(ev.id)
                            st.rerun()
