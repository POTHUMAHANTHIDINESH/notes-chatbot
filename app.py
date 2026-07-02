"""
Personal Notes Chatbot — Streamlit app.

Upload your own PDFs (lecture notes, textbooks, slides), build a local
search index, then ask questions and get answers grounded in YOUR notes,
with citations back to the file + page number.

Run locally:   streamlit run app.py
"""

import os
import tempfile

import streamlit as st

from rag_engine import VectorStore, build_index, answer_question

st.set_page_config(page_title="Notes Chatbot", page_icon="📚", layout="wide")

# ---------- Session state ----------
if "store" not in st.session_state:
    st.session_state.store = VectorStore.load()  # try to load a previously built index
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------- Sidebar ----------
with st.sidebar:
    st.title("📚 Notes Chatbot")
    st.caption("Ask questions about your own PDFs, with citations.")

    api_key = st.text_input(
        "Groq API key",
        type="password",
        value=os.environ.get("GROQ_API_KEY", ""),
        help="Free, no credit card. Get one at console.groq.com/keys",
    )

    st.divider()
    st.subheader("1. Upload your notes")
    uploaded_files = st.file_uploader(
        "PDFs (lecture notes, slides, textbooks...)",
        type=["pdf"],
        accept_multiple_files=True,
    )

    if st.button("Build / rebuild index", type="primary", disabled=not uploaded_files):
        with tempfile.TemporaryDirectory() as tmp_dir:
            saved_paths = []
            for f in uploaded_files:
                path = os.path.join(tmp_dir, f.name)
                with open(path, "wb") as out:
                    out.write(f.getbuffer())
                saved_paths.append(path)

            progress = st.progress(0.0, text="Starting...")

            def on_progress(done, total, filename):
                progress.progress(done / total, text=f"Processing {filename} ({done}/{total})")

            with st.spinner("Reading PDFs and building your search index..."):
                st.session_state.store = build_index(saved_paths, progress_callback=on_progress)
            progress.empty()
            st.success(f"Index built from {len(saved_paths)} file(s). Ask away!")

    if st.session_state.store is not None:
        n_chunks = len(st.session_state.store.chunks)
        n_files = len(set(c.source for c in st.session_state.store.chunks))
        st.info(f"Index ready: {n_files} file(s), {n_chunks} chunks.")

    st.divider()
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()

# ---------- Main chat ----------
st.header("Ask your notes")

if st.session_state.store is None:
    st.warning("Upload PDFs and click **Build / rebuild index** in the sidebar to get started.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("Sources"):
                for s in msg["sources"]:
                    st.markdown(f"**{s.source}**, page {s.page}")
                    st.caption(s.text[:300] + ("..." if len(s.text) > 300 else ""))

question = st.chat_input("e.g. Explain TCP congestion control from my Computer Networks notes")

if question:
    if st.session_state.store is None:
        st.error("Build an index first (upload PDFs in the sidebar).")
    elif not api_key:
        st.error("Enter your free Groq API key in the sidebar first.")
    else:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Searching your notes..."):
                try:
                    answer, chunks = answer_question(st.session_state.store, question, api_key)
                except Exception as e:
                    answer = f"Something went wrong calling Groq: {e}"
                    chunks = []
            st.markdown(answer)
            if chunks:
                with st.expander("Sources"):
                    for s in chunks:
                        st.markdown(f"**{s.source}**, page {s.page}")
                        st.caption(s.text[:300] + ("..." if len(s.text) > 300 else ""))

        st.session_state.messages.append({"role": "assistant", "content": answer, "sources": chunks})
