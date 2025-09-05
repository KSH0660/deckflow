import asyncio
import json
import time
from datetime import datetime
from uuid import UUID

import streamlit as st

from app.adapter.factory import current_llm, current_repo
from app.service.generate_deck import generate_deck


def main():
    st.set_page_config(
        page_title="DeckFlow - AI Presentation Generator", page_icon="🎯", layout="wide"
    )

    st.title("🎯 DeckFlow")
    st.markdown("**AI-powered presentation generator**")

    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")

        # Repository selection
        repo_type = st.selectbox(
            "Repository Type",
            ["InMemory", "SQLite"],
            help="Choose where to store deck data",
        )

        if repo_type == "SQLite":
            db_path = st.text_input("Database Path", value="decks.db")

        st.divider()
        st.markdown("### 📝 How to use")
        st.markdown(
            """
        1. Enter your presentation topic
        2. Click 'Generate Deck'
        3. Wait for AI to create your slides
        4. View the generated content
        """
        )

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("📋 Create New Deck")

        # Input form
        with st.form("deck_form"):
            prompt = st.text_area(
                "Presentation Topic",
                placeholder="예: Samsung vs Hynix 메모리 반도체 기술 비교 분석 프레젠테이션",
                height=100,
                help="Describe what kind of presentation you want to create",
            )

            submitted = st.form_submit_button("🚀 Generate Deck", type="primary")

            if submitted and prompt.strip():
                if len(prompt.strip()) < 5:
                    st.error("Prompt must be at least 5 characters long")
                elif len(prompt.strip()) > 5000:
                    st.error("Prompt must be less than 5000 characters")
                else:
                    generate_presentation(prompt.strip(), repo_type)

    with col2:
        st.header("📊 Recent Decks")
        display_recent_decks()


def generate_presentation(prompt: str, repo_type: str):
    """Generate presentation and display progress"""

    # Initialize progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        status_text.text("🔧 Initializing...")
        progress_bar.progress(10)

        # Get repository based on selection
        if repo_type == "SQLite":
            from app.adapter.db import SQLiteRepository

            repo = SQLiteRepository()
        else:
            repo = current_repo()

        llm = current_llm()

        status_text.text("🤖 Starting AI generation...")
        progress_bar.progress(20)

        # Generate deck
        start_time = time.time()
        deck_id = asyncio.run(generate_deck(prompt, llm, repo))
        generation_time = time.time() - start_time

        progress_bar.progress(100)
        status_text.text("✅ Generation complete!")

        # Store in session state for display
        st.session_state[f"deck_{deck_id}"] = {
            "deck_id": deck_id,
            "prompt": prompt,
            "generated_at": datetime.now(),
            "generation_time": generation_time,
        }

        # Display success message
        st.success(f"🎉 Deck generated successfully in {generation_time:.2f}s!")
        st.info(f"**Deck ID:** `{deck_id}`")

        # Display deck content
        display_deck_content(deck_id, repo)

    except Exception as e:
        progress_bar.progress(0)
        status_text.text("")
        st.error(f"❌ Generation failed: {str(e)}")


def display_deck_content(deck_id: str, repo):
    """Display generated deck content"""

    try:
        deck_data = asyncio.run(repo.get_deck(UUID(deck_id)))

        if not deck_data:
            st.warning("Deck not found")
            return

        st.divider()
        st.header("📑 Generated Presentation")

        # Deck info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Status", deck_data.get("status", "unknown"))
        with col2:
            st.metric("Slides", len(deck_data.get("slides", [])))
        with col3:
            created_at = deck_data.get("created_at")
            if isinstance(created_at, datetime):
                st.metric("Created", created_at.strftime("%H:%M:%S"))
            else:
                st.metric("Created", "N/A")

        # Deck metadata
        with st.expander("📋 Deck Information", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Title:** {deck_data.get('deck_title', 'N/A')}")
                st.write(f"**Goal:** {deck_data.get('goal', 'N/A')}")
                st.write(f"**Theme:** {deck_data.get('color_theme', 'N/A')}")
            with col2:
                st.write(f"**Audience:** {deck_data.get('audience', 'N/A')[:100]}...")
                st.write(
                    f"**Core Message:** {deck_data.get('core_message', 'N/A')[:100]}..."
                )

        # Slides content
        slides = deck_data.get("slides", [])
        if slides:
            st.subheader("🎯 Slides")

            for i, slide in enumerate(slides):
                with st.expander(f"Slide {i+1}", expanded=i == 0):
                    slide_content = slide.get("content", {})
                    html_content = slide_content.get("html_content", "")

                    if html_content:
                        st.components.v1.html(html_content, height=400, scrolling=True)
                    else:
                        st.warning("No content available for this slide")

                    # Show raw data in details
                    with st.expander("📊 Raw Data"):
                        st.json(slide_content)

    except Exception as e:
        st.error(f"Error displaying deck: {str(e)}")


def display_recent_decks():
    """Display recently generated decks from session state"""

    recent_decks = []
    for key, value in st.session_state.items():
        if key.startswith("deck_"):
            recent_decks.append(value)

    # Sort by generation time
    recent_decks.sort(key=lambda x: x.get("generated_at", datetime.min), reverse=True)

    if recent_decks:
        for deck in recent_decks[:5]:  # Show last 5
            with st.container():
                st.write(f"🆔 `{deck['deck_id'][:8]}...`")
                st.write(f"📝 {deck['prompt'][:50]}...")
                st.write(f"⏱️ {deck['generation_time']:.1f}s")

                if st.button(f"View", key=f"view_{deck['deck_id']}"):
                    repo = current_repo()
                    display_deck_content(deck["deck_id"], repo)

                st.divider()
    else:
        st.write("No decks generated yet")


if __name__ == "__main__":
    main()
