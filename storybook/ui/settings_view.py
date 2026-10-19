"""AI Provider and Application Settings View."""

import streamlit as st
from storybook.config import config
from storybook.providers.provider_manager import provider_manager


def render_settings_view() -> None:
    """Render the AI Provider and Application Settings screen."""
    st.title("⚙️ AI Provider & System Settings")
    st.caption("Configure your AI generation engines, API keys, transcription preferences, and fallback policies.")

    # Status Banner
    col_p, col_f, col_t = st.columns(3)
    with col_p:
        st.metric("Active Provider", config.ai_provider.upper())
    with col_f:
        st.metric("Auto Fallback", "ENABLED" if config.ai_auto_fallback else "DISABLED")
    with col_t:
        st.metric("Transcription", config.transcription_provider.upper())

    st.divider()

    # Section 1: Provider Selection & Routing
    st.subheader("1. Active AI Provider & Routing Policy")
    st.info(
        "💡 **No API Key Required:** Storybook Studio includes a built-in **Mock Provider** that generates "
        "deterministic, structured story outlines and scenes completely offline. You do not need paid API keys to "
        "test or use all core story-writing features."
    )

    provider_options = ["mock", "gemini", "groq"]
    current_p_idx = provider_options.index(config.ai_provider) if config.ai_provider in provider_options else 0

    selected_provider = st.selectbox(
        "Primary AI Engine",
        provider_options,
        index=current_p_idx,
        help="Select which provider executes your story generation, outlining, and drafting requests.",
        format_func=lambda x: {
            "mock": "Mock Provider (100% Offline / No Keys Required)",
            "gemini": "Google Gemini (Primary Cloud LLM)",
            "groq": "Groq (High-Speed LLM Inference)",
        }.get(x, x),
    )

    auto_fallback = st.toggle(
        "Enable Automatic Fallback (Gemini ➔ Groq)",
        value=config.ai_auto_fallback,
        help=(
            "When enabled, if Gemini encounters a temporary 429 rate limit or service outage, "
            "the request will be automatically routed to Groq. Will not fall back for invalid keys."
        ),
    )

    st.divider()

    # Section 2: Google Gemini Configuration
    st.subheader("2. Google Gemini Configuration (Primary Provider)")
    st.markdown(
        "Gemini provides deep reasoning, large context windows, and structured schema generation. "
        "[Get a Gemini API Key](https://aistudio.google.com/apikey)"
    )

    gemini_key_status = f"Configured ({config.mask_key(config.gemini_api_key)})" if config.is_gemini_configured else "Not Configured"
    st.caption(f"Current Status: **{gemini_key_status}**")

    gemini_key_input = st.text_input(
        "Gemini API Key",
        value="",
        type="password",
        placeholder="Enter new key to update, or leave blank to keep current",
        help="Stored locally in .env. Never logged, exported, or transmitted elsewhere.",
    )

    gemini_model_input = st.text_input(
        "Gemini Model ID",
        value=config.gemini_model or "gemini-2.5-flash",
        help="Recommended: gemini-2.5-flash or gemini-3.8-flash.",
    )

    st.divider()

    # Section 3: Groq Configuration
    st.subheader("3. Groq Configuration (Fallback Provider)")
    st.markdown(
        "Groq delivers ultra-fast open-weight model inference (e.g., Llama 3.3). "
        "[Get a Groq API Key](https://console.groq.com/keys)"
    )

    groq_key_status = f"Configured ({config.mask_key(config.groq_api_key)})" if config.is_groq_configured else "Not Configured"
    st.caption(f"Current Status: **{groq_key_status}**")

    groq_key_input = st.text_input(
        "Groq API Key",
        value="",
        type="password",
        placeholder="Enter new key to update, or leave blank to keep current",
        help="Stored locally in .env. Never logged, exported, or transmitted elsewhere.",
    )

    groq_model_input = st.text_input(
        "Groq Model ID",
        value=config.groq_model or "llama-3.3-70b-versatile",
        help="Recommended: llama-3.3-70b-versatile or llama-3.1-8b-instant.",
    )

    st.divider()

    # Section 4: Voice & Speech-to-Text Transcription
    st.subheader("4. Voice Capture & Transcription Preferences")
    st.caption("Dictate your ideas or upload recordings. Transcripts are reviewed before being saved.")

    enable_cloud_transcription = st.checkbox(
        "Allow Cloud Audio Transcription",
        value=config.enable_cloud_transcription,
        help="When enabled, audio clips may be sent to the chosen cloud provider for speech-to-text processing.",
    )

    transcription_options = ["faster_whisper", "groq", "gemini", "mock", "none"]
    current_t_idx = transcription_options.index(config.transcription_provider) if config.transcription_provider in transcription_options else 0

    transcription_provider = st.selectbox(
        "Transcription Engine",
        transcription_options,
        index=current_t_idx,
        format_func=lambda x: {
            "faster_whisper": "Fast Whisper (Local CPU / No API Key Needed - Recommended)",
            "groq": "Groq Whisper API (whisper-large-v3, Cloud Ultra-Fast)",
            "gemini": "Gemini Multimodal Audio Transcription",
            "mock": "Mock Engine (Local offline demonstration)",
            "none": "None (Manual text input or review only)",
        }.get(x, x),
    )

    st.divider()

    # Save Settings Button
    col_save, col_test = st.columns([1, 1])
    with col_save:
        if st.button("💾 Save Settings to .env", type="primary", use_container_width=True):
            updates = {
                "AI_PROVIDER": selected_provider,
                "AI_AUTO_FALLBACK": "true" if auto_fallback else "false",
                "GEMINI_MODEL": gemini_model_input.strip(),
                "GROQ_MODEL": groq_model_input.strip(),
                "ENABLE_CLOUD_TRANSCRIPTION": "true" if enable_cloud_transcription else "false",
                "TRANSCRIPTION_PROVIDER": transcription_provider,
            }
            if gemini_key_input.strip():
                updates["GEMINI_API_KEY"] = gemini_key_input.strip()
            if groq_key_input.strip():
                updates["GROQ_API_KEY"] = groq_key_input.strip()

            config.update_settings(updates)
            st.success("✅ Settings updated and persisted to .env successfully!")
            st.rerun()

    with col_test:
        if st.button("🔌 Test Provider Connections", use_container_width=True):
            with st.spinner("Testing connectivity across configured providers..."):
                results = provider_manager.test_all_providers()

            for prov_name, res in results.items():
                if res["ok"]:
                    st.success(f"**{prov_name.upper()} ({res.get('model', '')}):** {res['message']}")
                else:
                    st.warning(f"**{prov_name.upper()} ({res.get('model', '')}):** {res['message']}")
