"""
app.py - ECM AI Search POC (all-in-one, runs on a Windows 11 laptop)

Serves:
  1. Mock ECM REST API          ->  /ecm-rest/...    (mimics a generic ECM content API)
  2. RAG chatbot API            ->  POST /ask        (Chroma retrieval + Claude Haiku 4.5)
  3. Mock ECM Web Client UI     ->  /                (document browser + embedded chat widget)
  4. Chat widget page           ->  /widget          (the iframe panel, like an ECM web widget)

Run:  uvicorn app:app --reload --port 8000
Then open http://localhost:8000
"""

import json
import os
from pathlib import Path

import chromadb
from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel

import os
load_dotenv(os.path.expanduser(r"~\.secrets\ecm-ai.env"))

BASE_DIR = Path(__file__).parent
DOCS_DIR = BASE_DIR / "sample_docs"
REPO = json.loads((BASE_DIR / "mock_repository.json").read_text(encoding="utf-8"))
DOC_BY_ID = {d["r_object_id"]: d for d in REPO["documents"]}

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5")
claude = Anthropic()  # reads ANTHROPIC_API_KEY from environment / .env

chroma = chromadb.PersistentClient(path=str(BASE_DIR / "chroma_db"))
collection = chroma.get_or_create_collection("ecm_chunks")

app = FastAPI(title="ECM AI Search POC")

# ----------------------------------------------------------------------
# 1. MOCK ECM REST API
#    Generic content-API shape, so ingest.py can later be pointed at a
#    real ECM Content Server by changing only the base URL + auth.
# ----------------------------------------------------------------------

@app.get("/ecm-rest/repositories")
def list_repositories():
    return {"entries": [{"title": REPO["repository"]}]}


@app.get("/ecm-rest/repositories/MOCKDOCBASE/dql")
def run_dql(dql: str = ""):
    """Very small DQL simulator: returns all docs in the pilot cabinet."""
    entries = [
        {"content": {"properties": {
            "r_object_id": d["r_object_id"],
            "object_name": d["object_name"],
            "acl_name": d["acl_name"],
            "r_version_label": d["r_version_label"],
        }}}
        for d in REPO["documents"]
    ]
    return {"dql": dql, "entries": entries}


@app.get("/ecm-rest/repositories/MOCKDOCBASE/objects/{object_id}/content-media")
def get_content(object_id: str):
    doc = DOC_BY_ID.get(object_id)
    if not doc:
        raise HTTPException(404, "Object not found")
    return PlainTextResponse((DOCS_DIR / doc["object_name"]).read_text(encoding="utf-8"))


# ----------------------------------------------------------------------
# 2. RAG CHATBOT API
# ----------------------------------------------------------------------

class AskRequest(BaseModel):
    question: str
    user: str = "viraaj"
    context_object_id: str | None = None  # set when a doc is open in the web client


SYSTEM_PROMPT = (
    "You are an enterprise document assistant for an ECM repository. "
    "Answer ONLY using the provided document excerpts. For every claim, cite the "
    "source as [object_name]. If the excerpts do not contain the answer, reply "
    "exactly: 'I could not find this in the documents you have access to.' "
    "Never invent documents or facts. Be concise."
)


@app.post("/ask")
def ask(req: AskRequest):
    user_acls = REPO["users"].get(req.user)
    if not user_acls:
        raise HTTPException(403, f"Unknown user '{req.user}'")

    # --- Retrieval (permission-aware) ---
    where = {"acl_name": {"$in": user_acls}}
    if req.context_object_id:  # "summarize this doc" mode
        doc = DOC_BY_ID.get(req.context_object_id)
        if doc and doc["acl_name"] in user_acls:
            where = {"r_object_id": req.context_object_id}

    results = collection.query(query_texts=[req.question], n_results=6, where=where)

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    if not docs:
        return {"answer": "I could not find this in the documents you have access to.",
                "sources": []}

    context = "\n\n---\n\n".join(
        f"[{m['object_name']}] (id={m['r_object_id']})\n{t}"
        for t, m in zip(docs, metas)
    )

    # --- Generation (Claude Haiku 4.5) ---
    msg = claude.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Document excerpts:\n\n{context}\n\nQuestion: {req.question}",
        }],
    )
    answer = "".join(b.text for b in msg.content if b.type == "text")

    seen, sources = set(), []
    for m in metas:
        if m["r_object_id"] not in seen:
            seen.add(m["r_object_id"])
            sources.append({"object_name": m["object_name"],
                            "r_object_id": m["r_object_id"]})

    return {"answer": answer, "sources": sources, "model": CLAUDE_MODEL}


# ----------------------------------------------------------------------
# 3. UI ROUTES (mock ECM web client + chat widget) + helpers for the frontend
# ----------------------------------------------------------------------

@app.get("/")
def ecm_client():
    return FileResponse(BASE_DIR / "static" / "ecm_client.html")


@app.get("/widget")
def widget():
    return FileResponse(BASE_DIR / "static" / "widget.html")


@app.get("/api/documents")
def ui_documents(user: str = "viraaj"):
    """Document list filtered by the selected user's ACLs (like real ECM web-client browsing)."""
    user_acls = REPO["users"].get(user, [])
    return JSONResponse([d for d in REPO["documents"] if d["acl_name"] in user_acls])


@app.get("/api/users")
def ui_users():
    return JSONResponse(list(REPO["users"].keys()))
