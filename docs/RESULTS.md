# Results note

## 1. Sanity checks (`python envctl.py baseline`, `python envctl.py oracle <task>`)

| Task | Untouched start | Oracle fix |
|---|---|---|
| fix-ordinal | 0.00 (guards 758/758) | 1.00 |
| fix-case-conversion | 0.00 (guards 798/798) | 1.00 |
| implement-parameterize | 0.00 (guards 821/821) | 1.00 |
| restore-irregular-plurals | 0.00 (guards 805/805) | 1.00 |

Every untouched task passes all of its guards, so each injected bug is
isolated to its own target functions, and the oracle scores 1.0 on all four.
Case counts vary slightly with the random seed.

One finding during building: the first version of the partial-credit task
gave an agent that **did nothing** a reward of 0.51, because many random
cases already passed in the broken code. I changed partial credit to count
only the cases where the starting code gives the wrong answer
(`discriminative_only`). The do-nothing score is now 0.00.

## 2. Exploit attempts (`python exploits/run_exploits.py`)

The "naive grader" is a deliberately simple baseline: copy the public upstream
test suite into the workspace and run pytest there. The hardened grader is
`tests/grade.py`.

| Attempt | Task | Naive | Hardened | Why |
|---|---|---|---|---|
| E1 edit or delete the visible tests, leave the bug | fix-ordinal | 0.00 | **0.00 blocked** | grader never runs `/app/tests` |
| E2 hardcode the answers from the public upstream tests, leave the bug | fix-ordinal | 1.00 | **0.00 blocked** | fresh random inputs on every run (target 308/411) |
| E3 plant a `conftest.py` that rewrites every test result to "passed" | fix-ordinal | 1.00 | **0.00 fixed** | clean room: only `inflection/__init__.py` is copied out; no pytest at all |
| E4 at grading time, import the grader's own `reference.py` and re-export it | fix-ordinal | 1.00 | **1.00 gets through locally** | see below |
| P1 honest partial fix (only person/people and man/men) | restore-irregular-plurals | 0.00 | 0.55 | partial credit works as intended |

**E3 got through and was fixed.** The naive grader runs pytest inside the
agent's directory, so any `conftest.py`, `pytest.ini` or plugin the agent
drops there runs inside the grader. The hardened grader copies the single
graded file into an empty temporary directory and runs it in a separate
`python -I -S` interpreter (no `PYTHONPATH`, no site-packages). The
comparison happens in a parent process that never imports agent code.

**E4 is the honest residual.** Agent code executes during grading, so it can
read anything the grading process can read, including the reference. The fix
is in the Docker verifier (`tests/test.sh`): it does `chmod -R go-rwx /tests`
and runs the child process as `nobody`, so the reference is unreadable and
the reward file is unwritable from agent code. *Status: implemented but not
yet verified in Docker. Locally on Windows there is no unprivileged user to
drop to, so E4 still scores 1.0 here.*

**Known limits, documented rather than fixed:**

- **Interpreter tampering.** The agent runs as root in the same container that
  later runs the verifier, so in principle it can replace
  `/usr/local/bin/python3` or the standard library itself. No in-container
  grader can fully defend against that. The real fix is to extract only
  `/app/inflection/__init__.py` and grade it in a fresh container built from
  the pristine image.
- **Contamination.** `inflection` is public, so a model may have memorised
  the correct code, or could `pip install inflection` and copy it. This
  cannot be blocked at grader level. Mitigations: no network for the agent,
  do not ship upstream in the image, and for training use perturbed or
  private forks whose behaviour differs from what the model memorised.

## 3. Agent runs

*TODO (to be done at home): runs of `agent/mini_agent.py` with a local
Ollama model on each task, 3 seeds each. Table: task, run, reward,
steps, what the agent did.*

**What these runs do not prove.** A handful of runs on 3 or 4 tasks is
anecdote, not measurement: with n = 3 per task, a 0/3 against a 2/3 is well
within noise. They also do not show that the reward is unhackable by a
stronger model (only that the specific exploits above are handled), that the
tasks are well calibrated, or that skill on them transfers anywhere.

**How I would measure whether training here helps.** Generate a larger task
pool with the same pipeline (many bugs, several libraries), and split it by
*library* into train and held-out sets so there is no leakage. Measure pass@1
and pass@k with many samples per task, with confidence intervals, before and
after RL fine-tuning on the train split. Also check transfer to an external
benchmark (for example a slice of SWE-bench Verified) to catch overfitting to
this format. Track the rate of reward hacking during training (for example
grader-file access, or high reward with a large diff) as a separate signal.
