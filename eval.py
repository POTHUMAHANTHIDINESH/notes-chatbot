"""
eval.py — measure how well the RAG pipeline actually works.

Two things get measured, separately:
  1. RETRIEVAL accuracy: for each test question, did the correct source
     file/page show up in the top-3 retrieved chunks?
  2. ANSWER accuracy: for each test question, does the LLM's final answer
     actually contain the key fact(s) we expect?

These are different failure modes:
  - Retrieval can succeed but the LLM still gives a bad answer (hallucination,
    ignoring context, etc.)
  - Retrieval can fail, in which case the answer is doomed regardless of how
    good the LLM is.
Measuring both tells you WHERE a problem lives if the chatbot is wrong.

HOW TO USE:
  1. Make sure you've already built your index once in the Streamlit app
     (so vectorstore/index.faiss and vectorstore/meta.pkl exist).
  2. Fill in TEST_CASES below with questions about YOUR OWN notes — pick
     things you already know the answer to and which file/page they're on.
  3. Set your Groq key: either `set GROQ_API_KEY=your_key` in this terminal,
     or paste it directly into GROQ_API_KEY_FALLBACK below (don't commit that).
  4. Run:  python eval.py
"""

import os

from rag_engine import VectorStore, retrieve, answer_question

GROQ_API_KEY_FALLBACK = ""  # optional: paste key here for a quick local run (don't commit it)

# ---------------------------------------------------------------------------
# EDIT THIS: replace with real questions about YOUR notes.
# - expected_source: the PDF filename (must match exactly, e.g. "networks_ch4.pdf")
# - expected_page: the page number you know the answer is on
# - expected_keywords: 1-3 words/phrases that MUST appear in a correct answer
# ---------------------------------------------------------------------------
TEST_CASES = [
    {
        "question": "What is TCP congestion control?",
        "expected_source": "networks_ch4.pdf",
        "expected_page": 12,
        "expected_keywords": ["congestion", "window"],
    },
    {
        "question": "What is the difference between supervised and unsupervised learning?",
        "expected_source": "ml_intro.pdf",
        "expected_page": 3,
        "expected_keywords": ["labeled", "unlabeled"],
    },
    # Add 6-8 more of your own below, same format.
]


def check_retrieval(store, case, k=3):
    results = retrieve(store, case["question"], k=k)
    hit = any(
        r.source == case["expected_source"] and r.page == case["expected_page"]
        for r in results
    )
    return hit, results


def check_answer(answer_text, case):
    text_lower = answer_text.lower()
    return all(kw.lower() in text_lower for kw in case["expected_keywords"])


def main():
    api_key = os.environ.get("GROQ_API_KEY", "") or GROQ_API_KEY_FALLBACK
    if not api_key:
        print("ERROR: set GROQ_API_KEY (env var) or fill GROQ_API_KEY_FALLBACK in this file.")
        return

    store = VectorStore.load()
    if store is None:
        print("ERROR: no index found. Build one first in the Streamlit app "
              "(upload PDFs -> 'Build / rebuild index'), then re-run this script.")
        return

    retrieval_hits = 0
    answer_hits = 0
    print(f"Running {len(TEST_CASES)} test questions...\n")

    for i, case in enumerate(TEST_CASES, start=1):
        r_hit, results = check_retrieval(store, case)
        retrieval_hits += int(r_hit)

        answer_text, _ = answer_question(store, case["question"], api_key)
        a_hit = check_answer(answer_text, case)
        answer_hits += int(a_hit)

        print(f"[{i}] {case['question']}")
        print(f"    Retrieval: {'PASS' if r_hit else 'FAIL'} "
              f"(expected {case['expected_source']} p.{case['expected_page']}; "
              f"got {[(r.source, r.page) for r in results]})")
        print(f"    Answer:    {'PASS' if a_hit else 'FAIL'} "
              f"(expected keywords {case['expected_keywords']})")
        print()

    n = len(TEST_CASES)
    print("=" * 50)
    print(f"Retrieval accuracy: {retrieval_hits}/{n} ({100*retrieval_hits/n:.0f}%)")
    print(f"Answer accuracy:    {answer_hits}/{n} ({100*answer_hits/n:.0f}%)")
    print("=" * 50)


if __name__ == "__main__":
    main()
