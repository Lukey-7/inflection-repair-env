#!/usr/bin/env python3
"""Objective grader for one inflection-repair task.

Design (each point closes a cheap way to game the reward):

1. Hidden checks: the cases come from ``cases_lib.py`` in the tests directory,
   which the agent never sees (Harbor copies /tests in only at verification).
   Visible tests in /app/tests are ignored entirely, so editing or deleting
   them changes nothing.
2. Fresh inputs every run: most cases are random, drawn with a new seed per
   grading run, and expected outputs come from the pristine reference
   implementation (differential testing). Hardcoding answers cannot keep up.
3. Clean room: only ``inflection/__init__.py`` is copied out of the workspace
   into an empty temp dir. conftest.py, pytest.ini, sitecustomize, .pth files
   and any other file the agent planted are left behind. Symlinks are refused.
4. Isolated interpreter: the submission runs in a child ``python -I -S``
   (no PYTHONPATH, no user or system site-packages), so an installed copy of
   upstream ``inflection`` or a patched pytest cannot be pulled in by accident.
5. The child only returns raw outputs; the comparison happens here, in a
   process that never imports the submission. Anything the submission prints
   goes to stderr, not into the result channel.
6. Inside Docker (``--sandbox-user nobody``) the child runs unprivileged, so
   it cannot read /tests (chmod 700 by test.sh) or write the reward file.

Reward: binary tasks score 1.0 only if every target and guard case matches.
Partial-credit tasks score (target cases matched / target cases) but drop to
0.0 if any guard case fails.
"""
import argparse
import importlib.util
import json
import os
import random
import shutil
import signal
import stat
import subprocess
import sys
import tempfile

CHILD_TIMEOUT_SEC = 60


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _write_reward(path, reward):
    if path:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w") as fh:
            fh.write("%.4f\n" % reward)


def _child_env():
    env = {"PYTHONHASHSEED": "0", "PYTHONIOENCODING": "utf-8"}
    for key in ("SYSTEMROOT", "PATH"):  # SYSTEMROOT is needed on Windows
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def run_submission(workspace, tests_dir, cases, sandbox_user=None):
    """Run the submission on ``cases`` in a clean room. Returns (results, err)."""
    src = os.path.join(workspace, "inflection", "__init__.py")
    if not os.path.isfile(src):
        return None, "missing inflection/__init__.py"
    if os.path.islink(src) or os.path.islink(os.path.dirname(src)):
        return None, "refusing symlinked submission"

    room = tempfile.mkdtemp(prefix="grade-room-")
    try:
        os.makedirs(os.path.join(room, "inflection"))
        dst = os.path.join(room, "inflection", "__init__.py")
        shutil.copyfile(src, dst)
        shutil.copyfile(os.path.join(tests_dir, "child.py"),
                        os.path.join(room, "child.py"))
        for path in (room, os.path.join(room, "inflection")):
            os.chmod(path, 0o755)
        for path in (dst, os.path.join(room, "child.py")):
            os.chmod(path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

        cmd = [sys.executable, "-I", "-S", os.path.join(room, "child.py"),
               room]
        kwargs = {}
        if sandbox_user and hasattr(os, "geteuid"):
            if os.geteuid() == 0:
                kwargs.update(user=sandbox_user, group="nogroup",
                              extra_groups=[])
            else:
                print("[grade] warning: not root, cannot drop to %r"
                      % sandbox_user, file=sys.stderr)
        if os.name == "posix":
            kwargs["start_new_session"] = True

        proc = subprocess.Popen(cmd, cwd=room, env=_child_env(),
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, **kwargs)
        try:
            out, err = proc.communicate(json.dumps(cases).encode("utf-8"),
                                        timeout=CHILD_TIMEOUT_SEC)
        except subprocess.TimeoutExpired:
            out, err = b"", b"timeout"
        finally:
            # Kill anything the submission may have left running.
            if os.name == "posix":
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    pass
            else:
                proc.kill()
            proc.wait()
        if not out:
            return None, "child produced no result (%s)" % \
                err.decode("utf-8", "replace")[-300:]
        try:
            payload = json.loads(out.decode("utf-8"))
        except ValueError:
            return None, "unparseable child output"
        if "import_error" in payload:
            return None, "import failed: " + payload["import_error"]
        results = payload.get("results")
        if not isinstance(results, list) or len(results) != len(cases):
            return None, "wrong number of results"
        return results, None
    finally:
        shutil.rmtree(room, ignore_errors=True)


def grade(workspace, tests_dir, seed=None, sandbox_user=None, verbose=True):
    with open(os.path.join(tests_dir, "task.json")) as fh:
        config = json.load(fh)
    if seed is None:
        seed = int.from_bytes(os.urandom(4), "big")
    rng = random.Random(seed)

    # Load grader-side code BEFORE running anything the agent wrote.
    cases_lib = _load(os.path.join(tests_dir, "cases_lib.py"), "_cases_lib")
    child = _load(os.path.join(tests_dir, "child.py"), "_grader_child")
    reference = _load(os.path.join(tests_dir, "reference.py"),
                      "_reference_inflection")

    tagged = cases_lib.build_cases(config, rng)
    if config.get("discriminative_only"):
        # Partial credit should reward only behaviour the agent had to
        # change: drop target cases the untouched starting code already
        # gets right, so doing nothing scores 0 rather than ~0.5.
        start = _load(os.path.join(tests_dir, "start_state.py"),
                      "_start_state_inflection")
        t_calls = [[f, a] for role, _, f, a in tagged if role == "target"]
        keep = iter([e != s for e, s in zip(
            child.run_cases(reference, t_calls),
            child.run_cases(start, t_calls))])
        tagged = [c for c in tagged if c[0] != "target" or next(keep)]
    calls = [[func, args] for _, _, func, args in tagged]
    expected = child.run_cases(reference, calls)

    got, error = run_submission(workspace, tests_dir, calls, sandbox_user)
    summary = {"task": config["name"], "seed": seed,
               "reward_type": config["reward_type"]}
    if error:
        summary.update(reward=0.0, error=error)
        return summary

    stats = {"target": [0, 0], "guard": [0, 0]}
    failures = []
    for (role, group, func, args), exp, act in zip(tagged, expected, got):
        stats[role][1] += 1
        if act == exp:
            stats[role][0] += 1
        elif len(failures) < 8:
            failures.append({"role": role, "call": "%s%r" % (func, tuple(args)),
                             "expected": exp, "got": act})

    t_ok, t_all = stats["target"]
    g_ok, g_all = stats["guard"]
    if g_ok < g_all:
        reward = 0.0
    elif config["reward_type"] == "partial":
        reward = t_ok / t_all if t_all else 0.0
    else:
        reward = 1.0 if t_ok == t_all else 0.0
    summary.update(reward=reward, target_passed="%d/%d" % (t_ok, t_all),
                   guard_passed="%d/%d" % (g_ok, g_all))
    if verbose:
        summary["sample_failures"] = failures
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--workspace", required=True,
                    help="directory containing inflection/__init__.py")
    ap.add_argument("--tests-dir",
                    default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--reward-file")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--sandbox-user")
    args = ap.parse_args(argv)

    summary = grade(args.workspace, args.tests_dir, args.seed,
                    args.sandbox_user)
    _write_reward(args.reward_file, summary["reward"])
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
