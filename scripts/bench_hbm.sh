#!/bin/bash
set -e

# This script runs a benchmark for the Hierarchical Buffer Memory (HBM) learner.
# It measures the data throughput across different tiers (VRAM, RAM, NVMe).

echo ">>> Starting HBM Learner benchmark..."

# The command to execute inside the container.
# It calls a dedicated benchmark script.
BENCHMARK_COMMAND="python -m tests.test_hbm_replay" # Using the test as a placeholder for the bench

# Using `docker compose exec` to run the command in the already-running 'core' service.
docker compose exec core bash -c "$BENCHMARK_COMMAND"

echo ">>> Benchmark script finished."
