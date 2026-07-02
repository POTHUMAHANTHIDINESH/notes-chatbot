# 📚 Notes Chatbot — RAG over your own PDFs, 100% free

Upload your lecture notes / textbook PDFs, ask questions in plain English,
get answers grounded in *your* material with citations back to the exact
file and page. Built for exam prep.

**Stack (every piece is free, no credit card anywhere):**

| Piece | Tool |
|---|---|
| PDF parsing | `pypdf` |
| Embeddings | `sentence-transformers` (runs locally on CPU) |
| Vector search | `FAISS` (local file, no hosted database) |
| Answer generation | [Groq API](https://console.groq.com) free tier (Llama 3.3 70B) |
| UI | Streamlit |
| Hosting | Streamlit Community Cloud |

---

## 1. Get a free Groq API key (2 minutes)

1. Go to https://console.groq.com/keys
2. Sign up with email or Google — **no credit card required**.
3. Click "Create API Key", copy it. You'll paste this into the app's sidebar
   (or set it as an environment variable — see below).

Free tier gives you 30 requests/min and 14,400 requests/day — more than
enough for studying.

---

## 2. Run it locally

```bash
git clone https://github.com/YOUR_USERNAME/notes-chatbot.git
cd notes-chatbot

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

streamlit run app.py
```

This opens the app in your browser at `http://localhost:8501`.

- Paste your Groq API key into the sidebar (or put it in a `.env` file —
  copy `.env.example` to `.env` and fill it in, or export it as
  `GROQ_API_KEY` in your shell).
- Upload your PDFs and click **Build / rebuild index**.
- Ask questions in the chat box.

The first run downloads the small embedding model (~90MB) once; after that
it's cached locally and everything runs offline except the actual Groq
answer-generation call.

---

## 3. Push this project to GitHub

If you haven't already, from inside the `notes-chatbot` folder:

```bash
git init
git add .
git commit -m "Initial commit: RAG notes chatbot"

# Create a new repo on GitHub first (github.com/new), then:
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/notes-chatbot.git
git push -u origin main
```

Your Groq key is **never** committed — it's excluded via `.gitignore`
(`.env` and `.streamlit/secrets.toml` are both ignored) and is only ever
typed into the running app or read from an environment variable.

---

## 4. Deploy for free — Streamlit Community Cloud

1. Push the repo to GitHub (step 3).
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **New app**, pick your `notes-chatbot` repo, branch `main`, main
   file `app.py`.
4. Under **Advanced settings → Secrets**, add:
   ```toml
   GROQ_API_KEY = "your_key_here"
   ```
   (This is optional — users can also just paste their own key into the
   sidebar every time, which is nice if you want to share the app publicly
   without giving away your key.)
5. Click **Deploy**. You'll get a public URL like
   `https://notes-chatbot-yourname.streamlit.app` within a minute or two.

That's the whole deployment — no servers, no Docker, no billing setup.

### Alternative free hosts
- **Hugging Face Spaces** (Streamlit SDK) — same idea, upload the same
  files, set `GROQ_API_KEY` as a Space secret.
- **Render.com free web service** — works too, but free instances sleep
  after inactivity and are slower to wake than Streamlit Cloud.

---

## 5. How it works

1. **Ingest**: each PDF is read page by page (`pypdf`), so every chunk keeps
   its source filename and page number.
2. **Chunk**: page text is split into ~900-character overlapping windows so
   answers aren't cut off mid-thought.
3. **Embed**: each chunk is turned into a vector locally with
   `all-MiniLM-L6-v2` (no API call, no cost, fast on CPU).
4. **Index**: vectors go into a `FAISS` flat index (cosine similarity),
   saved to `vectorstore/` so you don't have to re-embed every session.
5. **Retrieve**: your question is embedded the same way, and the top 5
   most similar chunks are pulled out.
6. **Generate**: those chunks + your question are sent to Groq's free
   Llama 3.3 70B endpoint with an instruction to answer *only* from the
   given context and cite file + page.

---

## 6. Evaluating the pipeline

`eval.py` measures two things separately, since they're different failure
modes:

- **Retrieval accuracy** — did the correct source file/page show up in the
  top-3 retrieved chunks for a given question?
- **Answer accuracy** — does the final LLM answer actually contain the key
  fact(s) expected? (Retrieval can succeed while the LLM still gets the
  answer wrong, or vice versa — measuring both tells you where the problem
  lives.)

To run it:
1. Build an index first via the Streamlit app (upload PDFs → build index).
2. Open `eval.py` and replace the placeholder `TEST_CASES` with real
   questions about your own notes — pick ones where you already know the
   exact file/page the answer lives on.
3. Run:
   ```bash
   python eval.py
   ```

Example output:
```
Retrieval accuracy: 8/10 (80%)
Answer accuracy:    7/10 (70%)
```

---

## 7. Project structure

```
notes-chatbot/
├── app.py              # Streamlit UI
├── rag_engine.py        # ingestion, embedding, retrieval, generation
├── eval.py               # retrieval + answer accuracy evaluation
├── requirements.txt
├── .gitignore
├── .env.example
├── README.md
└── vectorstore/          # generated at runtime, gitignored
```

---

## 8. Extending it

- **Persist across users**: currently the index is local to wherever the
  app runs. For a shared deployed app with multiple users, swap the local
  `vectorstore/` for a per-user upload flow (already how it works — each
  session's uploads rebuild the index) or add user auth + per-user storage.
- **More file types**: add a `.pptx`/`.docx` extractor next to `extract_pages`
  in `rag_engine.py` if your notes aren't all PDFs.
- **Better retrieval**: swap `IndexFlatIP` for `IndexHNSWFlat` if your notes
  folder grows very large (thousands of pages) — flat search is fine up to
  a few hundred pages.
"# notes-chatbot" 
