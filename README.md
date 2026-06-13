# ECM AI Search POC

> **Disclaimer:** This is an independent, educational proof-of-concept. It is **not**
> affiliated with, endorsed by, or sponsored by OpenText Corporation or any other
> vendor. "Documentum" and "D2 SmartView" are trademarks of OpenText and are referenced
> in this README only descriptively (nominative fair use), to indicate the *type* of
> enterprise content management (ECM) system this project simulates. This repository
> contains **no proprietary code, schemas, logos, or materials** from any vendor. The
> mock REST API, sample documents, metadata, and UI were all written from scratch and
> are entirely fictional.

An AI-powered document search assistant for **enterprise content management (ECM)**
systems, demonstrated end-to-end on a laptop. It mocks an ECM repository with a REST
API and a web-client UI, then layers a Claude-powered chatbot that answers questions
about the documents — with citations and permission (ACL) awareness.

No real ECM server, no Docker, no database install required. The only paid dependency
is the Claude API (~$0.008 per question with Claude Haiku 4.5). Embeddings run locally
and free.

## Why it's interesting
- **Retrieval-Augmented Generation (RAG)** over an enterprise repository.
- **Permission-aware:** users only get answers from documents their ACLs allow.
- **Cited answers:** every response links back to the source document.
- **Context-aware:** open a document and ask "summarize this".
- **Vendor-neutral by design:** the REST shape and metadata model mirror common ECM
  systems, so the ingestion code can later target a real ECM (e.g. a Documentum-style
  REST API) by changing only the base URL and adding authentication.

## What's Inside
| File/Folder | What it is |
|---|---|
| `sample_docs/` | 8 fictional enterprise docs (SOPs, contracts, policies) |
| `mock_repository.json` | Fictional ECM metadata: object IDs, ACLs, 3 test users |
| `app.py` | Mock ECM REST API + RAG `/ask` endpoint + UI server |
| `ingest.py` | Chunks docs + embeds into Chroma (FREE local embeddings) |
| `static/ecm_client.html` | Mock ECM web-client UI (browser, viewer, chat panel) |
| `static/widget.html` | The AI chat widget (iframe-embedded, like a real ECM widget) |

## Setup — 6 Steps (~20 minutes)

### Step 1 — Install Python
Download Python 3.12 from https://www.python.org/downloads/windows/
**IMPORTANT:** tick the box "Add python.exe to PATH" during install.
Verify in PowerShell: `python --version`

### Step 2 — Get the project
Clone the repository, then enter the folder:
```powershell
git clone https://github.com/viraajbhapse-afk/ecm-ai-search-poc.git
cd ecm-ai-search-poc
```
(No Git? Click the green **Code** button on GitHub -> **Download ZIP**, unzip, then `cd` into the folder.)

### Step 3 — Create environment & install packages
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
(If activation is blocked: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then retry.)

### Step 4 — Add your Claude API key
1. Get a key at https://console.anthropic.com (add ~$5 credit — plenty).
2. Copy `.env.example` to `.env`:
   ```powershell
   copy .env.example .env
   notepad .env
   ```
3. Paste your key after `ANTHROPIC_API_KEY=` and save.
   In Notepad's Save dialog set "Save as type" to **All Files** so it saves as `.env`, not `.env.txt`.

> Prefer to keep the key outside the project folder? See **Keeping your key outside
> the project** below.

### Step 5 — Index the documents (one time)
```powershell
python ingest.py
```
First run downloads a small free embedding model (~80 MB). You should see
"Done. N chunks stored".

### Step 6 — Run it
```powershell
uvicorn app:app --port 8000
```
Open **http://localhost:8000** in your browser.

## The 5-Minute Demo Script
1. **Login as `viraaj`** (top-right dropdown) — ask: *"What is the RMAN backup schedule?"* → cited answer; click the source → the document opens in the viewer.
2. **Ask:** *"Which contracts expire in 2027 and what notice is needed?"* → it reasons across the MSA.
3. **Open the NDA**, then ask *"Summarize this document"* → context-aware answer about the open doc.
4. **The security moment:** switch user to `guest` → contracts disappear from the list → ask the same contract question → *"I could not find this in the documents you have access to."* Same AI, permission-aware.
5. Close: "This widget pattern drops into a real ECM web client; this ingest script points at a real ECM REST API. Total AI cost today: under 1 dirham."

## How This Maps to a Real ECM Later
- `ingest.py` calls REST endpoints shaped like a generic ECM content API → change the base URL + add auth.
- `mock_repository.json` users/ACLs → replaced by the live ECM session + real ACL values.
- `static/widget.html` → registered as an external/iframe widget in the ECM web client's config.

## Keeping your key outside the project
Instead of a `.env` in the project, set a Windows user environment variable:
```powershell
setx ANTHROPIC_API_KEY "sk-ant-your-key"
setx CLAUDE_MODEL "claude-haiku-4-5"
```
Close and reopen PowerShell (setx only affects new windows), delete the project `.env`,
and run as normal — `Anthropic()` reads the key straight from the environment.

## Troubleshooting
- **`'python' is not recognized`** → reinstall Python with "Add to PATH" ticked.
- **Widget says API key error** → check `.env` exists (not `.env.txt`) and restart uvicorn (it reads the key only at startup).
- **`ingest.py` slow first time** → it's downloading the embedding model once. Normal.
- **Port busy** → `uvicorn app:app --port 8010` and open localhost:8010.

## Tech Stack
Python · FastAPI · Chroma (local vector DB + free local embeddings) · Anthropic Claude API.

## License
MIT — see [LICENSE](LICENSE).
