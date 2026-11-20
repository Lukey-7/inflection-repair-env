#!/bin/bash
# Harbor verifier entry point. Runs after the agent has finished.
# Writes a single float reward to /logs/verifier/reward.txt.
set -u
mkdir -p /logs/verifier
rm -f /logs/verifier/reward.txt

# The submission is executed as 'nobody'. Make the hidden tests (including the
# reference implementation) unreadable to it, so it cannot copy the oracle.
chmod -R go-rwx /tests

python3 /tests/grade.py \
  --workspace /app \
  --tests-dir /tests \
  --reward-file /logs/verifier/reward.txt \
  --sandbox-user nobody

# A crashed grader must never leave the reward missing or stale.
if [ ! -s /logs/verifier/reward.txt ]; then
  echo 0 > /logs/verifier/reward.txt
fi
