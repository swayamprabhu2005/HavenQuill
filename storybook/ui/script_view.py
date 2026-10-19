"""Script View providing screenplay adaptation, incremental continuation, and PDF export."""

import io
import streamlit as st
from pathlib import Path
from storybook.services.script_service import script_service
from storybook.services.story_service import StoryService
from storybook.services.outline_service import OutlineService


def render_script_view(
    project_id: str,
    story_service: StoryService,
    outline_service: OutlineService,
) -> None:
    """Render the screenplay and script adaptation interface."""
    project = story_service.get_project(project_id)
    if not project:
        st.error("Project not found.")
        return

    st.markdown("## 🎬 Screenplay & Script Studio")
    st.caption("Adapt your novel into an industry-standard screenplay with intelligent incremental continuation.")

    coverage = script_service.get_chapter_coverage_status(project_id)
    script = script_service.get_or_create_script(project_id, title=f"{project.title} - Screenplay")

    if coverage["total_chapters"] == 0:
        st.info("Your project has no chapters yet. Write or generate chapters in the Book View or Story Studio first.")
        return

    # Status Banner
    with st.container(border=True):
        col_stat, col_act = st.columns([3, 2])
        with col_stat:
            st.markdown(f"**Book Coverage**: {len(coverage['covered_chapters'])} of {coverage['total_chapters']} chapters adapted")
            
            if coverage["is_up_to_date"]:
                st.success("✅ **Up to Date**: All written chapters have been adapted into the screenplay.")
            elif coverage["has_script"] and len(coverage["pending_chapters"]) > 0:
                st.warning(
                    f"🌟 **New Chapters Detected**: {len(coverage['pending_chapters'])} new chapter(s) "
                    f"({', '.join(f'Ch. {c.order_index}' for c in coverage['pending_chapters'])}) "
                    "are ready to be seamlessly added to the screenplay."
                )
            else:
                st.info("Ready to adapt your book manuscript into a screenplay.")

        with col_act:
            if coverage["has_script"] and len(coverage["pending_chapters"]) > 0:
                if st.button("🎬 Continue Script with New Chapters", type="primary", use_container_width=True):
                    with st.spinner("Continuing screenplay adaptation with new chapters..."):
                        try:
                            updated_script, res = script_service.adapt_book_to_script(
                                project_id=project_id,
                                regenerate_all=False,
                            )
                            st.success(f"Screenplay seamlessly continued via {res.provider_name}!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Adaptation failed: {e}")
            else:
                button_label = "🎬 Adapt Entire Book to Script" if not coverage["has_script"] else "🔄 Regenerate Entire Screenplay"
                btn_type = "primary" if not coverage["has_script"] else "secondary"
                if st.button(button_label, type=btn_type, use_container_width=True):
                    with st.spinner("Adapting book manuscript into screenplay..."):
                        try:
                            updated_script, res = script_service.adapt_book_to_script(
                                project_id=project_id,
                                regenerate_all=True,
                            )
                            st.success(f"Screenplay generated via {res.provider_name}!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Adaptation failed: {e}")

    # If script exists, display export options and script reader/editor
    if script and script.script_content.strip():
        # Export Actions
        c_pdf, c_fountain, c_txt = st.columns(3)
        with c_pdf:
            try:
                # Generate in-memory PDF
                temp_pdf = Path(st.session_state.get("temp_dir", "data")) / f"{project.id}_script.pdf"
                script_service.export_script_pdf(script, temp_pdf)
                with open(temp_pdf, "rb") as f:
                    pdf_bytes = f.read()
                st.download_button(
                    "📄 Download Screenplay PDF",
                    data=pdf_bytes,
                    file_name=f"{project.title.lower().replace(' ', '_')}_script.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.caption(f"PDF exporter ready")

        with c_fountain:
            fountain_text = script_service.export_script_fountain(script)
            st.download_button(
                "🖋️ Download Fountain (.fountain)",
                data=fountain_text,
                file_name=f"{project.title.lower().replace(' ', '_')}.fountain",
                mime="text/plain",
                use_container_width=True,
            )

        with c_txt:
            st.download_button(
                "📝 Download Text (.txt)",
                data=script.script_content,
                file_name=f"{project.title.lower().replace(' ', '_')}_screenplay.txt",
                mime="text/plain",
                use_container_width=True,
            )

        st.markdown("---")

        # Screenplay Presentation Tabs
        tab_view, tab_edit = st.tabs(["📖 Screenplay Reading View", "✏️ Script Editor"])

        with tab_view:
            st.markdown(
                """
                <style>
                .screenplay-container {
                    background-color: #FAF8F5;
                    color: #1A1A1A;
                    font-family: 'Courier New', Courier, monospace;
                    font-size: 14px;
                    line-height: 1.6;
                    padding: 30px;
                    border-radius: 8px;
                    border: 1px solid #E2DACF;
                    white-space: pre-wrap;
                    box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(f'<div class="screenplay-container">{script.script_content}</div>', unsafe_allow_html=True)

        with tab_edit:
            st.caption("Directly edit or fine-tune dialogue, sluglines, and scene directions:")
            edited_content = st.text_area(
                "Screenplay Text",
                value=script.script_content,
                height=500,
                key=f"edit_script_{script.id}",
            )
            if st.button("💾 Save Script Edits", type="primary"):
                script.script_content = edited_content
                script_service.script_repo.update(script)
                st.success("Screenplay saved successfully!")
                st.rerun()

    else:
        st.markdown(
            """
            <div style="text-align: center; padding: 40px 20px; background-color: #FAF8F5; border: 1px dashed #C8BDB0; border-radius: 8px;">
                <h4 style="color: #2F3E46;">No Screenplay Generated Yet</h4>
                <p style="color: #52796F; max-width: 500px; margin: 0 auto 20px auto;">
                    Click the <strong>Adapt Entire Book to Script</strong> button above to convert your novel's prose into
                    proper Hollywood format with sluglines, action cues, and centered dialogue.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
