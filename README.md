📚 Notes Chatbot — RAG over your own PDFs, 100% free

Ask questions about your own lecture notes / textbook PDFs and get answers
grounded in your material, with citations back to the exact file and page.
Built for exam prep.

Stack (every piece is free, no credit card anywhere):

PieceToolPDF parsingpypdfEmbeddingssentence-transformers (runs locally, no API)Vector searchFAISS (local file, no hosted database)Answer generationGroq API free tier (Llama 3.3 70B)UIStreamlitHostingStreamlit Community Cloud

Setup


Get a free Groq API key — sign up at console.groq.com/keys (no credit card).
Install and run:


bash   git clone https://github.com/YOUR_USERNAME/notes-chatbot.git
   cd notes-chatbot
   python -m venv venv
   venv\Scripts\activate        # Mac/Linux: source venv/bin/activate
   pip install -r requirements.txt
   streamlit run app.py


Paste your Groq key into the sidebar (or set it once with
setx GROQ_API_KEY "your_key" on Windows / export GROQ_API_KEY=your_key
on Mac/Linux, so you never have to re-enter it).
Upload your PDFs → Build / rebuild index → ask questions in the chat box.


How it works


Ingest — each PDF is read page by page (pypdf) so every chunk keeps its source filename and page number.
Chunk — page text is split into ~900-character overlapping windows.
Embed — each chunk becomes a vector locally via all-MiniLM-L6-v2 (no API call, no cost).
Index — vectors go into a local FAISS index, cached in vectorstore/.
Retrieve — your question is embedded the same way; the top 5 most similar chunks are pulled out.
Generate — those chunks + your question go to Groq's free Llama 3.3 70B model, instructed to answer only from the given context and cite file + page.


Evaluating retrieval & answer quality

eval.py measures two things separately:


Retrieval accuracy — did the correct file/page show up in the top-3 retrieved chunks?
Answer accuracy — does the final answer contain the expected key facts?


Edit TEST_CASES in eval.py with real questions about your own notes, then:

bashpython eval.py

Retrieval accuracy: 8/10 (80%)
Answer accuracy:    7/10 (70%)

Deploy for free

Push to GitHub → share.streamlit.io → sign in with GitHub → New app → pick this repo, branch main, file app.py → add GROQ_API_KEY under Secrets (optional) → Deploy.

Project structure

notes-chatbot/
├── app.py           # Streamlit UI
├── rag_engine.py     # ingestion, embedding, retrieval, generation
├── eval.py            # retrieval + answer accuracy evaluation
├── requirements.txt
├── .gitignore
├── .env.example
└── README.md
