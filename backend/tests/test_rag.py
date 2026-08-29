import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.rag.chunker import chunk_code
from app.rag.embedder import embed_texts, embed_query
from app.services.rag_service import make_title_from_question


def test_chunk_python_functions_split_by_boundary():
    code = (
        "import os\n\n"
        "def foo():\n    return 1\n\n"
        "def bar():\n    return 2\n"
    )
    chunks = chunk_code(code, "python")
    assert len(chunks) >= 2
    assert any("def foo" in c["text"] for c in chunks)
    assert any("def bar" in c["text"] for c in chunks)
    # line ranges should be valid and increasing
    for c in chunks:
        assert c["start_line"] <= c["end_line"]


def test_chunk_fallback_for_unknown_language():
    code = "\n".join([f"line {i}" for i in range(100)])
    chunks = chunk_code(code, "text")
    assert len(chunks) > 1
    assert chunks[0]["start_line"] == 1


def test_chunk_empty_file_returns_no_chunks():
    assert chunk_code("", "python") == []


def test_embeddings_are_normalized_and_consistent_dimension():
    vectors = embed_texts(["def foo(): pass", "class Bar: pass"])
    assert vectors.shape[0] == 2
    for v in vectors:
        norm = (v ** 2).sum() ** 0.5
        assert abs(norm - 1.0) < 1e-3 or norm == 0

    q = embed_query("what does foo do")
    assert q.shape[0] == vectors.shape[1]


def test_title_generation_is_local_and_deterministic():
    title = make_title_from_question("How does authentication work in this app?")
    assert title == "How does authentication work in this"
    assert len(title) <= 60
