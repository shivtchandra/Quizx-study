# llm_integration.py

import streamlit as st
import json
import random
import requests
import google.generativeai as genai
from typing import Optional, Union

# --- Configuration for Gemini API ---
try:
    # This securely reads the API key from your Streamlit Secrets file
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')
except (KeyError, Exception):
    gemini_model = None # Will be handled gracefully if user selects Gemini without a key

# --- Configuration for Local Llama 3 ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"

# --- Core Helper Functions to Call Each Model ---

def _call_llama(prompt: str, json_mode: bool = False) -> str:
    """Helper function to call the local Llama 3 API via Ollama."""
    payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
    if json_mode:
        payload["format"] = "json"
    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        return response.json().get('response', '{}').strip()
    except requests.exceptions.RequestException:
        st.error(f"Failed to connect to Local AI. Is Ollama running?", icon="❌")
        return '{"error": "Connection to local AI failed."}' if json_mode else "Connection to local AI failed."

def _call_gemini(prompt: str, expect_json: bool = False) -> str:
    """Helper function to call the Gemini API with safety settings and error checking."""
    if not gemini_model:
        return '{"error": "Gemini model is not configured."}' if expect_json else "Error: Gemini model not configured. Please add GOOGLE_API_KEY to your secrets."
    safety_settings = {
        'HARM_CATEGORY_HARASSMENT': 'BLOCK_ONLY_HIGH',
        'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_ONLY_HIGH',
        'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_ONLY_HIGH',
        'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_ONLY_HIGH',
    }
    try:
        response = gemini_model.generate_content(prompt, safety_settings=safety_settings)
        if not response.candidates or response.candidates[0].finish_reason.name != "STOP":
            return '{"error": "Response was blocked by safety filters."}' if expect_json else "Response was blocked by safety filters."
        return response.text.strip().replace("```json", "").replace("```", "")
    except Exception as e:
        return f'{{"error": "Error calling Gemini: {e}"}}' if expect_json else f"Error calling Gemini: {e}"

# --- Main Functions Now Use the Model Choice to Decide Which Helper to Call ---


# New: coding prompt templates (you can expand these)
CODING_QUESTION_PROMPTS = {
    'write_code': (
        "Write a short (<=30 lines) function that solves the described problem. "
        "Include function signature and one short example input -> output in a comment."
    ),
    'find_bug': (
        "Provide a short code snippet (6-12 lines) that contains a subtle bug. "
        "Ask the user to identify the bug and provide the corrected code."
    ),
    'predict_output': (
        "Provide a short code snippet (6-12 lines) and ask the user to predict the output. "
        "Make the snippet tricky but not obfuscated (loops, scopes, small gotchas)."
    ),
    'explain_concept': (
        "Provide a brief code example and ask the user to explain what concept is demonstrated "
        "(e.g., closure, memoization). Keep example minimal."
    ),
    'refactor_code': (
        "Provide a simple but intentionally inefficient piece of code (6-12 lines). "
        "Ask the user to refactor it to be more efficient and explain the optimization."
    )
}

def _ensure_json(text: str) -> dict:
    """Attempt to parse JSON and return {} on failure."""
    try:
        return json.loads(text)
    except Exception:
        return {}

def generate_knowledge_graph(topic: str, model_choice: str) -> dict:
    prompt = (
        "You are an expert curriculum designer. Output ONLY raw JSON (no surrounding text).\n\n"
        f"Create an ordered knowledge graph for '{topic}' with 5-7 skills.\n"
        "Each skill must be an object keyed by a snake_case id and include exactly these fields:\n"
        "  - name: string (3-6 words)\n"
        "  - prerequisites: list of skill ids (may be empty)\n"
        "  - learning_objective: one short sentence\n"
        "  - est_time_mins: integer\n\n"
        "First (foundational) skill MUST have prerequisites: [].\n"
        "Return JSON only. Example:\n"
        "{\"variables_and_types\": {\"name\": \"Variables and Types\", \"prerequisites\": [], \"learning_objective\": \"...\", \"est_time_mins\": 20}, ...}"
    )
    if model_choice == "Cloud AI (Gemini)":
        response_str = _call_gemini(prompt, expect_json=True)
    else:
        response_str = _call_llama(prompt, json_mode=True)
    graph = _ensure_json(response_str)
    return graph if isinstance(graph, dict) and graph else {}

def generate_question(
    skill_name: str,
    model_choice: str,
    sub_topic: Optional[str] = None,
    sample_question: Optional[str] = None,
    difficulty: str = "Medium",
    search_online: bool = False,
    output_format: str = "plain",   # "plain" or "full_quiz"
    quiz_type_hint: Optional[str] = None,  # e.g., "MCQ", "Coding", "Fill in the Blank"
    coding_prompt_type: Optional[str] = None  # one of CODING_QUESTION_PROMPTS keys
) -> Union[str, dict]:
    """
    If output_format == "plain": returns a string (legacy behavior).
    If output_format == "full_quiz": returns a dict:
      {
        "question_text": "...",
        "question_type": "MCQ" | "Coding" | "Fill in the Blank" | "Short Answer",
        "options": [...],           # for MCQ
        "answer": "...",            # optional (you can choose to leave out for display)
        "metadata": {"style": "LeetCode", "coding_prompt_type": "write_code"}
      }
    """
    difficulty_map = {
        "Easy": "single-step, conceptual or application problem appropriate for beginners",
        "Medium": "multi-step problem requiring synthesis or procedural steps",
        "Hard": "challenging multi-step problem that requires deeper reasoning"
    }
    style_instruction = (
        "Match reputable online learning/quiz sources. "
        "Use Khan Academy style for conceptual questions, LeetCode/GeeksforGeeks style for code problems, "
        "and Brilliant-style for math word problems."
    )

    # If coding question and a specific coding_prompt_type given, use that template
    coding_instr = ""
    if quiz_type_hint and quiz_type_hint.lower() == "coding":
        if coding_prompt_type and coding_prompt_type in CODING_QUESTION_PROMPTS:
            coding_instr = CODING_QUESTION_PROMPTS[coding_prompt_type]
        else:
            # sensible default
            coding_instr = CODING_QUESTION_PROMPTS['write_code']

    base_prompt = [
        "You are a high-quality educational content generator.",
        "Produce ONE problem (no answer or extra commentary) unless output_format requests JSON.",
        f"Skill: '{skill_name}'. Difficulty: {difficulty}.",
        f"Guidance: {difficulty_map.get(difficulty,'multi-step problem')}.",
        f"Style note: {style_instruction}.",
    ]
    if sub_topic and sub_topic.strip():
        base_prompt.append(f"Focus on sub-topic: '{sub_topic}'.")
    if sample_question and sample_question.strip():
        base_prompt.append("Write a NEW problem that matches the style and difficulty of this example (do not reuse wording or numbers):")
        base_prompt.append(f"Example: '{sample_question}'")
    if search_online:
        base_prompt.append(
            "When search_online is enabled, closely match phrasing and tone of common online quiz sources (do NOT add links)."
        )
    if coding_instr:
        base_prompt.append("Coding instructions: " + coding_instr)

    # Build final prompt
    if output_format == "plain":
        # Plain text question (legacy)
        final_prompt = "\n".join(base_prompt) + "\n\nOutput: the single problem statement ONLY (no JSON)."
        if model_choice == "Cloud AI (Gemini)":
            return _call_gemini(final_prompt)
        else:
            return _call_llama(final_prompt)

    # --- full_quiz JSON output requested ---
    # instruct model to return a JSON object with defined fields
    json_request = (
        "Output ONLY a JSON object with these fields:\n"
        "  - question_text: string (the problem statement)\n"
        "  - question_type: one of ['MCQ','Coding','Fill in the Blank','Short Answer']\n"
        "  - options: list of strings (include only for MCQ; otherwise [])\n"
        "  - answer: the canonical answer (optional if you want to hide answers in UI)\n"
        "  - metadata: object with optional keys like {'style':'LeetCode','coding_prompt_type':'write_code'}\n\n"
        "Ensure JSON is valid and contains only the object (no surrounding text)."
    )

    final_prompt = "\n".join(base_prompt) + "\n\n" + json_request

    if model_choice == "Cloud AI (Gemini)":
        response_str = _call_gemini(final_prompt, expect_json=True)
    else:
        response_str = _call_llama(final_prompt, json_mode=True)

    parsed = _ensure_json(response_str)
    # Minimal normalization so UI can rely on fields
    if not parsed:
        # fallback: return a simple dict with plain text if parsing failed
        text_fallback = _call_gemini(final_prompt) if model_choice == "Cloud AI (Gemini)" else _call_llama(final_prompt)
        return {
            "question_text": text_fallback if isinstance(text_fallback, str) else str(text_fallback),
            "question_type": quiz_type_hint or "Short Answer",
            "options": [],
            "answer": None,
            "metadata": {"style": "unknown", "coding_prompt_type": coding_prompt_type}
        }
    # Guarantee keys exist
    parsed.setdefault("question_text", parsed.get("question", "") or "")
    parsed.setdefault("question_type", parsed.get("question_type", quiz_type_hint or "Short Answer"))
    parsed.setdefault("options", parsed.get("options", []) or [])
    parsed.setdefault("answer", parsed.get("answer", None))
    parsed.setdefault("metadata", parsed.get("metadata", {}))
    # add coding hint if present
    if coding_prompt_type:
        parsed["metadata"].setdefault("coding_prompt_type", coding_prompt_type)
    return parsed

def generate_hints(problem: str, model_choice: str) -> list:
    prompt = (
        "You are a stepwise tutor. Given the problem below, provide EXACTLY three hints as JSON:\n"
        "{\"hints\": [\"Hint 1 - minimal nudge\", \"Hint 2 - method\", \"Hint 3 - near solution but not the answer\"]}\n\n"
        f"Problem: {problem}\n\nHints must be progressive."
    )
    if model_choice == "Cloud AI (Gemini)":
        response_str = _call_gemini(prompt, expect_json=True)
    else:
        response_str = _call_llama(prompt, json_mode=True)
    parsed = _ensure_json(response_str)
    return parsed.get("hints", []) if isinstance(parsed, dict) else []

def check_answer(problem: str, student_answer: str, model_choice: str) -> bool:
    prompt = (
        "You are an accurate grader. Respond ONLY with JSON: {\"status\":\"correct\"|\"incorrect\", \"confidence\": float}.\n"
        "Be conservative when uncertain. Use confidence 0.7+ for clear correctness.\n\n"
        f"Problem: {problem}\nStudent answer: {student_answer}\n\nReturn JSON only."
    )
    if model_choice == "Cloud AI (Gemini)":
        response_str = _call_gemini(prompt, expect_json=True)
    else:
        response_str = _call_llama(prompt, json_mode=True)
    parsed = _ensure_json(response_str)
    return parsed.get("status") == "correct"
    
def generate_solution(problem: str, model_choice: str) -> str:
    prompt = (
        "You are an expert teacher. Provide a clear, encouraging step-by-step solution.\n\n"
        "Output plain text format:\n"
        "Final answer: <one-line>\n"
        "Steps:\n  1. ...\n  2. ...\nCommon mistakes: <one sentence>\nEncouragement: <one short sentence>\n\n"
        f"Problem: {problem}"
    )
    if model_choice == "Cloud AI (Gemini)":
        return _call_gemini(prompt)
    else:
        return _call_llama(prompt)
