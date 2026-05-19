#!/usr/bin/env bash
# ZettaBrain hero demo — echoes realistic terminal output for each phase.
# Sourced by demo/init.sh so 'install', 'setup', 'ingest', 'chat' are available
# as plain commands inside the vhs tape session.

GRN='\033[0;32m'
CYN='\033[0;36m'
YLW='\033[0;33m'
BLD='\033[1m'
DIM='\033[2m'
RST='\033[0m'

ok()  { echo -e "  ${GRN}✓${RST}  $*"; }
inf() { echo -e "  ${CYN}[INFO]${RST}  $*"; }
hdr() { echo -e "\n${BLD}$*${RST}"; }

# ── Phase 1: install ──────────────────────────────────────────────────────────
install() {
  echo ""
  inf "Detected: Ubuntu 22.04 LTS  (x86_64)"
  sleep 0.3
  ok  "Python 3.11.9 ready"
  sleep 0.2
  inf "Installing zettabrain-rag via pipx..."
  sleep 0.6
  ok  "zettabrain-rag 0.5.24 installed"
  sleep 0.2
  inf "Installing Ollama..."
  sleep 0.5
  ok  "Ollama 0.6.8 running"
  sleep 0.2
  inf "Pulling embedding model: nomic-embed-text..."
  sleep 0.5
  ok  "nomic-embed-text ready"
  sleep 0.3
  echo ""
  echo -e "  ${GRN}${BLD}Installation complete.${RST}  Run: ${CYN}sudo zettabrain-setup${RST}"
  echo ""
}

# ── Phase 2: setup ────────────────────────────────────────────────────────────
setup() {
  echo ""
  echo -e "${BLD}${CYN}╔══════════════════════════════════════════════════╗${RST}"
  echo -e "${BLD}${CYN}║   ZettaBrain RAG  —  Setup Wizard  v0.5.24      ║${RST}"
  echo -e "${BLD}${CYN}╚══════════════════════════════════════════════════╝${RST}"
  echo ""
  sleep 0.3

  echo -e "${DIM}── Step 1/6: Storage${RST}"
  sleep 0.2
  ok  "Storage type : LOCAL"
  ok  "Documents    : /home/demo/documents  (12 files)"
  echo ""
  sleep 0.3

  echo -e "${DIM}── Step 2/6: Embedding model${RST}"
  sleep 0.2
  ok  "nomic-embed-text already present"
  echo ""
  sleep 0.3

  echo -e "${DIM}── Step 3/6: LLM selection${RST}"
  sleep 0.2
  echo -e "  Hardware detected: ${YLW}CPU only${RST}"
  echo -e "  Recommended model: ${GRN}phi4:3.8b${RST}  (best CPU quality/speed)"
  echo ""
  echo "  CPU-optimised models (no GPU required):"
  echo -e "    ${GRN}1) phi4:3.8b${RST}       — recommended  ← default"
  echo      "    2) qwen3:0.6b      — ultrafast"
  echo      "    3) gemma3:1b       — tiny"
  echo      "    4) tinyllama:1.1b  — lightweight"
  echo      "    5) llama3.2:3b     — general purpose"
  sleep 0.6
  echo ""
  ok  "Selected LLM: phi4:3.8b"
  sleep 0.3
  inf "Pulling phi4:3.8b — this may take a few minutes..."
  sleep 0.7
  ok  "LLM ready: phi4:3.8b"
  echo ""
  sleep 0.3

  echo -e "${DIM}── Step 4/6: HTTPS / TLS${RST}"
  sleep 0.2
  ok  "TLS: local.zettabrain.app (trusted cert, traffic stays on this machine)"
  echo ""
  sleep 0.3

  echo -e "${DIM}── Step 5/6: System service${RST}"
  sleep 0.2
  ok  "ZettaBrain web server started and enabled on boot"
  echo ""
  sleep 0.2

  echo -e "${BLD}${GRN}╔══════════════════════════════════════════╗${RST}"
  echo -e "${BLD}${GRN}║        ZettaBrain Setup Complete!        ║${RST}"
  echo -e "${BLD}${GRN}╚══════════════════════════════════════════╝${RST}"
  echo ""
  echo -e "  Open in browser: ${CYN}https://local.zettabrain.app:7860${RST}"
  echo ""
}

# ── Phase 3: ingest ───────────────────────────────────────────────────────────
ingest() {
  echo ""
  inf "Found 12 supported file(s) in /home/demo/documents"
  echo ""
  sleep 0.2
  ok  "01_Employee_Trading_Policy.docx   (24/24 chunks)"
  sleep 0.15
  ok  "02_AML_Procedures_Manual.docx     (31/31 chunks)"
  sleep 0.15
  ok  "03_KYC_Onboarding_Guide.docx      (28/28 chunks)"
  sleep 0.15
  ok  "04_Employee_Benefits_Guide.docx   (22/22 chunks)"
  sleep 0.15
  ok  "05_Expense_Policy.docx            (19/19 chunks)"
  sleep 0.15
  ok  "06_Risk_Assessment_Framework.docx (33/33 chunks)"
  sleep 0.15
  ok  "07_Performance_Review.docx        (21/21 chunks)"
  sleep 0.15
  ok  "08_Insider_Trading_Policy.docx    (26/26 chunks)"
  sleep 0.15
  ok  "09_IT_Security_Policy.docx        (29/29 chunks)"
  sleep 0.15
  ok  "10_New_Employee_Onboarding.docx   (25/25 chunks)"
  sleep 0.2
  echo ""
  echo -e "  ${GRN}${BLD}Done.${RST} 10 files ingested.  Total chunks in store: ${BLD}258${RST}"
  inf "Rebuilding BM25 keyword index... 258 chunks indexed."
  echo ""
}

# ── Phase 4: chat ─────────────────────────────────────────────────────────────
chat() {
  echo ""
  echo -e "${BLD}${CYN}ZettaBrain Chat${RST}  ${DIM}[phi4:3.8b · 258 chunks]${RST}  Type 'quit' to exit"
  echo -e "${DIM}────────────────────────────────────────────────────────────${RST}"
  echo ""
  sleep 0.5
  echo -e "${BLD}You:${RST} What is the pre-clearance process for trading securities?"
  echo ""
  sleep 0.4
  echo -ne "  ${DIM}Retrieving…${RST}"
  sleep 0.5
  echo -e "\r  ${GRN}⚡ 0.9s${RST}  5 chunks retrieved from 3 documents"
  echo ""
  sleep 0.3
  echo -e "${BLD}${CYN}ZettaBrain:${RST}"
  sleep 0.2
  echo    "  Submit a request via the ComplianceTrack portal at least"
  sleep 0.1
  echo    "  24 hours before the intended trade. Once approved, the"
  sleep 0.1
  echo    "  clearance is valid for 48 hours from approval time."
  echo ""
  sleep 0.1
  echo -e "  ${DIM}[01_Employee_Trading_Policy.docx · 08_Insider_Trading_Policy.docx]${RST}"
  echo ""
  sleep 0.4
  echo -e "${BLD}You:${RST} What should I do if I suspect a PHI breach?"
  echo ""
  sleep 0.4
  echo -ne "  ${DIM}Retrieving…${RST}"
  sleep 0.5
  echo -e "\r  ${GRN}⚡ 0.8s${RST}  5 chunks retrieved from 2 documents"
  echo ""
  sleep 0.3
  echo -e "${BLD}${CYN}ZettaBrain:${RST}"
  sleep 0.2
  echo    "  Immediately notify your Privacy Officer and contain the"
  sleep 0.1
  echo    "  breach. Affected individuals must be notified within 60"
  sleep 0.1
  echo    "  days; if 500+ individuals are affected, notify HHS and"
  sleep 0.1
  echo    "  media outlets in the affected state simultaneously."
  echo ""
  echo -e "  ${DIM}[01_HIPAA_Privacy_Policy.docx · 03_HIPAA_Security_ePHI.docx]${RST}"
  echo ""
}
