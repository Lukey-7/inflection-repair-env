#!/usr/bin/env python3
"""Verify a task end to end in Docker without Harbor.

    python tools/docker_check.py fix-ordinal                 # untouched -> expect 0
    python tools/docker_check.py fix-ordinal --oracle        # expect 1
    python tools/docker_check.py fix-ordinal --exploit e4    # expect 0 in Docker
    python tools/docker_check.py fix-ordinal --workspace DIR # grade any workspace

It builds tasks/<task>/environment, copies the workspace into /app and the
hidden tests into /tests (copied, not bind-mounted, so test.sh's chmod works
on Docker Desktop too), runs tests/test.sh as root exactly as the Harbor
verifier would, and prints the reward.
"""
import argparse
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "exploits"))
import envctl  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task")
    ap.add_argument("--oracle", action="store_true")
    ap.add_argument("--exploit", choices=["e1", "e2", "e3", "e4"])
    ap.add_argument("--workspace")
    args = ap.parse_args()

    tdir = os.path.join(envctl.TASKS, args.task)
    if args.workspace:
        ws = os.path.abspath(args.workspace)
    else:
        ws = envctl.reset(args.task)
        if args.oracle:
            shutil.copyfile(os.path.join(tdir, "solution", "inflection_fixed.py"),
                            os.path.join(ws, "inflection", "__init__.py"))
        if args.exploit:
            import run_exploits as rx
            tamper = {"e1": rx.e1_edit_tests, "e2": rx.e2_hardcode,
                      "e3": rx.e3_conftest,
                      "e4": rx.e4_read_oracle(args.task)}[args.exploit]
            tamper(ws)

    image = "irenv-" + args.task
    subprocess.run(["docker", "build", "-q", "-t", image,
                    os.path.join(tdir, "environment")], check=True)
    script = ("rm -rf /app/* && cp -r /ws_src/. /app/ && "
              "cp -r /tests_src /tests && bash /tests/test.sh && "
              "echo REWARD=$(cat /logs/verifier/reward.txt)")
    subprocess.run(["docker", "run", "--rm", "--network", "none",
                    "-v", "%s:/ws_src:ro" % ws,
                    "-v", "%s:/tests_src:ro" % os.path.join(tdir, "tests"),
                    image, "bash", "-c", script], check=True)


if __name__ == "__main__":
    main()
