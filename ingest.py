"""
ingest.py - Index documents from the (mock) ECM REST API into Chroma.

This calls REST endpoints shaped like a generic ECM content API, so later you
can point the base URL at a real ECM Content Server and reuse this file.

Run AFTER the app is up:   python ingest.py
(Or run standalone - it reads files directly if the API isn't running.)
"""

import json
from pathlib import Path

import chromadb

BASE_DIR = Path(__file__).parent
DOCS_DIR = BASE_DIR / "sample_docs"
REPO = json.loads((BASE_DIR / "mock_repository.json").read_text(encoding="utf-8"))

CHUNK_SIZE = 1200      # characters per chunk
CHUNK_OVERLAP = 200    # characters of overlap between consecutive chunks


def chunk_text(text: str) -> list[str]:
    """Simple sliding-window chunker. Dumb but debuggable."""
    chunks, start = [], 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start = end - CHUNK_OVERLAP
        if end >= len(text):
            break
    return chunks


def main():
    chroma = chromadb.PersistentClient(path=str(BASE_DIR / "chroma_db"))
    # Fresh index each run (fine at POC scale)
    try:
        chroma.delete_collection("ecm_chunks")
    except Exception:
        pass
    collection = chroma.create_collection("ecm_chunks")
    # NOTE: Chroma uses a FREE local embedding model (all-MiniLM, ONNX) by
    # default. First run downloads ~80 MB once. No embedding API key needed.

    ids, texts, metas = [], [], []
    for doc in REPO["documents"]:
        path = DOCS_DIR / doc["object_name"]
        content = path.read_text(encoding="utf-8")
        for i, chunk in enumerate(chunk_text(content)):
            ids.append(f"{doc['r_object_id']}_{i}")
            texts.append(chunk)
            metas.append({
                "r_object_id": doc["r_object_id"],
                "object_name": doc["object_name"],
                "acl_name": doc["acl_name"],
                "chunk_no": i,
            })
        print(f"Indexed {doc['object_name']}  (acl={doc['acl_name']})")

    collection.add(ids=ids, documents=texts, metadatas=metas)
    print(f"\nDone. {len(ids)} chunks stored in ./chroma_db")
    print("First run downloads the local embedding model - one-time only.")


if __name__ == "__main__":
    main()
