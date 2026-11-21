# Results: full detail

The one-page summary is [RESULTS.md](RESULTS.md); this file has the complete tables and reasoning.

## 1. Sanity checks

| Check | fix-ordinal | fix-case-conversion | implement-parameterize | restore-irregular-plurals |
|---|---|---|---|---|
| Local grader, untouched start | 0.00 | 0.00 | 0.00 | 0.00 |
| Local grader, oracle fix | 1.00 | 1.00 | 1.00 | 1.00 |
| Docker verifier (`tools/docker_check.py`), untouched / oracle | 0.00 / 1.00 | 0.00 / 1.00 | 0.00 / 1.00 | 0.00 / 1.00 |
| **Harbor** `harbor run -a oracle` | 1.00 | 1.00 | 1.00 | 1.00 |
| **Harbor** `harbor run -a nop` (does nothing) | 0.00 | 0.00 | 0.00 | 0.00 |

Every untouched task passes all of its guard checks, so each injected bug is
isolated to its own target functions. `harbor lint` passes on all four tasks.
Two of the first Harbor oracle trials failed with a Docker Hub network error
while the base image was being pulled (not a task fault); both scored 1.00 on
rerun.

One finding during building: the first version of the partial-credit task
gave an agent that **did nothing** a reward of 0.51, because many random
cases already passed in the broken code. Partial credit now counts only the
cases where the starting code is wrong (`discriminative_only`), so doing
nothing scores 0.00.

## 2. Exploit attempts

The "naive grader" is a deliberately simple baseline: copy the public upstream
test suite into the workspace and run pytest there. The hardened grader is
`tests/grade.py`. "Docker" is the real verifier (`tests/test.sh`) in the task
image.

| Attempt (all leave the bug in place) | Naive | Hardened, local | Hardened, Docker | Status |
|---|---|---|---|---|
| E1 edit or delete the visible tests | 0.00 | 0.00 | 0.00 | blocked: the grader never runs `/app/tests` |
| E2 hardcode the answers from the public upstream tests | 1.00 | 0.00 | 0.00 | blocked: fresh random inputs every run |
| E3 plant a `conftest.py` that rewrites every result to "passed" | 1.00 | 0.00 | 0.00 | **got through the naive grader; fixed** |
| E4 at grading time, import the grader's own `reference.py` | 1.00 | 1.00 | 0.00 | **got through; fixed in Docker** |
| P1 honest partial fix (task 4, two of eight pairs) | 0.00 | 0.55 | – | partial credit works as intended |

**E3, conftest hijack.** The naive grader runs pytest inside the agent's
directory, so a planted `conftest.py` runs inside the grader. Fix: copy the
single graded file into an empty temporary directory and run it in a
separate `python -I -S` interpreter. The comparison happens in a parent
process that never imports agent code.

**E4, reading the oracle.** Agent code runs during grading, so it can read
anything the grading process can read. Fix: `tests/test.sh` makes `/tests`
readable only by root and runs the submission as `nobody`. Verified with a
control in the same container: the exploit scores **1.00 with the
protection bypassed** (calling `grade.py` directly as root) and **0.00
through `test.sh`**. Locally on Windows there is no unprivileged user to drop
to, so the local column stays 1.00.

**Interpreter tampering, now addressed.** The agent runs as root, so in a
shared container it could replace `python3` or the standard library before
the verifier runs. `harbor lint` flags exactly this. The tasks therefore use
`[verifier] environment_mode = "separate"` with
`artifacts = ["/app/inflection/__init__.py"]`. Harbor copies only that one
file into a fresh container built from the pristine image, so planted files,
a patched interpreter or edited site-packages never reach the grader.
Confirmed in the Harbor runs above: the artefact arrives and is graded
(411/411 target, 758/758 guard for the oracle).

**Known limit: contamination.** `inflection` is public, so a model may have
memorised the correct code (one of the agents below said its fix "matches
the upstream library as I remember it"). No grader can block this. For
training I would use perturbed or private forks whose correct behaviour
differs from upstream, and run the agent with no network.

## 3. Agent runs

**Strong agent: Claude Sonnet as a subagent, 1 run per task.** This was not a
free model; it ran on my existing Claude subscription, and I disclose it as
such. Each run had only its workspace and instruction, and its result was
graded 3 times with fresh random seeds.

| Task | Reward (3 gradings) | What happened |
|---|---|---|
| fix-ordinal | 1.00, 1.00, 1.00 | Spotted that `% 10` can never equal 11 to 13; one-line fix |
| fix-case-conversion | 1.00, 1.00, 1.00 | Traced both symptoms to `underscore` and `humanize`; left `titleize` alone |
| implement-parameterize | 1.00, 1.00, 1.00 | Implemented the spec literally; used a lambda replacement to avoid backslash bugs |
| restore-irregular-plurals | 1.00, 1.00, 1.00 | First attempt broke `cow -> kine` (gave `cine`), noticed it and rewrote the helper |

No run tried to edit tests or hardcode answers, and each one said so when
asked.

**Free agent: qwen2.5-coder:3b via Ollama on CPU, 1 run per task, at most
12 steps** (`agent/mini_agent.py`; transcripts in `runs/`). On this laptop
the four runs took about 47 minutes in total, which is why there is only one
run each.

| Task | Reward | Target | Guard | What happened |
|---|---|---|---|---|
| fix-ordinal | 0.00 | 300/411 | 758/758 | Read the file and ran the tests, then inserted a duplicate `ordinal` body above the old one (no effect). After that it repeated the same failing `replace` 7 times until the step limit |
| fix-case-conversion | 0.00 | 281/371 | **792/798** | Edited the wrong functions (`pluralize`, `singularize`); its `humanize` edit re-applied the bug. The guards caught the collateral damage |
| implement-parameterize | 0.00 | 171/348 | **16/821** | Overwrote the whole library with a 10-line file containing only `parameterize`, then declared itself done. Visible-only grading would have missed this; the guards scored it 0 |
| restore-irregular-plurals | 0.00 | 0/159 | 805/805 | Made one no-op edit and declared itself done after 3 steps |

Two notes from these runs:

- **Harness bug found and fixed.** The first attempt silently ran with
  Ollama's default 4,096-token context, smaller than the library file, so
  the model never saw the end of it. I stopped the run, set
  `num_ctx = 16384`, made the transcript flush every step, and reran. Only
  the corrected runs are reported.
- **The guards earned their keep.** In two of the four runs the agent broke
  code outside the target. A grader that only checks the reported symptom
  would have missed it, and in one case (deleting the whole file) a grader
  that only checks the target function would have scored it partly right.

Taken together, the two agents bracket the tasks: a 3B model on CPU solves
none, and a frontier model solves all four first time. That points to a
calibration problem. There is no middle rung yet, and these tasks would give
little learning signal to either model.

**What these runs do not prove.** With 1 run per task, these are
anecdotes, not measurements. The strong agent solving everything mainly shows
the tasks are solvable and the instructions unambiguous; it also suggests the
tasks are too easy for frontier models, which is plausible given
contamination. Neither run shows that the reward is unhackable by a model
that is actively trying to hack it, only that these specific exploits are
handled. They say nothing about whether skill here transfers.

**How I would measure whether training here helps.** Generate a larger task
pool with the same pipeline (many bugs, several libraries, perturbed forks),
and split it by *library* into train and held-out sets so there is no
leakage. Measure pass@1 and pass@k with many samples per task, with
confidence intervals, before and after RL fine-tuning on the train split.
Also check transfer to an external benchmark (for example a slice of
SWE-bench Verified) to catch overfitting to this format. Track hacking
attempts during training (grader-file access, high reward with an outsized
diff) as a separate signal.
