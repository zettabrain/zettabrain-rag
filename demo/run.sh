#!/usr/bin/env bash
# Run all demo phases sequentially — recorded by asciinema.
# Usage: asciinema rec hero.cast -c demo/run.sh
set -e
source "$(dirname "$0")/demo.sh"

GRN='\033[0;32m'
RST='\033[0m'
prompt() { echo -e "\n${GRN}❯${RST} $*"; }

clear
sleep 0.5

prompt "curl -fsSL https://zettabrain.app/install.sh | sudo bash"
sleep 0.4
install
sleep 0.6

prompt "sudo zettabrain-setup"
sleep 0.4
setup
sleep 0.6

prompt "zettabrain-ingest --folder ~/documents"
sleep 0.4
ingest
sleep 0.6

prompt "zettabrain-chat"
sleep 0.4
chat
sleep 1.5
