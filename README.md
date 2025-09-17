

# 🎓 PAL Agent: Personalized Adaptive Learning Agent

The PAL Agent is a sophisticated, AI-powered tutoring application designed to provide a personalized learning experience for any subject. It combines a structured pedagogical framework with the power of Large Language Models (LLMs) to create a dynamic and responsive study companion.

The application features two primary modes: a general **AI Tutor** that can teach any topic from scratch and a **PDF Study Assistant** that can turn a user's own documents (like lecture notes or research papers) into interactive study materials.

-----

## ✨ Key Features

We've packed the PAL Agent with a rich set of features to create a truly adaptive learning environment:

  * **Dynamic Curriculum Design:** Don't have a pre-made course? No problem. The AI can generate a logical, multi-skill curriculum (a "knowledge graph") for any topic you provide, from "Basic Python Programming" to "The History of Ancient Rome."

  * **🧠 AI Tutor Mode:**

      * **Adaptive Learning Path:** Using Bayesian Knowledge Tracing (BKT), the tutor assesses your mastery of each skill in real-time. It only presents new topics after you've mastered the prerequisites, ensuring you're never overwhelmed.
      * **Dynamic Difficulty Scaling:** Questions within a topic automatically adjust their difficulty (Easy, Medium, Hard) based on your performance, keeping you challenged but not frustrated.
      * **Versatile Question Types:** For coding topics, the tutor generates a mix of questions, including "find the bug," "predict the output," and standard "write the code" challenges.
      * **Practice Mode:** Allows you to bypass the adaptive path and focus your practice on a specific skill of your choice.
      * **Advanced Control:** You can guide the AI by providing a sub-topic or even a sample question to match its style and format.

  * **📄 PDF Study Assistant (RAG-Powered):**

      * **Upload & Learn:** Upload any PDF, and the agent uses Retrieval-Augmented Generation (RAG) to understand its content.
      * **Interactive Quizzing:** Generate a custom quiz with a mix of Multiple-Choice and Fill-in-the-Blank questions based on your document.
      * **Source-Grounded Feedback:** After the quiz, a detailed review shows you which questions you got right or wrong, along with the **exact quote from the PDF** that serves as the source for the correct answer.
      * **Flashcard Generation:** Automatically extract key terms and definitions from your document and generate a set of interactive, flippable flashcards for quick review.

-----

## 💡 What Makes the PAL Agent Unique?

While there are many learning tools available, the PAL Agent stands out for several reasons:

1.  **Hyper-Personalization:** Unlike platforms with fixed curricula, the PAL Agent creates its learning path on the fly, tailored to the user's specific topic of interest.
2.  **Hybrid Intelligence:** It's not just a simple chatbot. It combines a structured pedagogical model (the BKT-powered knowledge graph) with the flexible, creative power of LLMs. This ensures a learning path that is both logical and engaging.
3.  **Document-Specific Learning:** The RAG-powered PDF assistant is a killer feature. It turns a user's passive study materials into active, personalized learning tools, bridging the gap between their course content and their practice.
4.  **Model Agnostic:** The architecture is designed to be flexible. It can run on a powerful cloud API like Google Gemini for maximum reliability or be configured to run **100% locally** on a model like Llama 3 for privacy and cost-free operation.

-----

## 🛠️ Technology Stack

  * **Frontend:** [Streamlit](https://streamlit.io/)
  * **AI / LLM Orchestration:** [LangChain](https://www.langchain.com/)
  * **LLMs:** The architecture supports both:
      * **Cloud APIs:** Google Gemini
      * **Local Models:** Ollama with Llama 3
  * **RAG Components:**
      * **PDF Parsing:** `PyPDF`
      * **Embeddings:** `Sentence-Transformers`
      * **Vector Store:** `FAISS`
  * **Core Logic:** Python, Pandas

-----

## 🚀 Setup and Installation

Follow these steps to get the PAL Agent running on your local machine.

1.  **Clone the repository (or set up your project folder):**

    ```bash
    git clone <your-repo-url>
    cd AGENT
    ```

2.  **Create and activate a Python virtual environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required libraries:**
    Make sure you have a `requirements.txt` file with all the necessary libraries, then run:

    ```bash
    pip install -r requirements.txt
    ```

4.  **(Optional) Set up API Keys:**
    If you are using the Gemini API, create a folder named `.streamlit` and inside it, a file named `secrets.toml`. Add your key:

    ```toml
    # .streamlit/secrets.toml
    GOOGLE_API_KEY = "AIzaSy..."
    ```

5.  **(Optional) Set up a custom theme:**
    In the `.streamlit` folder, create a file named `config.toml` to define your theme.

-----

## ▶️ How to Run

1.  Make sure your local Ollama server is running (if you are using the all-local version).
2.  Run the following command in your terminal:
    ```bash
    streamlit run app.py
    ```
3.  The application will open in your web browser. Enjoy your personalized learning session\!
