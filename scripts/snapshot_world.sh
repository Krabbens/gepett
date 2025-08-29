#!/bin/bash
set -e

# This script creates a snapshot of the current Minecraft world.
# Snapshots are stored in the `worlds_snapshots` directory.

# --- Configuration ---
SOURCE_WORLD_DIR="../server/world"
SNAPSHOTS_BASE_DIR="../worlds_snapshots"

# --- Logic ---
SNAPSHOT_ID=${1:-$(uuidgen)} # Use provided argument or generate a new UUID
DESTINATION_DIR="$SNAPSHOTS_BASE_DIR/$SNAPSHOT_ID"

echo ">>> Creating world snapshot..."

if [ ! -d "$SOURCE_WORLD_DIR" ]; then
    echo "!!! Source world directory not found at '$SOURCE_WORLD_DIR'. Has the server been started at least once?"
    exit 1
fi

mkdir -p "$DESTINATION_DIR"

echo ">>> Copying '$SOURCE_WORLD_DIR' to '$DESTINATION_DIR'..."
# Using rsync is often faster and more robust for large directories
rsync -a --delete "$SOURCE_WORLD_DIR/" "$DESTINATION_DIR"

if [ $? -eq 0 ]; then
    echo ">>> Snapshot successful. ID: $SNAPSHOT_ID"
    echo ">>> Location: $DESTINATION_DIR"
else
    echo "!!! Snapshot failed."
    exit 1
fi
