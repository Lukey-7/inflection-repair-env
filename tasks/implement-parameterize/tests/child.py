"""Sandboxed evaluation child.

Runs in a separate interpreter started with ``python -I -S`` (isolated mode, no
site-packages), as an unprivileged user when the grader runs inside Docker.
It imports ONLY the submitted ``inflection/__init__.py`` that the grader copied
into a clean temporary directory, calls the requested functions and writes the
raw return values back to the grader. It never sees expected answers: the
comparison against the reference happens in the parent process.
"""
import json
import os
import sys

ALLOWED = {
    "camelize", "dasherize", "humanize", "ordinal", "ordinalize",
    "parameterize", "pluralize", "singularize", "tableize", "titleize",
    "transliterate", "underscore",
}


def run_cases(mod, cases):
    """Call ``mod.<func>(*args)`` for every case; never raise."""
    out = []
    for func, args in cases:
        if func not in ALLOWED:
            out.append(["err", "NotAllowed"])
            continue
        try:
            value = getattr(mod, func)(*args)
        except KeyboardInterrupt:
            raise
        except BaseException as exc:  # includes SystemExit from submissions
            out.append(["err", type(exc).__name__])
            continue
        if isinstance(value, str) and type(value) is str:
            out.append(["ok", value])
        else:
            # A str subclass could override __eq__; refuse anything but str.
            out.append(["bad", type(value).__name__])
    return out


def main():
    submission_dir = sys.argv[1]
    cases = json.loads(sys.stdin.read())

    # Keep a private handle on the real stdout, then point fd 1 at stderr so
    # anything the submission prints cannot be mistaken for our result.
    real_out = os.fdopen(os.dup(1), "w", encoding="utf-8")
    os.dup2(2, 1)
    sys.stdout = sys.stderr

    sys.path.insert(0, submission_dir)
    try:
        import inflection  # noqa: the submission
        payload = {"results": run_cases(inflection, cases)}
    except KeyboardInterrupt:
        raise
    except BaseException as exc:
        payload = {"import_error": "%s: %s" % (type(exc).__name__, exc)}
    real_out.write(json.dumps(payload))
    real_out.flush()


if __name__ == "__main__":
    main()
