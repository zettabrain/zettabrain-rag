# ZettaBrain Reference

Detailed reference for commands, configuration, diagnostics, supported platforms, and uninstallation.

---

## Commands

| Command | Description |
|---------|-------------|
| `sudo zettabrain-setup` | Interactive wizard: storage, model selection, TLS |
| `zettabrain-server` | Launch web GUI (HTTPS on port 7860) |
| `zettabrain-lite` | Alias for `zettabrain-server` |
| `zettabrain-chat` | Terminal chat with your documents |
| `zettabrain-ingest` | Index documents into the vector store |
| `zettabrain-ingest --folder /path` | Index a specific folder |
| `zettabrain-ingest --file /path/doc.pdf` | Index a single file |
| `zettabrain-ingest --stats` | Show vector store contents |
| `zettabrain-ingest --clear` | Wipe the vector store |
| `zettabrain-status` | Show version, certs, storage, and store stats |
| `sudo zettabrain-storage add` | Add a storage source after initial setup |
| `zettabrain-cert` | Regenerate TLS certificates |

### Terminal chat commands

Inside `zettabrain-chat`:

| Command | Action |
|---------|--------|
| *(any question)* | Query your documents |
| `sources` | Show which chunks were retrieved |
| `timing` | Show retrieve/generate times |
| `debug on` / `debug off` | Toggle chunk-level debug output |
| `quit` | Exit |

---

## Configuration

Settings file: `/opt/zettabrain/src/zettabrain.env`

| Variable | Default | Description |
|----------|---------|-------------|
| `ZETTABRAIN_DOCS` | `/opt/zettabrain/data` | Documents folder |
| `ZETTABRAIN_CHROMA` | `/opt/zettabrain/src/zettabrain_vectorstore` | ChromaDB path |
| `ZETTABRAIN_LLM_PROVIDER` | `trial` | LLM provider: `trial`, `ollama`, `claude`, `gemini`, `openai` |
| `ZETTABRAIN_LLM_MODEL` | `phi4-mini` | Ollama model name |
| `ZETTABRAIN_EMBED_MODEL` | `nomic-embed-text` | Embedding model |
| `ZETTABRAIN_CHUNK_SIZE` | `1000` (PDF) / `800` (TXT) | Chunk size in characters |
| `ZETTABRAIN_CHUNK_OVERLAP` | `150` (PDF) / `100` (TXT) | Chunk overlap |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API endpoint |
| `ANTHROPIC_API_KEY` | — | Claude API key |
| `GOOGLE_API_KEY` | — | Gemini API key |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `OPENAI_BASE_URL` | — | Custom OpenAI-compatible endpoint |

### Business identity (for Skills)

These appear in generated documents (quotes, proposals, etc.):

| Variable | Description |
|----------|-------------|
| `org_name` | Your organisation name |
| `org_address` | Address |
| `org_phone` | Phone number |
| `org_email` | Contact email |
| `org_website` | Website URL |
| `org_registration` | Registration or tax ID |

---

## Diagnostics

```bash
# Version, certs, storage, vector store stats
zettabrain-status

# Check Ollama is running
curl http://localhost:11434

# List downloaded models
ollama list

# Stream server logs (Linux)
journalctl -u zettabrain -f

# Stream server logs (macOS)
tail -f /opt/zettabrain/logs/server.log

# Check vector store health
zettabrain-ingest --stats
```

### File locations

| Item | Path |
|------|------|
| Vector database | `/opt/zettabrain/src/zettabrain_vectorstore/` |
| Ingestion log | `/opt/zettabrain/src/ingested_files.json` |
| Configuration | `/opt/zettabrain/src/zettabrain.env` |
| TLS certificates | `/opt/zettabrain/certs/` |
| Server logs (Linux) | `journalctl -u zettabrain` |
| Server logs (macOS) | `/opt/zettabrain/logs/server.log` |
| Skills (user-created) | `/opt/zettabrain/src/skills/` |
| SQLite database | `/opt/zettabrain/src/zettabrain.db` |

---

## Supported Platforms

### Linux

| Distribution | Versions |
|--------------|----------|
| Ubuntu | 20.04, 22.04, 24.04 |
| Debian | 11, 12 |
| Amazon Linux | 2, 2023 |
| RHEL / CentOS Stream | 8, 9 |
| Rocky Linux / AlmaLinux | 8, 9 |
| Fedora | 38+ |
| Linux Mint / Pop!_OS | Current releases |

### macOS

| Version | Architecture |
|---------|--------------|
| 12 Monterey+ | Intel |
| 12 Monterey+ | Apple Silicon (M1/M2/M3) |

GPU acceleration via Metal is automatic on Apple Silicon.

### Windows

| Version | Notes |
|---------|-------|
| Windows 10 / 11 | Via WSL2 (recommended) or PowerShell installer |

---

## Model Reference

### CPU-only

| Model | Size | Speed | Best for |
|-------|------|-------|----------|
| `qwen3:0.6b` | ~500 MB | Instant | Quick lookups, routing |
| `gemma3:1b` | ~815 MB | Very fast | Structured explanations |
| `tinyllama:1.1b` | ~638 MB | Very fast | Basic Q&A |
| `phi4-mini` | ~2.5 GB | Moderate | Best RAG reasoning on CPU |
| `llama3.2:3b` | ~2 GB | Moderate | General purpose |
| `mistral:7b` | ~4 GB | Slow | Strong instruction (12 GB+ RAM) |
| `llama3.1:8b` | ~5 GB | Slow | Balanced quality (16 GB+ RAM) |

### GPU

| Model | VRAM | Speed | Best for |
|-------|------|-------|----------|
| `phi4-mini` | ~2.5 GB | Fast | Best reasoning per GB |
| `mistral:7b` | ~4 GB | Fast | Strong instruction following |
| `openhermes` | ~4 GB | Fast | Formatted RAG responses |
| `llama3.1:8b` | ~5 GB | Fast | Balanced quality |
| `mistral-nemo:12b` | ~7 GB | Moderate | Better reasoning |
| `qwen2.5:14b` | ~9 GB | Moderate | Excellent quality |
| `qwen2.5:32b` | ~20 GB | Slower | Best quality |

### Performance benchmarks

Compliance query against a 10-document financial corpus:

| Model | Hardware | Retrieve | Generate | Total |
|-------|----------|----------|----------|-------|
| `qwen3:0.6b` | CPU | ~1 s | 15-40 s | ~1 min |
| `phi4-mini` | CPU | ~1 s | 120-300 s | 2-5 min |
| `llama3.2:3b` | CPU | ~1 s | 90-180 s | 2-3 min |
| `llama3.1:8b` | CPU | ~1 s | 200-400 s | 4-7 min |
| `mistral:7b` | GPU | ~1 s | 5-12 s | 6-13 s |
| `llama3.1:8b` | GPU | ~1 s | 3-7 s | 4-8 s |
| `qwen2.5:14b` | GPU | ~1 s | 4-10 s | 5-11 s |
| Apple M2/M3 | 16 GB | ~1 s | 10-20 s | 11-21 s |

---

## Storage Backends

### Local

Documents on the same machine. Fastest option.

### NFS

Network File System shares. Configure during `zettabrain-setup` or add later:

```bash
sudo zettabrain-storage add
# Select "NFS share"
# Enter server IP and export path
```

### SMB / CIFS

Windows shares or Samba. Requires credentials:

```bash
sudo zettabrain-storage add
# Select "SMB / CIFS"
# Enter server, share name, username, password
```

### S3-compatible

MinIO, AWS S3, Backblaze B2, or any S3-compatible storage:

```bash
sudo zettabrain-storage add
# Select "Object storage"
# Enter endpoint, bucket, access key, secret key
```

Requires FUSE mount (s3fs, goofys, or mountpoint-s3).

### OneDrive

Connect via the web GUI:

1. Go to Settings > Storage
2. Click "Connect OneDrive"
3. Follow the device code flow
4. Select folders to sync

---

## Uninstall

### Remove the package

```bash
pip uninstall zettabrain-rag
# or
pipx uninstall zettabrain-rag
```

### Stop and remove the service

**Linux (systemd):**

```bash
sudo systemctl stop zettabrain
sudo systemctl disable zettabrain
sudo rm /etc/systemd/system/zettabrain.service
sudo systemctl daemon-reload
```

**macOS (launchd):**

```bash
sudo launchctl unload /Library/LaunchDaemons/io.zettabrain.server.plist
sudo rm /Library/LaunchDaemons/io.zettabrain.server.plist
```

### Remove all data

```bash
sudo rm -rf /opt/zettabrain
```

This deletes configuration, vector store, logs, and certificates.

---

## API Reference

The web server exposes a REST API on port 7860.

### Core endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/status` | Ollama, vector store, storage status |
| `POST` | `/api/chat` | Single-turn RAG query |
| `WS` | `/ws/chat` | Streaming chat via WebSocket |
| `POST` | `/api/ingest` | Trigger document ingestion |
| `DELETE` | `/api/vectorstore` | Clear the vector store |

### Skills endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/skills` | List available skills |
| `GET` | `/api/skills/templates` | List built-in skill templates |
| `POST` | `/api/generate` | Generate a document using a skill |
| `POST` | `/api/skills/draft` | AI-assisted skill creation |
| `POST` | `/api/skills/upload` | Upload a custom skill |
| `DELETE` | `/api/skills/{name}` | Delete a skill |

### Storage endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/storage` | List configured storage sources |
| `POST` | `/api/storage` | Add a storage source |
| `DELETE` | `/api/storage/{index}` | Remove a storage source |
| `POST` | `/api/onedrive/connect` | Start OneDrive device flow |
| `POST` | `/api/onedrive/sync` | Sync files from OneDrive |

### Export endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/export/{id}/pdf` | Export generated document as PDF |
| `GET` | `/api/export/{id}/docx` | Export generated document as DOCX |
