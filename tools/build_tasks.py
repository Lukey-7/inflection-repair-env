#!/usr/bin/env python3
"""Generate the Harbor task directories under tasks/ from upstream + bug specs.

Each task = pristine upstream ``inflection`` with a small, exact set of edits
(the "bugs"). Re-run after changing anything in common/ or in TASKS below:

    python tools/build_tasks.py
"""
import json
import os
import shutil
import textwrap

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPSTREAM = os.path.join(ROOT, "upstream", "inflection.py")
COMMON = os.path.join(ROOT, "common")

AUTHOR = "Varun R Darji"

COMMON_NOTES = """
## Rules

- Work in `/app`. The library is `/app/inflection/__init__.py`.
- **Only `/app/inflection/__init__.py` is graded.** Put your whole fix in that
  file; other files you create or edit are ignored.
- Keep every public function name and signature unchanged, and keep the
  library dependency-free (standard library only).
- A few visible tests are in `/app/tests` (`cd /app && python -m pytest -q`).
  They are deliberately incomplete. The hidden grader checks many more inputs,
  including randomly generated ones, and also checks that every other function
  in the library still behaves correctly.
"""

T3_SPEC = """
`parameterize(string, separator='-')` turns arbitrary text into a URL slug.
It must behave exactly as follows:

1. Transliterate: apply Unicode NFKD normalisation, then drop every character
   that is not ASCII (the existing `transliterate()` helper does this).
2. Replace every maximal run of characters that are **not** ASCII letters,
   ASCII digits, `-` or `_` with a single `separator`. (`-` and `_` in the
   input are kept as they are, whatever the separator is.)
3. If `separator` is not empty:
   - collapse any run of two or more consecutive `separator` characters into
     one `separator`;
   - then remove one leading `separator` and one trailing `separator`, if
     present.
4. Lower-case the result.

Callers only ever pass a single-character separator or the empty string.

Examples:

```
parameterize("Donald E. Knuth")              -> "donald-e-knuth"
parameterize("Trailing bad characters!@#")   -> "trailing-bad-characters"
parameterize("Squeeze   separators")         -> "squeeze-separators"
parameterize("Malmö")                        -> "malmo"
parameterize("Donald E. Knuth", "_")         -> "donald_e_knuth"
parameterize("With-some-dashes", "_")        -> "with-some-dashes"
parameterize("Donald E. Knuth", "")          -> "donaldeknuth"
parameterize("a -- b")                       -> "a-b"
```
"""

T4_SPEC = """
A refactor deleted the library's support for irregular nouns, so for example
`pluralize("person")` now returns `"persons"` and `singularize("children")`
returns `"children"`.

Restore support for exactly these irregular pairs (singular -> plural):

```
person -> people     man   -> men      human  -> humans   child  -> children
sex    -> sexes      move  -> moves    cow    -> kine     zombie -> zombies
```

Requirements:

- Both `pluralize` and `singularize` must handle them, and so must anything
  built on them (`tableize`).
- They must also apply when the irregular word ends a longer word:
  `salesperson -> salespeople`, `node_child -> node_children`,
  `spokesman -> spokesmen`, `woman -> women`.
- Keep the case of the first letter: `Person -> People`, `Child -> Children`.
- Pluralizing a plural irregular word leaves it unchanged
  (`people -> people`), and singularizing a singular one leaves it unchanged.
- Note that `human -> humans` is listed on purpose: it must not become
  `humen`.

**Partial credit:** your reward is the fraction of hidden irregular-noun checks
that pass, but it drops to 0 if any other behaviour of the library breaks.
"""

TASKS = [
    {
        "name": "fix-ordinal",
        "difficulty": "easy",
        "target_groups": ["ordinal"],
        "reward_type": "binary",
        "bugs": [
            ("    if number % 100 in (11, 12, 13):",
             "    if number % 10 in (11, 12, 13):"),
        ],
        "instruction": """
# Fix ordinal suffixes

Bug report against the `inflection` library in `/app`:

> `inflection.ordinalize(11)` returns `'11st'`, but it should be `'11th'`.
> The same goes for 12 (`'12th'`) and 13 (`'13th'`), and for numbers such as
> 111, 1012 and -213. Other numbers look right (`'1st'`, `'22nd'`, `'103rd'`).

Find and fix the bug.
""",
        "visible_tests": """
import inflection


def test_simple_ordinals():
    assert inflection.ordinalize(1) == "1st"
    assert inflection.ordinalize(2) == "2nd"
    assert inflection.ordinalize(3) == "3rd"
    assert inflection.ordinalize(4) == "4th"


def test_teens():
    assert inflection.ordinalize(11) == "11th"
    assert inflection.ordinalize(12) == "12th"
    assert inflection.ordinalize(13) == "13th"
""",
    },
    {
        "name": "fix-case-conversion",
        "difficulty": "medium",
        "target_groups": ["case"],
        "reward_type": "binary",
        "bugs": [
            ("    word = re.sub(r\"([A-Z]+)([A-Z][a-z])\", r'\\1_\\2', word)\n",
             ""),
            ("    word = re.sub(r\"_id$\", \"\", word)",
             "    word = re.sub(r\"id$\", \"\", word)"),
        ],
        "instruction": """
# Fix case-conversion bugs

Two bug reports against the `inflection` library in `/app`:

> 1. `inflection.titleize("HTMLTidyGenerator")` returns `'Htmltidy Generator'`
>    instead of `'Html Tidy Generator'`, and
>    `inflection.tableize("HTMLPage")` returns `'htmlpages'` instead of
>    `'html_pages'`.
> 2. `inflection.humanize("paid")` returns `'Pa'` instead of `'Paid'`, while
>    `humanize("author_id")` should still give `'Author'`.

Fix the root causes in the library. Several public functions are built on top
of each other, so check which function is actually responsible before you
change anything.
""",
        "visible_tests": """
import inflection


def test_titleize_acronym():
    assert inflection.titleize("HTMLTidyGenerator") == "Html Tidy Generator"


def test_tableize_acronym():
    assert inflection.tableize("HTMLPage") == "html_pages"


def test_humanize():
    assert inflection.humanize("paid") == "Paid"
    assert inflection.humanize("author_id") == "Author"
""",
    },
    {
        "name": "implement-parameterize",
        "difficulty": "hard",
        "target_groups": ["parameterize"],
        "reward_type": "binary",
        "bugs": [
            (
                "    string = transliterate(string)\n"
                "    # Turn unwanted chars into the separator\n"
                "    string = re.sub(r\"(?i)[^a-z0-9\\-_]+\", separator, string)\n"
                "    if separator:\n"
                "        re_sep = re.escape(separator)\n"
                "        # No more than one of the separator in a row.\n"
                "        string = re.sub(r'%s{2,}' % re_sep, separator, string)\n"
                "        # Remove leading/trailing separator.\n"
                "        string = re.sub(r\"(?i)^{sep}|{sep}$\".format(sep=re_sep), '', string)\n"
                "\n"
                "    return string.lower()\n",
                "    raise NotImplementedError(\"parameterize\")\n",
            ),
        ],
        "instruction": "\n# Implement `parameterize`\n\n"
                       "In the `inflection` library in `/app`, the body of "
                       "`parameterize` has been removed. Implement it.\n"
                       + T3_SPEC,
        "visible_tests": """
import inflection


def test_basic():
    assert inflection.parameterize("Donald E. Knuth") == "donald-e-knuth"


def test_underscore_separator():
    assert inflection.parameterize("Donald E. Knuth", "_") == "donald_e_knuth"


def test_no_separator():
    assert inflection.parameterize("Donald E. Knuth", "") == "donaldeknuth"
""",
    },
    {
        "name": "restore-irregular-plurals",
        "difficulty": "medium",
        "target_groups": ["plural_irregular"],
        "reward_type": "partial",
        "bugs": [
            ("IRREGULAR_DEF", ""),
            ("IRREGULAR_CALLS", ""),
        ],
        "instruction": "\n# Restore irregular plurals (partial credit)\n"
                       + T4_SPEC,
        "visible_tests": """
import inflection


def test_person():
    assert inflection.pluralize("person") == "people"
    assert inflection.singularize("people") == "person"


def test_child_compound():
    assert inflection.pluralize("node_child") == "node_children"
""",
    },
]

TASK_TOML = """\
version = "1.0"

# Only the graded file leaves the agent's container. The verifier runs in a
# fresh container built from the same image, so nothing else the agent did
# (planted files, a patched interpreter, edited site-packages) reaches it.
artifacts = ["/app/inflection/__init__.py"]

[metadata]
author_name = "{author}"
difficulty = "{difficulty}"
category = "software-engineering"
tags = ["python", "bug-fix", "inflection"]

[verifier]
timeout_sec = 300.0
environment_mode = "separate"

[agent]
timeout_sec = 900.0

[environment]
build_timeout_sec = 600.0
cpus = 1
memory_mb = 2048
storage_mb = 4096
"""


def _irregular_blocks(src):
    start = src.index("def _irregular(")
    end = src.index("def camelize(")
    calls_start = src.index("_irregular('person', 'people')")
    return src[start:end], src[calls_start:]


def apply_bugs(src, bugs):
    irr_def, irr_calls = _irregular_blocks(src)
    for old, new in bugs:
        if old == "IRREGULAR_DEF":
            old = irr_def
        elif old == "IRREGULAR_CALLS":
            old = irr_calls
        if src.count(old) != 1:
            raise SystemExit("bug anchor not found exactly once: %r" % old[:60])
        src = src.replace(old, new)
    return src


def _write(path, text, mode=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def build():
    with open(UPSTREAM, encoding="utf-8") as fh:
        upstream = fh.read()
    for task in TASKS:
        tdir = os.path.join(ROOT, "tasks", task["name"])
        if os.path.isdir(tdir):
            shutil.rmtree(tdir)
        buggy = apply_bugs(upstream, task["bugs"])
        assert buggy != upstream

        _write(os.path.join(tdir, "instruction.md"),
               task["instruction"].lstrip() + COMMON_NOTES)
        _write(os.path.join(tdir, "task.toml"),
               TASK_TOML.format(author=AUTHOR, difficulty=task["difficulty"]))

        env = os.path.join(tdir, "environment")
        _write(os.path.join(env, "Dockerfile"),
               open(os.path.join(COMMON, "Dockerfile"), encoding="utf-8").read())
        _write(os.path.join(env, "app", "inflection", "__init__.py"), buggy)
        _write(os.path.join(env, "app", "tests", "test_visible.py"),
               textwrap.dedent(task["visible_tests"]).lstrip())

        sol = os.path.join(tdir, "solution")
        _write(os.path.join(sol, "inflection_fixed.py"), upstream)
        _write(os.path.join(sol, "solve.sh"),
               open(os.path.join(COMMON, "solve.sh"), encoding="utf-8").read())

        tests = os.path.join(tdir, "tests")
        for name in ("test.sh", "grade.py", "child.py", "cases_lib.py"):
            _write(os.path.join(tests, name),
                   open(os.path.join(COMMON, name), encoding="utf-8").read())
        _write(os.path.join(tests, "reference.py"), upstream)
        _write(os.path.join(tests, "start_state.py"), buggy)
        _write(os.path.join(tests, "task.json"), json.dumps({
            "name": task["name"],
            "target_groups": task["target_groups"],
            "reward_type": task["reward_type"],
            "discriminative_only": task["reward_type"] == "partial",
            "n_random": 300,
            "n_guard_random": 40,
        }, indent=2) + "\n")
        print("built", tdir)


if __name__ == "__main__":
    build()
