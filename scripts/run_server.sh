#!/bin/bash
set -e

# This script is designed to run inside the 'paper' Docker container.
# It ensures necessary tools are installed, downloads PaperMC if needed, and starts the server.

# --- Configuration ---
MINECRAFT_VERSION="1.21" # The target Minecraft version
JAR_NAME="paper.jar"
PAPER_API_URL="https://api.papermc.io/v2/projects/paper"
USER_AGENT="GepettAgent/1.0 (https://github.com/user/gepett-cuda-headless)" # A valid User-Agent is required by the API

# --- Ensure Tools ---
# The base image might not have curl and jq, so install them if missing.
if ! command -v curl &> /dev/null || ! command -v jq &> /dev/null; then
    echo ">>> Installing curl and jq..."
    apt-get update && apt-get install -y curl jq --no-install-recommends && rm -rf /var/lib/apt/lists/*
fi

# --- Download PaperMC ---
if [ ! -f "$JAR_NAME" ]; then
    echo ">>> '$JAR_NAME' not found. Downloading PaperMC for Minecraft $MINECRAFT_VERSION..."

    # Get the latest build number for the specified Minecraft version
    LATEST_BUILD=$(curl -s -H "User-Agent: $USER_AGENT" "$PAPER_API_URL/versions/$MINECRAFT_VERSION/builds" | jq -r '.builds[-1].build')

    if [ -z "$LATEST_BUILD" ] || [ "$LATEST_BUILD" == "null" ]; then
        echo "!!! Could not find a build for Minecraft $MINECRAFT_VERSION. Exiting."
        exit 1
    fi

    echo ">>> Latest build is #$LATEST_BUILD. Constructing download URL..."
    DOWNLOAD_URL="$PAPER_API_URL/versions/$MINECRAFT_VERSION/builds/$LATEST_BUILD/downloads/paper-$MINECRAFT_VERSION-$LATEST_BUILD.jar"

    echo ">>> Downloading from $DOWNLOAD_URL..."
    curl -o "$JAR_NAME" -L -H "User-Agent: $USER_AGENT" "$DOWNLOAD_URL"

    if [ $? -ne 0 ]; then
        echo "!!! Download failed. Please check the version and API."
        exit 1
    fi
    echo ">>> Download complete."
else
    echo ">>> '$JAR_NAME' already exists. Skipping download."
fi

# --- EULA Agreement ---
# The EULA is handled by mounting the file, but we can double-check.
if [ "$MINECRAFT_EULA" != "TRUE" ] && [ ! -f "eula.txt" ]; then
    echo "!!! EULA has not been accepted. Set MINECRAFT_EULA=TRUE environment variable or provide eula.txt."
    exit 1
elif [ ! -f "eula.txt" ]; then
     echo "eula=true" > eula.txt
fi


# --- Start Server ---
echo ">>> Starting Minecraft server..."
# Using 2GB of RAM, running in nogui mode for headless operation.
exec java -Xms2G -Xmx2G -jar "$JAR_NAME" --nogui
