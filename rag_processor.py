# rag_processor.py

import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import tempfile
import os
import json
import google.generativeai as genai

@st.cache_resource
def get_embeddings_model():
    """Loads the embedding model from HuggingFace, caching it for performance."""
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

@st.cache_resource
def get_gemini_model():
    """Initializes and caches the Gemini model from Streamlit secrets."""
    try:
        GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=GOOGLE_API_KEY)
        return genai.GenerativeModel('gemini-1.5-flash')
    except (KeyError, Exception) as e:
        st.error(f"Error configuring Gemini: {e}. Please check your API key.", icon="🚨")
        return None

def _process_pdf_and_get_context(pdf_file):
    """Helper to process a PDF and return a string of the most relevant context."""
    vector_store = None
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(pdf_file.getvalue())
        pdf_path = tmp_file.name
    try:
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        texts = text_splitter.split_documents(documents)
        embeddings = get_embeddings_model()
        vector_store = FAISS.from_documents(texts, embeddings)
    finally:
        os.remove(pdf_path)
    
    if not vector_store:
        st.error("Could not process the PDF document.")
        return None
        
    retriever = vector_store.as_retriever(search_kwargs={'k': 10})
    docs = retriever.invoke("Key concepts, facts, and definitions from the document.")
    return " ".join([doc.page_content for doc in docs])

def process_pdf_and_generate_quiz(pdf_file, num_questions=5) -> list:
    """Main function for quizzes using the Gemini API."""
    context = _process_pdf_and_get_context(pdf_file)
    if not context: return []

    gemini_model = get_gemini_model()
    if not gemini_model: return []

    prompt = (
        f"You are an expert quiz creator AI. Based ONLY on the following context from a document, generate a list of exactly {num_questions} difficult quiz questions that test for conceptual understanding. "
        f"The questions should be a mix of Multiple Choice (MCQ) and Fill in the Blank. "
        f"Respond with ONLY a valid JSON list of objects. Each object must have five keys: "
        f"'question_text', 'question_type', 'options' (a list of 4 plausible strings for MCQ, or empty), 'answer', and 'source_quote' (a direct, short quote from the context that proves the answer).\n\n"
        f"CONTEXT:\n{context}"
    )
    
    try:
        response = gemini_model.generate_content(prompt)
        json_response = response.text.strip().replace("```json", "").replace("```", "")
        quiz_list = json.loads(json_response)
        return quiz_list if isinstance(quiz_list, list) else []
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error generating or parsing quiz JSON with Gemini: {e}")
        st.error("The AI failed to generate a valid quiz from the document.")
        return []

def process_pdf_and_generate_flashcards(pdf_file, num_flashcards=10) -> list:
    """Main function for flashcards using the Gemini API."""
    context = _process_pdf_and_get_context(pdf_file)
    if not context: return []
    
    gemini_model = get_gemini_model()
    if not gemini_model: return []

    prompt = (
        f"You are an expert at creating study materials. Based ONLY on the following context, generate a list of exactly {num_flashcards} flashcards. "
        f"Each flashcard should represent a key term or a core concept. "
        f"Respond with ONLY a valid JSON list of objects. Each object must have two keys: 'term' and 'definition'.\n\n"
        f"CONTEXT:\n{context}"
    )
    try:
        response = gemini_model.generate_content(prompt)
        json_response = response.text.strip().replace("```json", "").replace("```", "")
        flashcards = json.loads(json_response)
        return flashcards if isinstance(flashcards, list) else []
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error generating or parsing flashcard JSON with Gemini: {e}")
        st.error("The AI failed to generate valid flashcards.")
        return []