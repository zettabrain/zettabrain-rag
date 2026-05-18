# ZettaBrain RAG

**Private AI document assistant — your documents, your hardware, zero cloud.**

Chat with your documents using a fully local AI. No API keys. No data leaving your machine. Runs on your own server or laptop with a secure HTTPS web GUI. Supports local disk, NFS, SMB and object storage.

---

## Quick Install

```bash
curl -fsSL https://zettabrain.app/install.sh | sudo bash
```

Alternative mirror:

```bash
curl -fsSL https://install.zettabrain.io | sudo bash
```

What the installer does:
- Detects your OS (Ubuntu, Debian, Amazon Linux, RHEL, Fedora)
- Installs Python 3.9+ and system dependencies
- Installs `zettabrain-rag` via **pipx** (isolated, no virtualenv management needed)
- Installs and starts Ollama
- Pulls the `nomic-embed-text` embedding model (~275 MB)

---

## Install via pipx (developers)

```bash
# Install pipx if you don't have it
apt install -y pipx          # Ubuntu / Debian
brew install pipx            # macOS

# Install ZettaBrain
pipx install zettabrain-rag

# Verify
zettabrain --version
```

---

## First-time setup

### 1. Run setup wizard

```bash
sudo zettabrain-setup
```

Configures storage (Local / NFS / SMB), selects an LLM model based on your hardware, and enables HTTPS.

### 2. Launch the web GUI

```bash
zettabrain-server
```

Open **https://local.zettabrain.app:7860** in your browser — trusted HTTPS, fully private.

### 3. Or use the CLI chat

```bash
zettabrain-chat
```

---

## Commands

| Command | Description |
|---|---|
| `sudo zettabrain-setup` | Storage wizard + model selection + TLS cert |
| `zettabrain-server` | Launch secure HTTPS web GUI (port 7860) |
| `zettabrain-chat` | Interactive RAG chat in the terminal |
| `zettabrain-chat --rebuild` | Rebuild vector store then start chat |
| `zettabrain-chat --debug` | Show retrieved chunks on every query |
| `zettabrain-ingest` | Ingest documents into the vector store |
| `zettabrain-ingest --folder /path` | Ingest a specific folder |
| `zettabrain-ingest --file /path/doc.pdf` | Ingest a single file |
| `zettabrain-ingest --stats` | Show what is in the vector store |
| `zettabrain-ingest --clear` | Wipe the vector store |
| `zettabrain-status` | Show install paths, cert info, and store statistics |
| `sudo zettabrain-storage add` | Add a new storage source after initial setup |
| `zettabrain-storage list` | List configured storage sources |

### CLI chat commands

While inside `zettabrain-chat`:

| Type | Action |
|---|---|
| Any question | Query your documents |
| `sources` | Show which document chunks were used |
| `timing` | Show retrieve / generate time for all queries this session |
| `debug on` | Show retrieved chunks on every query |
| `debug off` | Hide debug output |
| `quit` | Exit |

---

## System requirements

| | Minimum | Recommended |
|---|---|---|
| **RAM** | 8 GB | 16 GB |
| **CPU** | 4 cores / 2.5 GHz | 8 cores / 3.0 GHz |
| **Disk** | 20 GB free | 50 GB free |
| **OS** | Ubuntu 22.04 / Debian 12 | Ubuntu 22.04 LTS |
| **Python** | 3.9 | 3.11+ |

> **Why 8 GB minimum:** `llama3.1:8b` (Q4) needs ~5 GB in RAM, plus ~2 GB for OS + Python + ChromaDB. Below 8 GB you will hit swap and responses can take 5+ minutes.

---

## GPU & model selection

Ollama **auto-detects your GPU** on install — NVIDIA (CUDA), AMD (ROCm), and Apple Silicon (Metal). No configuration needed beyond having the correct drivers installed.

`sudo zettabrain-setup` detects your hardware and presents a model menu:

```
Hardware detected: NVIDIA GeForce RTX 3080 (10GB VRAM)
Recommended model: llama3.1:8b  (10GB VRAM detected: balanced quality/speed)

  Available models:
    1) llama3.2:3b    — fastest (~2GB)        good for quick Q&A
    2) llama3.1:8b    — balanced (~5GB)       recommended for most   ← default
    3) mistral:7b     — fast (~4GB)           strong reasoning
    4) mistral-nemo:12b — better (~7GB)        needs 12GB+ VRAM/RAM
    5) qwen2.5:14b    — excellent (~9GB)      needs 16GB+ VRAM/RAM
    6) qwen2.5:32b    — best quality (~20GB)  needs 24GB+ VRAM/RAM
    7) Custom
```

You can also switch model at any time by editing `/opt/zettabrain/src/zettabrain.env`:

```bash
ZETTABRAIN_LLM_MODEL=qwen2.5:14b
```

Then restart the server: `zettabrain-server`

### Performance reference

Timings for a real compliance query against a 10-document financial services corpus:

> **"What is the pre-clearance process for personal securities trades and how long does approval last?"**

| Hardware | Model | Retrieve | Generate | Total |
|---|---|---|---|---|
| 4-core CPU, 8 GB RAM | llama3.2:3b | ~1 s | 90–180 s | ~2–3 min |
| 8-core CPU, 16 GB RAM | llama3.1:8b | ~1 s | 120–300 s | ~2–5 min |
| EC2 m5.2xlarge (8 vCPU, 32 GB) ✱ | qwen2.5:14b | **0.9 s** | **378 s** | ~6.5 min |
| NVIDIA RTX 3060 (8 GB) | llama3.1:8b | ~1 s | 5–10 s | ~6–11 s |
| NVIDIA RTX 3080 (10 GB) | llama3.1:8b | ~1 s | 3–7 s | ~4–8 s |
| Apple M2 (16 GB) | llama3.1:8b | ~1 s | 10–20 s | ~11–21 s |

✱ *Measured result — EC2 m5.2xlarge, CPU only, 10-doc financial corpus, 5 chunks retrieved.*

**Retrieve** covers: query embedding + ChromaDB MMR search + BM25 keyword search + FlashRank re-ranking.  
**Generate** depends on model size and hardware. A GPU reduces generate time by 30–60×.

The web UI shows per-query timing after every response: `⚡ 938ms retrieve · 🤖 378s generate`.

---

## Retrieval pipeline

ZettaBrain uses a hybrid retrieval approach for accuracy:

1. **Adaptive chunking** — chunk size tuned per document type (PDF / DOCX / TXT) and text density
2. **MMR semantic search** — Maximum Marginal Relevance via ChromaDB (diversity + relevance)
3. **BM25 keyword search** — exact term matching on the same corpus
4. **Merge & deduplicate** — semantic results ranked first, duplicates removed by content hash
5. **Cross-encoder re-ranking** — FlashRank (`ms-marco-MiniLM-L-12-v2`) picks the best chunks before sending to the LLM

---

## Supported document formats

`.pdf`  `.txt`  `.md`  `.docx`

---

## Sample Test Data

Not ready to use your own documents yet? Download ready-made test datasets to evaluate ZettaBrain against realistic enterprise content.

### Available datasets

| Industry | Documents | Organisation (fictional) |
|---|---|---|
| **Financial Services** | 10 DOCX files | Apex Financial Group — trading policy, AML/KYC procedures, insider trading, risk framework, employee handbook |
| **Healthcare** | 10 DOCX files | Riverside Medical Center — HIPAA privacy & security, medication protocols, emergency response codes, clinical documentation |

### Download

| File | Size | Link |
|---|---|---|
| Financial Services documents | ~90 KB | [zettabrain-financial-test-docs.zip](https://zettabrain.io/sample-data/zettabrain-financial-test-docs.zip) |
| Healthcare documents | ~91 KB | [zettabrain-healthcare-test-docs.zip](https://zettabrain.io/sample-data/zettabrain-healthcare-test-docs.zip) |
| Test prompts guide (40 prompts) | ~7 KB | [RAG_Test_Prompts_Guide.md](https://zettabrain.io/sample-data/RAG_Test_Prompts_Guide.md) |

The prompts guide includes 20 industry-specific prompts per dataset, cross-document summary prompts, and adversarial prompts that verify ZettaBrain correctly declines to answer questions not present in the documents.

### Quick start with sample data

```bash
# Download and unzip the financial services dataset
curl -LO https://zettabrain.io/sample-data/zettabrain-financial-test-docs.zip
unzip zettabrain-financial-test-docs.zip -d ~/zettabrain-test

# Point ZettaBrain at the folder and ingest
zettabrain-ingest --folder ~/zettabrain-test/financial

# Start chatting
zettabrain-chat
```

Open the web GUI at `https://local.zettabrain.app:7860` and paste prompts from the guide directly into the chat.

### Example result (financial services, EC2 m5.2xlarge, CPU only)

**Prompt:** *What is the pre-clearance process for personal securities trades and how long does approval last?*

**Answer (qwen2.5:14b):**
> The pre-clearance process involves submitting a request through the ComplianceTrack portal at least 24 hours before the intended trade. Approval is valid for 48 hours from the time of approval.
> [01_Employee_Investment_Trading_Policy.docx]

**Sources cited:** `01_Employee_Investment_Trading_Policy.docx` · `08_Insider_Trading_Policy.docx` · `10_New_Employee_Onboarding.docx`  
**Timing:** ⚡ 938 ms retrieve · 🤖 378 s generate (CPU only — GPU reduces generate to ~5–10 s)

---

## Configuration

All settings can be overridden via environment variables or `/opt/zettabrain/src/zettabrain.env`:

| Variable | Default | Description |
|---|---|---|
| `ZETTABRAIN_DOCS` | `/opt/zettabrain/data` | Documents folder |
| `ZETTABRAIN_CHROMA` | `/opt/zettabrain/src/zettabrain_vectorstore` | ChromaDB path |
| `ZETTABRAIN_LLM_MODEL` | `llama3.1:8b` | Ollama LLM model |
| `ZETTABRAIN_EMBED_MODEL` | `nomic-embed-text` | Ollama embedding model |
| `ZETTABRAIN_CHUNK_SIZE` | `1000` (PDF) / `800` (TXT) | Chunk size (adaptive) |
| `ZETTABRAIN_CHUNK_OVERLAP` | `150` (PDF) / `100` (TXT) | Chunk overlap (adaptive) |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API endpoint |

---

## Diagnostics

```bash
# Full status — version, certs, vector store stats
zettabrain-status

# Verify ChromaDB is working
python3 /opt/zettabrain/src/01_chromadb_setup.py

# Verify embedding model is working
python3 /opt/zettabrain/src/02_embeddings_test.py

# Check Ollama is running
curl http://localhost:11434

# List downloaded models
ollama list

# View server logs
journalctl -u zettabrain -f
```

---

## Uninstall

### pipx install
```bash
pipx uninstall zettabrain-rag
sudo rm -rf /opt/zettabrain
```

### One-line installer
```bash
pipx uninstall zettabrain-rag
sudo rm -rf /opt/zettabrain /var/log/zettabrain-install.log
sudo systemctl disable --now zettabrain 2>/dev/null || true
```

---

## Contributors

| | |
|---|---|
| **[@zettabrain](https://github.com/zettabrain)** | Creator & maintainer |

---

## License

MIT — © ZettaBrain
