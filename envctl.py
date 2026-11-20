#!/usr/bin/env python3
"""Local driver for the inflection-repair environment (no Docker needed).

    python envctl.py list                      # list tasks
    python envctl.py reset  <task>             # fresh workspace in workspaces/<task>
    python envctl.py grade  <task> [--workspace DIR] [--seed N]
    python envctl.py oracle <task>             # apply the reference fix, then grade
    python envctl.py baseline                  # grade every untouched task

The workspace is what an agent edits (it mirrors /app in the container).
Grading here runs the same tests/grade.py the Docker verifier runs, minus the
unprivileged sandbox user, which needs root inside a container.
"""
import argparse
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TASKS = os.path.join(ROOT, "tasks")
WORKSPACES = os.path.join(ROOT, "workspaces")


def task_names():
    return sorted(d for d in os.listdir(TASKS)
                  if os.path.isfile(os.path.join(TASKS, d, "task.toml")))


def reset(task):
    src = os.path.join(TASKS, task, "environment", "app")
    dst = os.path.join(WORKSPACES, task)
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    return dst


def grade(task, workspace=None, seed=None):
    tests_dir = os.path.join(TASKS, task, "tests")
    sys.path.insert(0, tests_dir)
    try:
        import importlib
        grade_mod = importlib.import_module("grade")
        importlib.reload(grade_mod)
    finally:
        sys.path.pop(0)
    workspace = workspace or os.path.join(WORKSPACES, task)
    return grade_mod.grade(workspace, tests_dir, seed=seed)


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sub.add_parser("baseline")
    for name in ("reset", "oracle"):
        sub.add_parser(name).add_argument("task")
    g = sub.add_parser("grade")
    g.add_argument("task")
    g.add_argument("--workspace")
    g.add_argument("--seed", type=int)
    args = ap.parse_args(argv)

    if args.cmd == "list":
        for name in task_names():
            print(name)
    elif args.cmd == "reset":
        print("workspace ready:", reset(args.task))
        print("instructions:", os.path.join(TASKS, args.task, "instruction.md"))
    elif args.cmd == "grade":
        ws = os.path.abspath(args.workspace) if args.workspace else None
        print(json.dumps(grade(args.task, ws, args.seed), indent=2,
                         ensure_ascii=False))
    elif args.cmd == "oracle":
        ws = reset(args.task)
        shutil.copyfile(
            os.path.join(TASKS, args.task, "solution", "inflection_fixed.py"),
            os.path.join(ws, "inflection", "__init__.py"))
        print(json.dumps(grade(args.task, ws), indent=2, ensure_ascii=False))
    elif args.cmd == "baseline":
        for name in task_names():
            ws = reset(name)
            res = grade(name, ws)
            print("%-28s reward=%.3f target=%s guard=%s" % (
                name, res["reward"], res.get("target_passed"),
                res.get("guard_passed")))


if __name__ == "__main__":
    main()
