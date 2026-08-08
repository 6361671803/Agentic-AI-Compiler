"""RAG over curated Python reference material, past fixes, and user uploads.

Uses Chroma's local persistent client with its bundled default embedding
function, so no external API key or network call is needed for embedding.

This app's own source code is deliberately NOT indexed here anymore. An
earlier version did that, and a small local model sometimes parroted
irrelevant chunks of this project's internals back as the "corrected code"
for whatever the user pasted in - a real, reproduced bug. Everything indexed
here is instead actually about fixing arbitrary Python code: exception
reference docs, a style guide, and a running memory of code you've
previously submitted plus how it was fixed.
"""
import hashlib
import os
import time

import chromadb

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STORE_DIR = os.path.join(PROJECT_ROOT, ".rag_store")
KNOWLEDGE_DIR = os.path.join(PROJECT_ROOT, "knowledge")
MAX_CONTEXT_CHUNKS = 3
MAX_CONTEXT_CHARS = 1200

_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=STORE_DIR)
        _collection = _client.get_or_create_collection("ai_compiler_context")
    return _collection


def _chunk_markdown(text, file_label):
    """Split a markdown file into its "## heading" sections."""
    sections = text.split("\n## ")
    chunks = []
    for i, section in enumerate(sections):
        if i > 0:
            section = "## " + section
        title = section.strip().splitlines()[0].lstrip("#").strip() if section.strip() else f"part{i}"
        chunks.append((f"{file_label}::{title}", section))
    return chunks


def _upsert_chunks(collection, source_tag, chunks):
    if not chunks:
        return
    ids, docs, metadatas = [], [], []
    for label, text in chunks:
        if not text.strip():
            continue
        chunk_id = hashlib.sha1(f"{source_tag}:{label}".encode("utf-8")).hexdigest()
        ids.append(chunk_id)
        docs.append(text)
        metadatas.append({"source": source_tag, "label": label})
    if ids:
        collection.upsert(ids=ids, documents=docs, metadatas=metadatas)


def index_knowledge(force=False):
    """Index the curated Python reference docs in knowledge/ (exceptions, style guide, ...).

    Skipped on repeat calls unless force=True, since re-embedding unchanged
    files on every Streamlit rerun would waste local compute for no benefit.
    """
    collection = _get_collection()
    if not force and collection.count() > 0:
        existing = collection.get(where={"source": "knowledge"}, limit=1)
        if existing["ids"]:
            return collection.count()

    if not os.path.isdir(KNOWLEDGE_DIR):
        return collection.count()

    for fname in os.listdir(KNOWLEDGE_DIR):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(KNOWLEDGE_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            text = f.read()
        chunks = _chunk_markdown(text, fname)
        _upsert_chunks(collection, "knowledge", chunks)

    return collection.count()


def index_upload(filename, content):
    """Index a user-uploaded reference file (docs, snippets) into the same store."""
    collection = _get_collection()
    chunk_size = 800
    chunks = [
        (f"{filename}#{i}", content[i:i + chunk_size])
        for i in range(0, len(content), chunk_size)
    ]
    _upsert_chunks(collection, f"upload:{filename}", chunks)
    return len(chunks)


def remember_fix(original_code, corrected_code, summary=""):
    """Store a code -> fix pair so future similar submissions can be grounded in it.

    Keyed by a hash of the original code: resubmitting the same snippet
    updates its remembered fix instead of piling up duplicates, while
    genuinely different code accumulates as new entries over time.
    """
    collection = _get_collection()
    key = hashlib.sha1(original_code.encode("utf-8")).hexdigest()[:12]
    doc = (
        f"Original code:\n{original_code}\n\n"
        f"Corrected code:\n{corrected_code}\n\n"
        f"Summary of the fix: {summary}" if summary else
        f"Original code:\n{original_code}\n\nCorrected code:\n{corrected_code}"
    )
    collection.upsert(
        ids=[f"fix-{key}"],
        documents=[doc],
        metadatas=[{"source": "past_fix", "label": f"past fix #{key}", "ts": time.time()}],
    )


def retrieve(query, k=MAX_CONTEXT_CHUNKS, max_chars=MAX_CONTEXT_CHARS):
    """Return a token-budget-capped context string plus the source labels used."""
    collection = _get_collection()
    if collection.count() == 0:
        return "", []

    results = collection.query(query_texts=[query], n_results=min(k, collection.count()))
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    pieces, sources, used = [], [], 0
    for doc, meta in zip(docs, metas):
        label = meta.get("label", meta.get("source", "unknown"))
        snippet = doc if len(doc) <= max_chars else doc[:max_chars] + "..."
        if used + len(snippet) > max_chars and pieces:
            break
        pieces.append(f"# {label}\n{snippet}")
        sources.append(label)
        used += len(snippet)

    return "\n\n".join(pieces), sources
