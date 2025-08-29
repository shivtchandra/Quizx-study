# llm_integration.py

import requests
import json
import re
import time
import os
import random # NEW: Import the random module

# --- NEW: Import and Configure Gemini ---
import google.generativeai as genai

# IMPORTANT: Replace "YOUR_API_KEY" with the key you got from Google AI Studio
try:
    # --- PASTE YOUR GOOGLE API KEY HERE ---
    GOOGLE_API_KEY = ""
    genai.configure(api_key=GOOGLE_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-pro-latest')
    print("Gemini configured successfully.")
except Exception as e:
    print(f"Error configuring Gemini: {e}")
    gemini_model = None

# --- Configuration for Local Llama 3 ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"

def _call_llama(prompt: str, json_mode: bool = False) -> str:
    # ... (This function remains unchanged) ...
    payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
    if json_mode:
        payload["format"] = "json"
    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        return response.json().get('response', '{}').strip()
    except Exception as e:
        return f'{{"error": "Llama 3 connection failed: {e}"}}'

# --- Function 1: The AI Curriculum Designer ---
def generate_knowledge_graph(topic: str) -> dict:
    # ... (This function remains unchanged) ...
    if not gemini_model:
        return {}
    prompt = (
        f"You are an expert curriculum designer AI that only outputs raw, valid JSON. "
        f"Create a knowledge graph for the topic: '{topic}'. "
        f"The graph must contain 5 to 7 fundamental skills. "
        f"For each skill, create a unique snake_case ID, a descriptive 'name', and a list of 'prerequisites'. "
        f"The first skill must have an empty prerequisites list. The graph must be logical. "
        f"Your output must be ONLY the JSON object. Example format: {{\"skill_1\": {{\"name\": \"...\", \"prerequisites\": []}}, \"skill_2\": {{\"name\": \"...\", \"prerequisites\": [\"skill_1\"]}}}}"
    )
    try:
        response = gemini_model.generate_content(prompt)
        json_str = response.text.strip().replace("```json", "").replace("```", "")
        graph = json.loads(json_str)
        if isinstance(graph, dict) and len(graph) > 2:
            return graph
        return {}
    except Exception as e:
        return {}

# --- Function 2: The Question Generator (NOW UPGRADED) ---
def generate_question(skill_name: str, sub_topic: str = None, sample_question: str = None) -> str:
    """
    Generates a question. If the topic is a coding language, it will randomly
    choose between different question types (e.g., write code, find bug, predict output).
    """
    
    # --- NEW: Logic to detect coding topics ---
    coding_keywords = ['python', 'javascript', 'java', 'c++', 'sql', 'html', 'css']
    is_coding_topic = any(keyword in skill_name.lower() for keyword in coding_keywords)
    
    prompt = ""
    # Use the user's sample question as the highest priority if provided
    if sample_question and sample_question.strip():
        prompt = (
            f"You are a helpful tutor. Generate a new, different problem that matches the style, format, and difficulty of this example: "
            f"'{sample_question}'. The main topic is '{skill_name}'."
        )
    # If it's a coding topic, choose a random question type
    elif is_coding_topic:
        question_types = ['write_code', 'find_bug', 'predict_output']
        chosen_type = random.choice(question_types)
        
        focus = f"on the topic of '{skill_name}'"
        if sub_topic and sub_topic.strip():
            focus += f" with a specific focus on '{sub_topic}'"

        if chosen_type == 'write_code':
            prompt = f"Ask the user to write a simple piece of code {focus}."
        elif chosen_type == 'find_bug':
            prompt = (
                f"Create a short code snippet {focus} that contains a single, common bug. "
                f"Then, ask the user to find and fix the bug."
            )
        elif chosen_type == 'predict_output':
            prompt = (
                f"Create a short, non-trivial code snippet {focus}. "
                f"Then, ask the user to predict what the final output of the code will be when it's run."
            )
    # For all other non-coding topics, or as a fallback
    else:
        prompt = f"Generate one simple, clear problem suitable for a beginner on the main topic of '{skill_name}'."
        if sub_topic and sub_topic.strip():
            prompt += f" The problem must focus specifically on the sub-topic: '{sub_topic}'."
            
    prompt += "\n\nProvide only the problem itself, with no extra conversational text, explanation, or the answer."
    
    return _call_llama(prompt, json_mode=False)


# --- (The other functions: generate_hints, check_answer, generate_solution remain unchanged) ---
def generate_hints(problem: str) -> list:
    # ... (function is unchanged) ...
    prompt = (
        f"You are a helpful tutor. Provide exactly three hints for the problem: '{problem}'. "
        f"Format your response as a JSON object with a single key 'hints' which contains a list of three strings. Example: {{\"hints\": [\"Hint 1\", \"Hint 2\", \"Hint 3\"]}}"
    )
    response_str = _call_llama(prompt, json_mode=True)
    try:
        result = json.loads(response_str)
        return result.get("hints", [])
    except (json.JSONDecodeError, AttributeError):
        return ["Failed to generate hints.", "", ""]

def check_answer(problem: str, student_answer: str) -> bool:
    # ... (function is unchanged) ...
    prompt = (
        f"You are a precise grading AI. The problem is: '{problem}'. The student's answer is: '{student_answer}'. "
        f"Respond with a JSON object with a single key 'status' which is either 'correct' or 'incorrect'. Example: {{\"status\": \"correct\"}}"
    )
    response_str = _call_llama(prompt, json_mode=True)
    try:
        result = json.loads(response_str)
        return result.get('status') == 'correct'
    except (json.JSONDecodeError, AttributeError):
        return False

def generate_solution(problem: str) -> str:
    # ... (function is unchanged) ...
    prompt = f"You are an expert teacher. Provide a clear, encouraging, step-by-step solution for the problem: {problem}"
    return _call_llama(prompt, json_mode=False)