# app.py

import streamlit as st
import pandas as pd
import base64
from bkt import BKT
from llm_integration import (
    generate_question, 
    generate_solution, 
    check_answer, 
    generate_hints,
    generate_knowledge_graph
)
from sequencer import AdaptiveSequencer
from rag_processor import process_pdf_and_generate_quiz, process_pdf_and_generate_flashcards


st.set_page_config(
    page_title="PAL Agent",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Session State Initialization for a Single Session ---
if 'app_mode' not in st.session_state:
    st.session_state.app_mode = "AI Tutor (General Topics)"
    st.session_state.model_choice = "Local AI (Llama 3)" # Default model
    st.session_state.sequencer = None
    st.session_state.knowledge_graph = None
    st.session_state.current_problem = None
    st.session_state.current_problem_meta = None   # <--- store full_quiz metadata here
    st.session_state.review_mode = False
    st.session_state.last_solution = ""
    st.session_state.hints = []
    st.session_state.hint_level = 0
    st.session_state.skill_name = ""
    st.session_state.difficulty = ""
    st.session_state.quiz_questions = None
    st.session_state.current_quiz_index = 0
    st.session_state.quiz_score = 0
    st.session_state.quiz_finished = False
    st.session_state.user_answers = []
    st.session_state.flashcards = None
    st.session_state.current_flashcard_index = 0
    st.session_state.flashcard_flipped = False
    st.session_state.search_online = False   # <--- added

# --- Helper Function for Custom Title ---
def custom_title(svg_code: str, title: str, subtitle: str):
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

## --- Sidebar --- ##
with st.sidebar:
    st.header("🤖 AI Engine")
    st.radio(
        "Choose AI model for the Tutor:",
        ("Local AI (Llama 3)", "Cloud AI (Gemini)"),
        key="model_choice",
        help="Local AI is fast and free. Cloud AI is more powerful but requires an API key in secrets.toml."
    )
    st.markdown("---")

    st.header("📚 Learning Mode")
    st.radio(
        "Choose your activity:",
        ("AI Tutor (General Topics)", "Study Assistant"),
        key="app_mode"
    )
    st.markdown("---")

    if st.session_state.app_mode == "AI Tutor (General Topics)":
        st.header("⚙️ Settings")
        topic_input = st.text_input("Enter any topic you want to learn:", "Basic Python Programming")
        if st.button("Load Curriculum", use_container_width=True):
            st.session_state.current_problem = None
            st.session_state.current_problem_meta = None
            with st.spinner(f"AI is designing a curriculum for '{topic_input}'..."):
                new_graph = generate_knowledge_graph(topic_input, st.session_state.model_choice)
                if new_graph and isinstance(new_graph, dict) and len(new_graph) > 2:
                    st.session_state.knowledge_graph = new_graph
                    st.session_state.sequencer = AdaptiveSequencer(st.session_state.knowledge_graph, BKT())
                    st.session_state.review_mode = False
                    st.toast("Curriculum created successfully!", icon="✅")
                    st.rerun()
                else:
                    st.error("Could not generate a curriculum.", icon="⚠️")
        
        if st.session_state.get('sequencer'):
            st.subheader("🎛️ Learning Style")
            st.radio("Style:", ("🧠 Adaptive Mode", "✏️ Practice Mode"), key="mode", label_visibility="collapsed", on_change=lambda: setattr(st.session_state, 'current_problem', None))
            
            # --- NEW: Show search checkbox only if Gemini is selected ---
            if st.session_state.model_choice == "Cloud AI (Gemini)":
                st.checkbox("Search online for interview questions", key="search_online", on_change=lambda: setattr(st.session_state, 'current_problem', None))

            if st.session_state.mode == "✏️ Practice Mode":
                practice_topic_names = [info['name'] for info in st.session_state.knowledge_graph.values()]
                st.selectbox("Skill:", options=practice_topic_names, key="practice_topic", on_change=lambda: setattr(st.session_state, 'current_problem', None))
                st.subheader("🔬 Advanced Options")
                st.text_input("Sub-topic (optional):", key="sub_topic", on_change=lambda: setattr(st.session_state, 'current_problem', None))
                st.text_area("Sample question style (optional):", key="sample_question", on_change=lambda: setattr(st.session_state, 'current_problem', None))
    
    elif st.session_state.app_mode == "Study Assistant":
        st.header("📄 Your Study Material")
        source_type = st.radio("Choose your study source:", ("PDF Document", "YouTube Video"))

        if source_type == "PDF Document":
            uploaded_file = st.file_uploader("Upload your PDF document", type="pdf")
            if uploaded_file:
                st.subheader("Study Tools")
                num_q = st.slider("Number of questions:", 1, 10, 5, key='num_questions_slider_pdf')
                num_fc = st.slider("Number of flashcards:", 5, 20, 10, key='num_flashcards_slider_pdf')
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Generate Quiz", use_container_width=True):
                        quiz_data = process_pdf_and_generate_quiz(uploaded_file, num_q)
                        if quiz_data:
                            st.session_state.quiz_questions = quiz_data
                            st.session_state.flashcards = None
                            st.session_state.current_quiz_index = 0
                            st.session_state.quiz_score = 0
                            st.session_state.quiz_finished = False
                            st.session_state.user_answers = []
                            st.rerun()
                with col2:
                    if st.button("Generate Flashcards", use_container_width=True):
                        flashcard_data = process_pdf_and_generate_flashcards(uploaded_file, num_fc)
                        if flashcard_data:
                            st.session_state.flashcards = flashcard_data
                            st.session_state.quiz_questions = None
                            st.session_state.current_flashcard_index = 0
                            st.session_state.flashcard_flipped = False
                            st.rerun()
        
        # elif source_type == "YouTube Video":
        #     youtube_url = st.text_input("Paste YouTube video URL:")
        #     if youtube_url:
        #         num_q_yt = st.slider("Number of questions:", 1, 10, 5, key='num_questions_slider_yt')
        #         if st.button("Generate Quiz from Video", use_container_width=True):
        #             quiz_data = process_youtube_and_generate_quiz(youtube_url, num_q_yt)
        #             if quiz_data:
        #                 st.session_state.quiz_questions = quiz_data
        #                 st.session_state.flashcards = None
        #                 st.session_state.current_quiz_index = 0
        #                 st.session_state.quiz_score = 0
        #                 st.session_state.quiz_finished = False
        #                 st.session_state.user_answers = []
        #                 st.rerun()

# --- Main Page Logic ---
tutor_active = st.session_state.app_mode == "AI Tutor (General Topics)" and st.session_state.get('sequencer')
quiz_active = st.session_state.app_mode == "Study Assistant" and st.session_state.get('quiz_questions')
flashcards_active = st.session_state.app_mode == "Study Assistant" and st.session_state.get('flashcards')

if tutor_active:
    custom_title(USER_ICON_SVG, "AI Tutor", f"Mode: {st.session_state.mode}")
    st.markdown("---")
    main_col, knowledge_col = st.columns([3, 1])
    with main_col:
        if st.session_state.get('review_mode', False):
            st.error("Not quite! Let's review the solution.", icon="❌")
            st.markdown(st.session_state.last_solution)
            if st.button("Next Question", use_container_width=True):
                st.session_state.review_mode = False
                st.session_state.current_problem = None
                st.session_state.current_problem_meta = None
                st.rerun()
        else:
            if st.session_state.get('current_problem') is None:
                next_skill_id, sub_topic, sample_question = None, None, None
                if st.session_state.mode == "🧠 Adaptive Mode":
                    next_skill_id = st.session_state.sequencer.get_next_skill()
                else: # Practice Mode
                    selected_name = st.session_state.get('practice_topic')
                    if selected_name:
                        next_skill_id = next((sid for sid, info in st.session_state.knowledge_graph.items() if info['name'] == selected_name), None)
                        sub_topic = st.session_state.get('sub_topic')
                        sample_question = st.session_state.get('sample_question')
                if next_skill_id:
                    mastery_prob = st.session_state.sequencer.student_knowledge.get(next_skill_id, 0.0)
                    if mastery_prob < 0.4: difficulty = "Easy"
                    elif mastery_prob < 0.8: difficulty = "Medium"
                    else: difficulty = "Hard"
                    st.session_state.difficulty = difficulty
                    skill_name = st.session_state.knowledge_graph.get(next_skill_id, {}).get('name', 'Unknown Skill')
                    st.session_state.skill_name = skill_name

                    # --- UPDATED: Get the search_online value ---
                    search_online = st.session_state.get("search_online", False)

                    with st.spinner("Generating a new problem..."):
                        # Request the full_quiz JSON object (if available)
                        q_obj = generate_question(
                            skill_name,
                            st.session_state.model_choice,
                            sub_topic,
                            sample_question,
                            st.session_state.difficulty,
                            search_online,
                            output_format="full_quiz"   # request structured quiz output
                        )

                        # If model returned dict -> store metadata; otherwise fallback to plain text
                        if isinstance(q_obj, dict):
                            st.session_state.current_problem_meta = q_obj
                            st.session_state.current_problem = q_obj.get("question_text", "")
                        else:
                            st.session_state.current_problem_meta = None
                            st.session_state.current_problem = q_obj

                        # generate hints using the question text (string)
                        st.session_state.hints = generate_hints(st.session_state.current_problem, st.session_state.model_choice)

                    st.session_state.skill_id = next_skill_id
                    st.session_state.hint_level = 0
                else:
                    st.session_state.current_problem = "All skills mastered!"
                    st.session_state.skill_name = "Congratulations!"
                    if st.session_state.mode == "🧠 Adaptive Mode": st.balloons()
            
            st.subheader(f"Target Skill: {st.session_state.skill_name}")
            if st.session_state.get('difficulty'): st.caption(f"Difficulty Level: **{st.session_state.difficulty}**")
            if st.session_state.current_problem != "All skills mastered!":
                st.info(st.session_state.current_problem)

                if st.session_state.get('hint_level', 0) < 3 and st.session_state.get('hints') and len(st.session_state.hints) == 3:
                    if st.button("💡 Need a hint?"):
                        st.session_state.hint_level += 1
                for i in range(st.session_state.get('hint_level', 0)):
                    if st.session_state.hints and i < len(st.session_state.hints) and st.session_state.hints[i]:
                        st.warning(f"Hint {i+1}: {st.session_state.hints[i]}", icon="💡")
                
                # --- Render answer input dynamically based on question type ---
                current_meta = st.session_state.get("current_problem_meta")
                q_type = None
                if isinstance(current_meta, dict):
                    q_type = current_meta.get("question_type")

                with st.form(key='answer_form', clear_on_submit=True):
                    # Choose input widget based on question type
                    if q_type == "MCQ":
                        options = current_meta.get("options", []) if isinstance(current_meta, dict) else []
                        student_answer = st.radio("Choose your answer:", options=options, index=0 if options else None)
                    elif q_type == "Coding":
                        student_answer = st.text_area("Paste your code here (or write a short explanation):", height=220)
                        st.caption("For coding tasks, paste code or write the expected approach/answer.")
                    elif q_type == "Fill in the Blank":
                        student_answer = st.text_input("Your answer:")
                    else:
                        # fallback: free text / short answer
                        student_answer = st.text_area("Your Answer Here:")

                    submit_button = st.form_submit_button(label="Submit Answer", use_container_width=True)
                    if submit_button:
                        with st.spinner("Checking your answer..."):
                            # Local MCQ grading fallback (deterministic) when answer present in metadata
                            is_correct = False
                            if q_type == "MCQ" and current_meta and current_meta.get("answer") is not None:
                                try:
                                    is_correct = str(student_answer).strip().lower() == str(current_meta.get("answer")).strip().lower()
                                except Exception:
                                    is_correct = False
                            else:
                                # Use LLM grader for other types / fallback
                                is_correct = check_answer(st.session_state.current_problem, student_answer, st.session_state.model_choice)

                        st.session_state.sequencer.update_student_knowledge(st.session_state.skill_id, is_correct)
                        if is_correct:
                            st.success("That's correct! Fantastic work!", icon="✅")
                            st.session_state.current_problem = None
                            st.session_state.current_problem_meta = None
                            st.rerun()
                        else:
                            with st.spinner("Generating step-by-step solution..."):
                                solution = generate_solution(st.session_state.current_problem, st.session_state.model_choice)
                                st.session_state.last_solution = solution
                            st.session_state.review_mode = True
                            st.rerun()

    with knowledge_col:
        st.subheader("📊 Knowledge Map")
        if st.session_state.get('sequencer'):
            knowledge_data = st.session_state.sequencer.student_knowledge
            skill_names = [info['name'] for info in st.session_state.knowledge_graph.values()]
            mastery_levels = [knowledge_data.get(skill_id, 0) * 100 for skill_id in st.session_state.knowledge_graph.keys()]
            df = pd.DataFrame({'Skill': skill_names, 'Mastery (%)': mastery_levels}).set_index('Skill')
            st.bar_chart(df, height=400)

elif quiz_active:
    custom_title(USER_ICON_SVG, "Study Assistant", "Quiz Mode")
    st.markdown("---")
    quiz = st.session_state.quiz_questions
    index = st.session_state.current_quiz_index
    if not st.session_state.get('quiz_finished', False):
        current_q = quiz[index]
        st.info(f"**Question {index + 1}/{len(quiz)}:** {current_q.get('question_text', 'N/A')}")
        with st.form(key=f"quiz_form_{index}"):
            user_answer = None
            q_type = current_q.get('question_type')
            if q_type == 'MCQ':
                user_answer = st.radio("Choose your answer:", options=current_q.get('options', []), index=None)
            elif q_type == 'Fill in the Blank':
                user_answer = st.text_input("Your answer:")
            
            submitted = st.form_submit_button("Submit Answer")
            if submitted and user_answer is not None:
                st.session_state.user_answers.append(user_answer)
                if st.session_state.current_quiz_index < len(quiz) - 1:
                        st.session_state.current_quiz_index += 1
                else:
                    st.session_state.quiz_finished = True
                st.rerun()
    else:
        score = 0
        for i, question_data in enumerate(quiz):
            if i < len(st.session_state.user_answers) and str(st.session_state.user_answers[i]).strip().lower() == str(question_data.get('answer')).strip().lower():
                score += 1
        st.session_state.quiz_score = score
        st.success(f"🎉 Quiz Complete! Your final score is: {st.session_state.quiz_score}/{len(quiz)} ({st.session_state.quiz_score/len(quiz):.2%})")
        st.markdown("---")
        st.subheader("Detailed Review")
        for i, question_data in enumerate(quiz):
            user_ans = st.session_state.user_answers[i] if i < len(st.session_state.user_answers) else "Not Answered"
            correct_ans = question_data.get('answer')
            is_correct = str(user_ans).strip().lower() == str(correct_ans).strip().lower()
            with st.container(border=True):
                st.markdown(f"**Question {i+1}:** {question_data.get('question_text')}")
                if is_correct:
                    st.success(f"Your answer: **{user_ans}**", icon="✅")
                else:
                    st.error(f"Your answer: **{user_ans}**", icon="❌")
                    st.info(f"Correct answer: **{correct_ans}**")
                st.markdown("**Source from transcript:**")
                st.markdown(f"> {question_data.get('source_quote', 'Source not available.')}")
        if st.button("Take another quiz or create flashcards"):
            st.session_state.quiz_questions = None
            st.rerun()

elif flashcards_active:
    custom_title(USER_ICON_SVG, "Study Assistant", "Flashcard Mode")
    st.markdown("---")
    cards = st.session_state.flashcards
    index = st.session_state.current_flashcard_index
    card = cards[index]
    st.info(f"**Card {index + 1}/{len(cards)}**")
    if not st.session_state.flashcard_flipped:
        st.markdown(f"<div style='text-align: center; font-size: 24px; padding: 50px; border: 1px solid #ccc; border-radius: 10px;'>{card.get('term', 'N/A')}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='text-align: center; font-size: 18px; padding: 30px; border: 1px solid #ccc; border-radius: 10px;'>{card.get('definition', 'N/A')}</div>", unsafe_allow_html=True)
    _, nav_col, _ = st.columns([1,2,1])
    with nav_col:
        if st.button("Flip Card 🔁", use_container_width=True):
            st.session_state.flashcard_flipped = not st.session_state.flashcard_flipped
            st.rerun()
    prev_col, next_col = st.columns(2)
    with prev_col:
        if st.session_state.current_flashcard_index > 0:
            if st.button("⬅️ Previous Card", use_container_width=True):
                st.session_state.current_flashcard_index -= 1
                st.session_state.flashcard_flipped = False
                st.rerun()
    with next_col:
        if st.session_state.current_flashcard_index < len(cards) - 1:
            if st.button("Next Card ➡️", use_container_width=True):
                st.session_state.current_flashcard_index += 1
                st.session_state.flashcard_flipped = False
                st.rerun()
else:
    # Welcome Screen
    custom_title(USER_ICON_SVG, "Personalized Adaptive Learning Agent", "Your AI-powered tutor")
    st.markdown("I can be your personal tutor for almost any subject or document.")
    st.info("👈 **Select a mode and load your content in the sidebar to get started.**")
