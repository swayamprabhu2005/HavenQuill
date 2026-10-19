"""Storybook Studio - Main Application Entrypoint."""

import streamlit as st
from storybook.config import config
from storybook.services.story_service import StoryService
from storybook.services.outline_service import OutlineService
from storybook.services.scene_service import SceneService
from storybook.services.character_service import StoryBibleService
from storybook.services.continuity_service import ContinuityService

from storybook.ui.dashboard import render_dashboard
from storybook.ui.project_editor import render_project_editor
from storybook.ui.scene_view import render_scene_view
from storybook.ui.book_view import render_book_view
from storybook.ui.story_bible_view import render_story_bible_view
from storybook.ui.settings_view import render_settings_view
from storybook.ui.live_scribe_view import render_live_scribe_view

# Initialize Services
story_service = StoryService()
outline_service = OutlineService()
scene_service = SceneService()
bible_service = StoryBibleService()
continuity_service = ContinuityService()


def main():
    st.set_page_config(
        page_title="Storybook Studio — Creative Sanctuary",
        page_icon="🌿",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Natural, Calming, Soothing Sanctuary Theme
    st.markdown(
        """
        <style>
            /* Calming Base Palette */
            .stApp {
                background-color: #FAF8F5;
                color: #2D3748;
            }
            .main .block-container {
                max-width: 1060px;
                padding-top: 1.8rem;
                padding-bottom: 4rem;
            }
            /* Soothing Sidebar in Soft Linen / Warm Cream */
            [data-testid="stSidebar"] {
                background-color: #F4EFEA;
                border-right: 1px solid #E6DED6;
            }
            /* Soft Sage Primary Buttons */
            button[kind="primary"] {
                background-color: #386641 !important;
                border-color: #2F5636 !important;
                color: #FFFFFF !important;
                border-radius: 8px;
                font-weight: 500;
                transition: all 0.2s ease-in-out;
            }
            button[kind="primary"]:hover {
                background-color: #2A4E31 !important;
                border-color: #24422A !important;
                box-shadow: 0 2px 6px rgba(40, 80, 50, 0.2);
            }
            button[kind="secondary"] {
                background-color: #FFFFFF !important;
                border: 1px solid #D5CCC2 !important;
                border-radius: 8px;
                color: #3D4852 !important;
            }
            button[kind="secondary"]:hover {
                background-color: #F8F5F0 !important;
                border-color: #B8ACA0 !important;
            }
            /* Calming Cards & Containers */
            [data-testid="stVerticalBlock"] > div[data-testid="stContainer"] {
                background-color: #FFFFFF;
                border-radius: 10px;
                border: 1px solid #EAE3DA;
            }
            /* Peaceful Saved indicator pill */
            .saved-pill {
                display: inline-block;
                padding: 4px 10px;
                font-size: 0.75rem;
                border-radius: 14px;
                background-color: #E2EDE3;
                color: #275231;
                font-weight: 600;
                letter-spacing: 0.3px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Initialize Session State
    if "active_nav" not in st.session_state:
        st.session_state["active_nav"] = "Dashboard"

    # Sidebar Navigation & Context
    with st.sidebar:
        st.markdown(
            """
            <div style="padding: 10px 0 15px 0;">
                <h2 style="margin: 0; font-family: Georgia, serif; font-size: 1.6rem;">Storybook Studio</h2>
                <span class="saved-pill">● Local SQLite Active</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        projects = story_service.list_projects()
        project_ids = [p.id for p in projects]

        # Ensure selected_project_id is valid
        if "selected_project_id" not in st.session_state or st.session_state["selected_project_id"] not in project_ids:
            if projects:
                st.session_state["selected_project_id"] = projects[0].id
            else:
                st.session_state["selected_project_id"] = None

        curr_proj_id = st.session_state.get("selected_project_id")
        current_project = story_service.get_project(curr_proj_id) if curr_proj_id else None

        # Project Switcher
        if projects:
            st.markdown("**Active Project:**")
            proj_labels = [p.title for p in projects]
            curr_proj_idx = next((i for i, p in enumerate(projects) if p.id == curr_proj_id), 0)

            chosen_label = st.selectbox(
                "Choose Project",
                proj_labels,
                index=curr_proj_idx,
                label_visibility="collapsed",
            )
            new_selected_id = projects[proj_labels.index(chosen_label)].id
            if new_selected_id != curr_proj_id:
                st.session_state["selected_project_id"] = new_selected_id
                st.rerun()

        st.markdown("---")

        # Navigation Options
        nav_options = [
            "Dashboard",
            "🌿 Live Story Sanctuary",
            "Project Studio",
            "Scene & Structure View",
            "Book View",
            "Story Bible",
            "Settings",
        ]

        active_idx = nav_options.index(st.session_state["active_nav"]) if st.session_state["active_nav"] in nav_options else 0
        selected_nav = st.radio("Navigation", nav_options, index=active_idx, label_visibility="collapsed")

        if selected_nav != st.session_state["active_nav"]:
            st.session_state["active_nav"] = selected_nav
            st.session_state["active_view"] = "dashboard"
            st.rerun()

        st.markdown("---")

        # Provider Status Indicator
        st.caption(f"**AI Engine:** `{config.ai_provider.upper()}`")
        if config.ai_provider == "gemini":
            st.caption(f"Model: {config.gemini_model}")
        elif config.ai_provider == "groq":
            st.caption(f"Model: {config.groq_model}")
        else:
            st.caption("Mode: 100% Offline (Mock Engine)")

        if config.ai_auto_fallback:
            st.caption("Auto-Fallback: 🟢 Enabled")

        st.markdown(
            "<small style='color: #888;'>Storybook Studio v1.0<br/>Phase 1 Local-First Build</small>",
            unsafe_allow_html=True,
        )

    # Route to Views
    target_nav = st.session_state["active_nav"]

    if target_nav == "Dashboard":
        render_dashboard(story_service)
    elif target_nav == "Settings":
        render_settings_view()
    elif not current_project:
        st.warning("Please create or select a project from the Dashboard first.")
        render_dashboard(story_service)
    elif target_nav == "🌿 Live Story Sanctuary":
        render_live_scribe_view(current_project.id, story_service, outline_service, scene_service)
    elif target_nav == "Project Studio":
        render_project_editor(current_project.id, story_service, outline_service, continuity_service)
    elif target_nav == "Scene & Structure View":
        render_scene_view(current_project.id, story_service, outline_service, scene_service)
    elif target_nav == "Book View":
        render_book_view(current_project.id, story_service, outline_service, scene_service)
    elif target_nav == "Story Bible":
        render_story_bible_view(current_project.id, story_service, bible_service)


if __name__ == "__main__":
    main()
