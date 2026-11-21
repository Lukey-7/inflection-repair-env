# Results note

Full tables and reasoning: [RESULTS_DETAIL.md](RESULTS_DETAIL.md).

**Sanity.** All four tasks pass `harbor lint`. In Harbor, the oracle scores
1.00 on every task and an agent that does nothing scores 0.00. Every
untouched task passes all of its guard checks, so each bug is isolated. One
fix while building: on the partial-credit task, doing nothing first scored
0.51. Credit now counts only the cases the broken code gets wrong, so doing
nothing scores 0.00.

## Exploits (every attempt leaves the bug in place)

| Attempt | Naive grader* | Hardened, Docker | Outcome |
|---|---|---|---|
| E1 edit or delete the visible tests | 0.00 | 0.00 | blocked: visible tests are never graded |
| E2 hardcode the answers from the public upstream tests | 1.00 | 0.00 | blocked: fresh random inputs every run |
| E3 plant a `conftest.py` that forces every test to pass | 1.00 | 0.00 | **got through; fixed** by grading one copied file in a clean `python -I -S` child |
| E4 import the grader's own reference at grading time | 1.00 | 0.00 | **got through; fixed**: the submission runs as `nobody` and `/tests` is unreadable. A control with the protection bypassed scores 1.00 |

\*Naive grader: copy the public upstream tests into the workspace and run pytest.

The verifier also runs in Harbor's **separate** container, receiving only
`inflection/__init__.py`, so a root agent tampering with Python cannot reach
it. **Not fixed: contamination.** The library is public, so the correct code
may be memorised. Mitigation: perturbed or private forks, and no network.

## Agent runs (1 run per task)

| Task | qwen2.5-coder:3b (free, local CPU) | Claude Sonnet (subscription, not free) |
|---|---|---|
| fix-ordinal | 0.00: looped on a failing edit | 1.00 |
| fix-case-conversion | 0.00: edited the wrong functions; guards caught 6 regressions | 1.00 |
| implement-parameterize | 0.00: replaced the whole file with 10 lines; guards 16/821 | 1.00 |
| restore-irregular-plurals | 0.00: one no-op edit, then "done" | 1.00 (fixed its own `cow -> kine` slip) |

No run tried to game the grader. A harness bug (Ollama's 4K default context,
smaller than the file) was found and fixed before these runs. Transcripts are
in `runs/`.

## What this does not prove, and how I would measure training gains

One run per task is anecdote, not evidence. It shows the tasks are solvable,
and the guards catch collateral damage. It also shows the ladder is badly
calibrated: a 3B model solves nothing and a frontier model solves everything.
It does not show the reward is unhackable by an adversarial model, or that
skill here transfers.

To measure training gains, I would generate a larger pool (many bugs,
several libraries, perturbed forks) and split train and held-out sets **by
library**. Then compare pass@1 and pass@k, with confidence intervals, before
and after RL; check transfer on an external benchmark (for example a slice of
SWE-bench Verified); and track hacking attempts during training as a separate
signal.
