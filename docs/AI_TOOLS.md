# AI tools used

- **Claude Code (Claude Opus), desktop app.** I used it as a pair programmer.
  We discussed the design together: the choice of library, the task ladder,
  the exploit list, and switching to Harbor's separate-verifier mode after
  `harbor lint` flagged the shared-container risk. It drafted most of the
  code and the first drafts of these notes, and it ran the Docker, Harbor and
  exploit checks. I reviewed the design decisions and the results and edited
  the write-ups.
- **Agents under test:**
  - `qwen2.5-coder:3b`, a free local model via Ollama, driven by
    `agent/mini_agent.py`.
  - Claude Sonnet as a "strong agent" (a Claude Code subagent), clearly
    labelled in docs/RESULTS.md as not free. It ran on my existing
    subscription; no API credits were bought.
- No paid APIs or cloud compute were used.
