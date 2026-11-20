# Scope note

**Source.** [`inflection`](https://pypi.org/project/inflection/) 0.5.1, a
single-file MIT-licensed Python port of Rails' inflector (pluralize,
camelize, parameterize, ordinalize, ...). It is small (426 lines), pure
standard library, deterministic, and ships a good upstream test suite. That
makes it cheap to containerise and, more importantly, gives an exact
reference implementation to grade against.

**What the agent does.** Each task drops the agent into `/app`, a copy of the
library with a known defect, plus a bug report or spec in `instruction.md`.
The agent can read files, edit them and run shell commands (including the
few visible tests). The action space is the shell; the observation is the
command output. There are four tasks:

| Task | Difficulty | What is wrong |
|---|---|---|
| `fix-ordinal` | easy | one-character bug: `11` becomes `11st` |
| `fix-case-conversion` | medium | two independent bugs in `underscore` and `humanize`, reported through `titleize`/`tableize`; the agent has to trace the symptoms to their root causes |
| `implement-parameterize` | hard | function body deleted; the agent implements it from a precise prose spec, including the edge cases around separators |
| `restore-irregular-plurals` | stretch, partial credit | irregular-noun support deleted; reward = fraction of the affected behaviours restored |

**What success is.** For tasks 1 to 3, reward 1.0 if the submitted
`inflection/__init__.py` matches the reference on every hidden check, and 0.0
otherwise. The hidden checks are fixed upstream inputs plus several hundred
fresh random inputs per run, covering both the target functions and every
other function (guards). Task 4 gives partial credit, counted only over the
cases that the broken starting code gets wrong, so doing nothing scores 0.

**Why a lab would want this.** It is a small instance of the shape that
matters for coding agents: localise a fault from a symptom-level report, make
a minimal fix without collateral damage, and implement exactly to a spec.
The guards measure regressions, not just whether the reported symptom went
away, and the differential grader produces an unbounded supply of fresh
checks, so the reward stays hard to overfit. The same pipeline (pristine
source, a scripted bug, the reference as oracle) scales to many tasks per
library, with calibrated difficulty.
