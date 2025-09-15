# llm_integration.py

import streamlit as st
import json
import random
import requests
import re
import time

# --- Configuration for Local Llama 3 ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"

# --- Core Function to Call the Local Llama 3 Model ---
def _call_llama(prompt: str, json_mode: bool = False) -> str:
    """Helper function to call the local Llama 3 API via Ollama."""
    payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
    if json_mode:
        payload["format"] = "json"
    
    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        return response.json().get('response', '{}').strip()
    except requests.exceptions.RequestException as e:
        # Provide an error message on the Streamlit page if connection fails
        st.error(f"Failed to connect to Local AI. Is Ollama running?", icon="❌")
        return f'{{"error": "Llama 3 connection failed: {e}"}}'
    except json.JSONDecodeError:
        return '{"error": "Failed to decode JSON response from Ollama"}'

# --- Function 1: The AI Curriculum Designer (Llama 3 Version) ---
def generate_knowledge_graph(topic: str) -> dict:
    """Uses a robust, two-step process to generate a knowledge graph with the local model."""
    
    # Step 1: Brainstorm a list of skills
    print(f"Step 1: Brainstorming skills for '{topic}' using Llama 3...")
    prompt_skills = (
        f"You are an expert curriculum designer. For the topic '{topic}', list the 5-7 most important skills a beginner should learn, in a logical learning order. "
        f"Respond with ONLY a valid JSON object containing a single key 'skills' which is a list of strings. "
        f"Example: {{\"skills\": [\"Skill Name 1\", \"Skill Name 2\"]}}"
    )
    
    response_skills_str = _call_llama(prompt_skills, json_mode=True)
    try:
        skills_data = json.loads(response_skills_str)
        skill_list = skills_data.get("skills", [])
        if not skill_list or not isinstance(skill_list, list):
            print("Llama 3 Step 1 Failed: Could not brainstorm skills.")
            return {}
    except (json.JSONDecodeError, AttributeError):
        print(f"Llama 3 Step 1 Failed: Invalid JSON for skills list. Got: {response_skills_str}")
        return {}

    print(f"Llama 3 Step 1 Success: Got skills: {skill_list}")
    
    # Step 2: Structure the skills into a graph
    print("Step 2: Structuring the skills into a knowledge graph using Llama 3...")
    formatted_skill_list = "\n".join([f"{i+1}. {name}" for i, name in enumerate(skill_list)])
    
    prompt_graph = (
        f"You are a curriculum structuring AI. Given this ordered list of skills for '{topic}':\n{formatted_skill_list}\n"
        f"Your task is to create a knowledge graph. Create a unique snake_case ID for each skill. "
        f"For each skill, determine its prerequisites ONLY from the skills that appear before it in the list. The first skill must have no prerequisites. "
        f"Respond with ONLY a valid JSON object using the exact skill names provided. "
        f"Example format: {{\"skill_1_id\": {{\"name\": \"Skill Name 1\", \"prerequisites\": []}}, \"skill_2_id\": {{\"name\": \"Skill Name 2\", \"prerequisites\": [\"skill_1_id\"]}}}}"
    )
    
    response_graph_str = _call_llama(prompt_graph, json_mode=True)
    try:
        graph = json.loads(response_graph_str)
        if isinstance(graph, dict) and len(graph) > 2:
            print("Llama 3 Step 2 Success: Curriculum generated.")
            return graph
        else:
            print("Llama 3 Step 2 Failed: Generated graph was invalid.")
            return {}
    except (json.JSONDecodeError, AttributeError):
        print(f"Llama 3 Step 2 Failed: Invalid JSON for graph structure. Got: {response_graph_str}")
        return {}


# --- All other functions also use the local Llama 3 model ---

def generate_question(skill_name: str, sub_topic: str = None, sample_question: str = None, difficulty: str = "Medium") -> str:
    difficulty_instructions = {
        "Easy": "The problem should be a straightforward, single-step question.",
        "Medium": "The problem should be a standard, multi-step question.",
        "Hard": "The problem should be a challenging word problem or a complex question."
    }
    prompt = f"Generate a {difficulty.lower()} problem for a beginner on the main topic of '{skill_name}'. {difficulty_instructions.get(difficulty, '')}"
    if sub_topic and sub_topic.strip():
        prompt += f" The problem must focus specifically on the sub-topic: '{sub_topic}'."
    if sample_question and sample_question.strip():
        prompt += f"\n\nGenerate a new, different problem that matches the style, format, and difficulty of this example: '{sample_question}'."
    coding_keywords = ['python', 'javascript', 'java', 'c++', 'sql', 'html', 'css']
    is_coding_topic = any(keyword in skill_name.lower() for keyword in coding_keywords)
    if is_coding_topic and not sample_question:
        question_types = {
            'write_code': f"Ask the user to write a simple piece of code {skill_name}.",
            'find_bug': f"Create a short code snippet for {skill_name} with a single, common bug, and ask the user to find and fix it.",
            'predict_output': f"Create a short code snippet for {skill_name} and ask the user to predict its final output."
        }
        chosen_type_prompt = random.choice(list(question_types.values()))
        prompt = f"Based on the following instruction: '{chosen_type_prompt}', create a {difficulty.lower()} level problem."
    prompt += "\n\nProvide only the problem itself, with no extra conversational text, explanation, or the answer."
    return _call_llama(prompt)

def generate_hints(problem: str) -> list:
    prompt = f"You are a helpful tutor. Provide exactly three hints for the problem: '{problem}'. Format your response as a JSON object: {{\"hints\": [\"Hint 1\", \"Hint 2\", \"Hint 3\"]}}"
    response_str = _call_llama(prompt, json_mode=True)
    try:
        return json.loads(response_str).get("hints", [])
    except (json.JSONDecodeError, AttributeError):
        return []

def check_answer(problem: str, student_answer: str) -> bool:
    prompt = f"You are a precise grading AI. The problem is: '{problem}'. The student's answer is: '{student_answer}'. Respond with a JSON object: {{\"status\": \"correct\"}} or {{\"status\": \"incorrect\"}}."
    response_str = _call_llama(prompt, json_mode=True)
    try:
        return json.loads(response_str).get('status') == 'correct'
    except (json.JSONDecodeError, AttributeError):
        return False

def generate_solution(problem: str) -> str:
    prompt = f"You are an expert teacher. Provide a clear, encouraging, step-by-step solution for the problem: {problem}"
    return _call_llama(prompt)