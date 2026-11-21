#!/usr/bin/env python3
"""Minimal free agent loop: a local Ollama model works on one task workspace.

    ollama pull qwen2.5-coder:7b
    python agent/mini_agent.py fix-ordinal --model qwen2.5-coder:7b

The model answers each turn with ONE JSON action:
    {"action": "list"}
    {"action": "read",  "path": "inflection/__init__.py"}
    {"action": "write", "path": "inflection/__init__.py", "content": "..."}
    {"action": "replace", "path": "...", "old": "...", "new": "..."}
    {"action": "test"}                     # runs the VISIBLE tests only
    {"action": "done"}
After "done" (or the step limit) the hidden grader scores the workspace.
Transcripts go to runs/<task>-<timestamp>.jsonl. Standard library only.

Tested with qwen2.5-coder:3b on CPU (see docs/RESULTS.md).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import envctl  # noqa: E402

SYSTEM = """You are a software engineer fixing a Python library.
You act by replying with exactly ONE JSON object and nothing else.
Actions:
  {"action": "list"}
  {"action": "read", "path": "<relative path>"}
  {"action": "replace", "path": "<relative path>", "old": "<exact text>", "new": "<text>"}
  {"action": "write", "path": "<relative path>", "content": "<full file>"}
  {"action": "test"}   (runs the visible tests)
  {"action": "done"}   (when you are finished)
Prefer "replace" for small edits."""


def chat(model, messages, host):
    body = json.dumps({"model": model, "messages": messages, "stream": False,
                       "format": "json",
                       # Ollama defaults to a 4096-token context, smaller than
                       # the library file itself; without this the model
                       # silently sees a truncated file.
                       "options": {"temperature": 0.2, "num_ctx": 16384}}
                      ).encode()
    req = urllib.request.Request(host + "/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read())["message"]["content"]


def safe_path(ws, rel):
    path = os.path.realpath(os.path.join(ws, rel))
    if not path.startswith(os.path.realpath(ws) + os.sep):
        raise ValueError("path escapes workspace")
    return path


def act(ws, action):
    kind = action.get("action")
    if kind == "list":
        out = []
        for d, _, files in os.walk(ws):
            for f in files:
                if "__pycache__" not in d:
                    out.append(os.path.relpath(os.path.join(d, f), ws))
        return "\n".join(sorted(out))
    if kind == "read":
        with open(safe_path(ws, action["path"]), encoding="utf-8") as fh:
            return fh.read()
    if kind == "write":
        with open(safe_path(ws, action["path"]), "w", encoding="utf-8") as fh:
            fh.write(action["content"])
        return "written"
    if kind == "replace":
        path = safe_path(ws, action["path"])
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        n = text.count(action["old"])
        if n != 1:
            return "error: 'old' text found %d times, need exactly 1" % n
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text.replace(action["old"], action["new"]))
        return "replaced"
    if kind == "test":
        proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"],
                              cwd=ws, capture_output=True, text=True,
                              timeout=120)
        return (proc.stdout + proc.stderr)[-3000:]
    return "error: unknown action"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task")
    ap.add_argument("--model", default="qwen2.5-coder:7b")
    ap.add_argument("--host", default="http://localhost:11434")
    ap.add_argument("--max-steps", type=int, default=25)
    args = ap.parse_args()

    ws = envctl.reset(args.task)
    with open(os.path.join(envctl.TASKS, args.task, "instruction.md"),
              encoding="utf-8") as fh:
        instruction = fh.read().replace("/app/", "").replace("/app", ".")
    os.makedirs(os.path.join(ROOT, "runs"), exist_ok=True)
    log_path = os.path.join(ROOT, "runs", "%s-%d.jsonl" % (args.task,
                                                           time.time()))
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": instruction}]
    with open(log_path, "w", encoding="utf-8") as log:
        for step in range(args.max_steps):
            reply = chat(args.model, messages, args.host)
            messages.append({"role": "assistant", "content": reply})
            try:
                action = json.loads(reply)
            except ValueError:
                m = re.search(r"\{.*\}", reply, re.S)
                action = json.loads(m.group(0)) if m else {}
            if action.get("action") == "done":
                log.write(json.dumps({"step": step, "action": action}) + "\n")
                break
            try:
                obs = act(ws, action)
            except Exception as exc:
                obs = "error: %s" % exc
            log.write(json.dumps({"step": step, "action": action,
                                  "observation": obs[:2000]}) + "\n")
            log.flush()
            messages.append({"role": "user", "content": obs})
        result = envctl.grade(args.task, ws)
        log.write(json.dumps({"grade": result}) + "\n")
    print(json.dumps({"task": args.task, "model": args.model,
                      "steps": step + 1, "reward": result["reward"],
                      "target": result.get("target_passed"),
                      "guard": result.get("guard_passed"),
                      "log": log_path}, indent=2))


if __name__ == "__main__":
    main()
