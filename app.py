# app.py

import streamlit as st
import pandas as pd
from bkt import BKT
import base64
from llm_integration import (
    generate_question,
    generate_solution,
    check_answer,
    generate_hints,
    generate_knowledge_graph
)
from sequencer import AdaptiveSequencer

st.set_page_config(page_title="PAL Agent", layout="wide")

# --- NEW: Caching function for curriculum generation ---
@st.cache_data(show_spinner="AI is designing your curriculum...")
def get_cached_curriculum(topic: str) -> dict:
    """Calls the API to generate a curriculum and caches the result."""
    return generate_knowledge_graph(topic)


# --- Callback function to reset the current question ---
def clear_problem_on_change():
    """Forces a new question to be generated when the user changes a setting."""
    st.session_state.current_problem = None
    st.session_state.hint_level = 0

# --- Function to render a custom title with your SVG icon ---
def custom_title(svg_code: str, title: str, subtitle: str):
    """Encodes SVG and displays it with a title and subtitle using HTML."""
    b64_svg = base64.b64encode(svg_code.encode('utf-8')).decode("utf-8")
    data_uri = f"data:image/svg+xml;base64,{b64_svg}"
    
    st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 20px;">
            <img src="{data_uri}" alt="icon" style="height: 48px; margin-right: 15px;">
            <div>
                <h1 style="margin: 0; padding: 0;">{title}</h1>
                <p style="margin: 0; padding: 0; color: #888;">{subtitle}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

USER_ICON_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#5D4037">
    <path d="M480-480q-66 0-113-47t-47-113q0-66 47-113t113-47q66 0 113 47t47 113q0 66-47 113t-113 47ZM160-160v-112q0-34 17.5-62.5T224-378q62-31 126-46.5T480-440q66 0 130 15.5T736-378q29 15 46.5 43.5T800-272v112H160Zm80-80h480v-32q0-11-5.5-20T700-306q-54-27-109-40.5T480-360q-56 0-111 13.5T260-306q-9 5-14.5 14t-5.5 20v32Zm240-320q33 0 56.5-23.5T560-640q0-33-23.5-56.5T480-720q-33 0-56.5 23.5T400-640q0 33 23.5 56.5T480-560Zm0-80Zm0 400Z"/>
</svg>
"""

SETT_ICON_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="m482-320 140-140q17-17 22-41.5t-5-47.5q-10-23-30-37t-45-14q-25 0-45 15.5T482-552q-18-17-37.5-32.5T400-600q-25 0-45.5 13.5T324-550q-10 23-4.5 47.5T342-460l140 140ZM370-80l-16-128q-13-5-24.5-12T307-235l-119 50L78-375l103-78q-1-7-1-13.5v-27q0-6.5 1-13.5L78-585l110-190 119 50q11-8 23-15t24-12l16-128h220l16 128q13 5 24.5 12t22.5 15l119-50 110 190-103 78q1 7 1 13.5v27q0 6.5-2 13.5l103 78-110 190-118-50q-11 8-23 15t-24 12L590-80H370Zm70-80h79l14-106q31-8 57.5-23.5T639-327l99 41 39-68-86-65q5-14 7-29.5t2-31.5q0-16-2-31.5t-7-29.5l86-65-39-68-99 42q-22-23-48.5-38.5T533-694l-13-106h-79l-14 106q-31 8-57.5 23.5T321-633l-99-41-39 68 86 64q-5 15-7 30t-2 32q0 16 2 31t7 30l-86 65 39 68 99-42q22 23 48.5 38.5T427-266l13 106Zm40-320Z"/></svg> """
## --- Sidebar --- ##
with st.sidebar:
    st.header("Your Learning Topic")
    topic_input = st.text_input("Enter any topic you want to learn:", "Basic Python Programming")
    if st.button("Load Curriculum", use_container_width=True):
        clear_problem_on_change()
        with st.spinner(f"AI is designing a curriculum for '{topic_input}'..."):
            new_graph = generate_knowledge_graph(topic_input)
            if new_graph and isinstance(new_graph, dict) and len(new_graph) > 2:
                st.session_state.knowledge_graph = new_graph
                st.session_state.sequencer = AdaptiveSequencer(st.session_state.knowledge_graph, BKT())
                st.session_state.review_mode = False
                st.toast("Curriculum created successfully!", icon="✅")
            else:
                st.error("⚠️ Could not generate a curriculum. Please try another topic.")

    if 'sequencer' in st.session_state:
        st.markdown("---")
        st.header("Settings")
        st.radio(
            "Choose your learning mode:",
            ("🧠 Adaptive Mode", "✏️ Practice Mode"),
            key="mode",
            on_change=clear_problem_on_change
        )
        if st.session_state.mode == "✏️ Practice Mode":
            practice_topic_names = [info['name'] for info in st.session_state.knowledge_graph.values()]
            st.selectbox(
                "Practice a specific skill:",
                options=practice_topic_names,
                key="practice_topic",
                on_change=clear_problem_on_change
            )
            st.subheader("Advanced Options")
            st.text_input("Focus on a sub-topic (optional):", key="sub_topic", on_change=clear_problem_on_change)
            st.text_area("Match a question style (optional):", key="sample_question", on_change=clear_problem_on_change)

# --- Main Page ---
if 'sequencer' not in st.session_state:
    # --- CORRECTED LINE: Use the custom_title function ---
    custom_title(USER_ICON_SVG, "Personalized Adaptive Learning Agent", "Your AI-powered tutor")
    st.markdown("I can be your personal tutor for almost any subject.")
    st.info("👈 **To get started, enter a topic in the sidebar and click 'Load Curriculum'.**")
else:
    # --- CORRECTED LINE: Use the custom_title function ---
    custom_title(USER_ICON_SVG, "Personalized Adaptive Learning Agent", f"Mode: {st.session_state.mode}")
    st.markdown("---")

    if st.session_state.get('review_mode', False):
        st.error("❗ Not quite! Let's review the solution.")
        st.markdown(st.session_state.last_solution)
        if st.button("▶️ Next Question", use_container_width=True):
            st.session_state.review_mode = False
            clear_problem_on_change()
            st.rerun()
    else:
        if st.session_state.get('current_problem') is None:
            next_skill_id, sub_topic, sample_question = None, None, None
            if st.session_state.mode == "🧠 Adaptive Mode":
                next_skill_id = st.session_state.sequencer.get_next_skill()
            else:
                if 'practice_topic' in st.session_state:
                    selected_name = st.session_state.practice_topic
                    next_skill_id = next((sid for sid, info in st.session_state.knowledge_graph.items() if info['name'] == selected_name), None)
                    sub_topic = st.session_state.get('sub_topic')
                    sample_question = st.session_state.get('sample_question')

            if next_skill_id:
                skill_name = st.session_state.knowledge_graph.get(next_skill_id, {}).get('name', 'Unknown Skill')
                st.session_state.skill_name = skill_name
                with st.spinner("Generating a new problem..."):
                    st.session_state.current_problem = generate_question(skill_name, sub_topic, sample_question)
                    st.session_state.hints = generate_hints(st.session_state.current_problem)
                st.session_state.skill_id = next_skill_id
                st.session_state.hint_level = 0
            else:
                st.session_state.current_problem = "⭐ All skills mastered!"
                st.session_state.skill_name = "Congratulations!"
                if st.session_state.mode == "🧠 Adaptive Mode":
                    st.balloons()

        st.subheader(f"Target Skill: {st.session_state.skill_name}")
        if st.session_state.current_problem != "⭐ All skills mastered!":
            st.info(st.session_state.current_problem)
            if st.session_state.hint_level < 3 and st.session_state.hints and len(st.session_state.hints) == 3:
                if st.button("💡 Need a hint?"):
                    st.session_state.hint_level += 1
            for i in range(st.session_state.hint_level):
                if st.session_state.hints and i < len(st.session_state.hints) and st.session_state.hints[i]:
                    st.warning(f"💡 Hint {i+1}: {st.session_state.hints[i]}")

            with st.form(key='answer_form', clear_on_submit=True):
                student_answer = st.text_area("Your Answer Here:")
                submit_button = st.form_submit_button(label="Submit Answer", use_container_width=True)
                if submit_button:
                    with st.spinner("Checking your answer..."):
                        is_correct = check_answer(st.session_state.current_problem, student_answer)
                    st.session_state.sequencer.update_student_knowledge(st.session_state.skill_id, is_correct)
                    if is_correct:
                        st.success("✅ That's correct! Fantastic work!")
                        clear_problem_on_change()
                        st.rerun()
                    else:
                        with st.spinner("Generating step-by-step solution..."):
                            solution = generate_solution(st.session_state.current_problem)
                            st.session_state.last_solution = solution
                        st.session_state.review_mode = True
                        st.rerun()

    st.markdown("---")
    with st.expander("Show My Knowledge Map"):
        knowledge_data = st.session_state.sequencer.student_knowledge
        skill_names = [info['name'] for info in st.session_state.knowledge_graph.values()]
        mastery_levels = [knowledge_data.get(skill_id, 0) * 100 for skill_id in st.session_state.knowledge_graph.keys()]
        df = pd.DataFrame({'Skill': skill_names, 'Mastery (%)': mastery_levels}).set_index('Skill')
        st.bar_chart(df, height=400)
