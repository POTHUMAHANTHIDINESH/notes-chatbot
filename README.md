# 📚 Notes Chatbot — AI-Powered RAG Assistant

A Retrieval-Augmented Generation (RAG) based AI assistant that allows users to upload PDF documents and ask context-aware questions with grounded, citation-backed answers.

Designed for students, researchers, and exam preparation.

---

# 🚀 Features

- Upload multiple PDF documents
- Ask questions in natural language
- Retrieve relevant context from documents
- Generate accurate answers using LLM
- Provide page-level citations
- Streamlit-based UI

---

# 🧠 Architecture

User Query
↓
Embedding (Sentence Transformers)
↓
Vector Search (FAISS)
↓
Top-K Chunks Retrieved
↓
LLM (Groq / Llama 3)
↓
Final Answer + Citations

---

# 🛠️ Tech Stack

- PyPDF
- SentenceTransformers
- FAISS
- Groq API (LLaMA 3)
- Streamlit
- Python

---

# ⚙️ Workflow

1. PDFs are parsed page by page
2. Text is split into chunks
3. Embeddings are generated
4. Stored in FAISS index
5. Query is embedded
6. Similar chunks retrieved
7. LLM generates grounded response

---

# 📂 Project Structure

notes-chatbot/
├── app.py
├── rag_engine.py
├── eval.py
├── requirements.txt
├── .gitignore
└── README.md

---

# 🚀 Setup

git clone https://github.com/YOUR_USERNAME/notes-chatbot.git
cd notes-chatbot

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
streamlit run app.py

---

# 🔑 API Setup

Get key: https://console.groq.com/keys

Windows:
setx GROQ_API_KEY "your_key"

Mac/Linux:
export GROQ_API_KEY=your_key

---

# 📊 Evaluation

Run:
python eval.py

---

# 💡 Highlights

- End-to-end RAG system
- Local embeddings
- Grounded answers with citations
- Lightweight and deployable

---

# 👨‍💻 Author
Dinesh
