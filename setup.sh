#!/bin/bash

# Get the directory of this script
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# Define the path to the virtual environment
VENV_PATH="$SCRIPT_DIR/venv"

# Create the virtual environment if it doesn't exist
if [ ! -d "$VENV_PATH" ]; then
  python3 -m venv "$VENV_PATH"
fi

# Activate the virtual environment
source "$VENV_PATH/bin/activate"

# Install the required Python packages
pip install -r "$SCRIPT_DIR/requirements.txt"

