"""
rag_engine.py
Core RAG (Retrieval-Augmented Generation) pipeline for the notes chatbot.

Pipeline:
  1. Extract text from PDFs (page by page, so we can cite page numbers)
  2. Chunk text into overlapping windows
  3. Embed chunks locally with sentence-transformers (no API calls, no cost)
  4. Store vectors in a local FAISS index
  5. On a query: embed the question, retrieve top-k chunks, send them to
     Groq's free LLM API as context, and ask it to answer using only that
     context, citing the source file + page.
"""

import os
import pickle
from dataclasses import dataclass, field
from typing import List

import faiss
import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from groq import Groq

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # small, fast, runs on CPU, free
CHUNK_SIZE = 900          # characters per chunk
CHUNK_OVERLAP = 150       # characters of overlap between chunks
TOP_K = 5                 # how many chunks to retrieve per question
GROQ_MODEL = "llama-3.3-70b-versatile"

INDEX_DIR = "vectorstore"
INDEX_FILE = os.path.join(INDEX_DIR, "index.faiss")
META_FILE = os.path.join(INDEX_DIR, "meta.pkl")


@dataclass
class Chunk:
    text: str
    source: str      # filename
    page: int        # 1-indexed page number


@dataclass
class VectorStore:
    chunks: List[Chunk] = field(default_factory=list)
    index: faiss.Index = None

    def save(self):
        os.makedirs(INDEX_DIR, exist_ok=True)
        faiss.write_index(self.index, INDEX_FILE)
        with open(META_FILE, "wb") as f:
            pickle.dump(self.chunks, f)

    @classmethod
    def load(cls):
        if not (os.path.exists(INDEX_FILE) and os.path.exists(META_FILE)):
            return None
        index = faiss.read_index(INDEX_FILE)
        with open(META_FILE, "rb") as f:
            chunks = pickle.load(f)
        return cls(chunks=chunks, index=index)


_embedder = None


def get_embedder() -> SentenceTransformer:
    """Lazily load the embedding model (downloads once, then cached locally)."""
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedder


def extract_pages(pdf_path: str) -> List[tuple]:
    """Return list of (page_number, text) for a PDF file."""
    reader = PdfReader(pdf_path)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append((i, text))
    return pages


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + size, n)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == n:
            break
        start = end - overlap
    return chunks


def build_index(pdf_paths: List[str], progress_callback=None) -> VectorStore:
    """Build a fresh FAISS index from a list of PDF file paths."""
    embedder = get_embedder()
    all_chunks: List[Chunk] = []

    for pi, pdf_path in enumerate(pdf_paths):
        filename = os.path.basename(pdf_path)
        pages = extract_pages(pdf_path)
        for page_num, page_text in pages:
            for piece in chunk_text(page_text):
                all_chunks.append(Chunk(text=piece, source=filename, page=page_num))
        if progress_callback:
            progress_callback(pi + 1, len(pdf_paths), filename)

    if not all_chunks:
        raise ValueError("No extractable text found in the uploaded PDFs.")

    texts = [c.text for c in all_chunks]
    embeddings = embedder.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    embeddings = np.array(embeddings, dtype="float32")

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # inner product on normalized vectors = cosine similarity
    index.add(embeddings)

    store = VectorStore(chunks=all_chunks, index=index)
    store.save()
    return store


def retrieve(store: VectorStore, query: str, k: int = TOP_K) -> List[Chunk]:
    """Retrieve the top-k most relevant chunks for a query."""
    embedder = get_embedder()
    q_emb = embedder.encode([query], normalize_embeddings=True)
    q_emb = np.array(q_emb, dtype="float32")
    scores, idxs = store.index.search(q_emb, k)
    results = []
    for idx in idxs[0]:
        if idx == -1:
            continue
        results.append(store.chunks[idx])
    return results


def build_prompt(question: str, chunks: List[Chunk]) -> str:
    context_blocks = []
    for c in chunks:
        context_blocks.append(f"[Source: {c.source}, page {c.page}]\n{c.text}")
    context = "\n\n---\n\n".join(context_blocks)

    return f"""You are a study assistant. Answer the student's question using ONLY the
context excerpts below, which come from their own notes/PDFs. If the context
doesn't contain the answer, say so honestly instead of guessing.

Always cite which file and page number each part of your answer comes from,
in the format (source: filename, p.X).

Context excerpts:
{context}

Question: {question}

Answer:"""


def ask_groq(prompt: str, api_key: str) -> str:
    """Send the prompt to Groq's free-tier LLM API and return the answer text."""
    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1024,
    )
    return completion.choices[0].message.content


def answer_question(store: VectorStore, question: str, api_key: str, k: int = TOP_K):
    """Full RAG call: retrieve relevant chunks, ask Groq, return (answer, chunks_used)."""
    chunks = retrieve(store, question, k=k)
    prompt = build_prompt(question, chunks)
    answer = ask_groq(prompt, api_key)
    return answer, chunks
