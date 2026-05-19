# ZettaBrain — README hero GIF
# Run: vhs demo/hero.tape  (from repo root)
# Output: demo/hero.gif  (~30 seconds)

Output demo/hero.gif

Set Shell      "bash"
Set FontFamily "JetBrains Mono"
Set FontSize   13
Set Width      960
Set Height     560
Set Theme      "Dracula"
Set Framerate  24
Set PlaybackSpeed 1
Set TypingSpeed   35ms

# Boot — load demo functions invisibly then clear the screen
Hide
Type "source demo/init.sh"
Enter
Sleep 500ms
Show

# ── Header: show the one-line install command ─────────────────────────────────
Sleep 400ms
Type "curl -fsSL https://zettabrain.app/install.sh | sudo bash"
Sleep 600ms

# Replace with demo output (command is aliased in the demo shell)
Ctrl+C
Sleep 200ms
Type "install"
Enter
Sleep 3200ms

# ── Setup wizard ──────────────────────────────────────────────────────────────
Type "sudo zettabrain-setup"
Sleep 400ms
Ctrl+C
Sleep 200ms
Type "setup"
Enter
Sleep 7500ms

# ── Ingest documents ──────────────────────────────────────────────────────────
Type "zettabrain-ingest --folder ~/documents"
Sleep 400ms
Ctrl+C
Sleep 200ms
Type "ingest"
Enter
Sleep 3500ms

# ── Chat ─────────────────────────────────────────────────────────────────────
Type "zettabrain-chat"
Sleep 400ms
Ctrl+C
Sleep 200ms
Type "chat"
Enter
Sleep 12000ms

# Hold on the last frame
Sleep 1500ms
