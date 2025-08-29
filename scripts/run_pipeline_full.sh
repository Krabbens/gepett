#!/bin/bash
set -e

# This script starts the main Gepett agent pipeline in FULL mode (with vision).
# It executes the main Python script inside the 'core' Docker container.

echo ">>> Starting Gepett pipeline in FULL (Vision-Enabled) mode..."

# This command will run the main script with a config that enables vision processing.
PIPELINE_COMMAND="python -m gepett.adapter.mc_adapter --config gepett/config/defaults.yaml --config gepett/config/cuda_full.yaml"

# Using `docker compose exec` to run the command in the already-running 'core' service.
docker compose exec core bash -c "$PIPELINE_COMMAND"

echo ">>> Pipeline script finished."
