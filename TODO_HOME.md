# To finish at home (delete this file before submitting)

Deadline: reply to the Adzzat email by **Sun 22 Nov, ~12:30**, keeping the subject unchanged.

1. `git pull`, then `python -m pip install pytest`, then
   `python envctl.py baseline` (all 0.0) and `python exploits/run_exploits.py`.
2. Docker (Docker Desktop running):
   - `python tools/docker_check.py fix-ordinal --oracle` → expect `REWARD=1.0000`
   - `python tools/docker_check.py fix-ordinal` → expect `REWARD=0.0000`
   - `python tools/docker_check.py fix-ordinal --exploit e4` → expect
     `REWARD=0.0000`. **This is the key check**: it verifies the E4 fix
     (`nobody` user plus `chmod`). Then update the E4 row in docs/RESULTS.md.
   - Run `--oracle` for the other 3 tasks too.
3. Optional: `pip install harbor`, then `harbor run -p tasks/fix-ordinal -a oracle`.
   If `task.toml` keys need adjusting, fix them in `tools/build_tasks.py` and rebuild.
4. Agent runs: install Ollama, run `ollama pull qwen2.5-coder:7b`, then
   `python agent/mini_agent.py <task>` 3 times per task. Fill in section 3 of
   docs/RESULTS.md with the rewards, and note anything sneaky the model tried.
5. Portfolio evidence: link to an RL environment you built before, plus a few
   lines on which parts were yours. Leave it out if there isn't one, and say
   so honestly.
6. Email: repo link, scope note (docs/SCOPE.md), results note
   (docs/RESULTS.md), AI tools (docs/AI_TOOLS.md), and the portfolio lines.
   The repo is private, so either make it public or add them as collaborators.
