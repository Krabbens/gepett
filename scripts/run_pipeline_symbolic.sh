#!/bin/bash
set -e

# This script starts the main Gepett agent pipeline in symbolic-only mode.
# It executes the main Python script inside the 'core' Docker container.

echo ">>> Starting Gepett pipeline in SYMBOLIC mode..."

# The command to execute inside the container.
# This will eventually be the main training/evaluation script.
# For now, we can use a placeholder that runs a component, e.g., the adapter.
# The actual main script would take configuration files as arguments.
PIPELINE_COMMAND="python -m gepett.adapter.mc_adapter --config gepett/config/defaults.yaml --config gepett/config/cuda_light.yaml"

# Using `docker compose exec` to run the command in the already-running 'core' service.
docker compose exec core bash -c "$PIPELINE_COMMAND"

echo ">>> Pipeline script finished."
