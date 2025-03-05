#!/bin/bash

# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

################################################################################
# Description:
# Finds and installs the first .whl file in a specified directory including
# specified extras. The directory path is passed as the first argument.
# Extras are specified with --extra flags.
#
# Example Usage:
#   ./install_wheel_extras.sh ./dist --extra qasm3 --extra cirq
#   ./install_wheel_extras.sh ./dist --extra qasm3
#   ./install_wheel_extras.sh ./dist
################################################################################

# Check if at least one argument (the directory path) is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <directory> [--extra <extra>...]"
    exit 1
fi

# The first argument is the directory path
DIST=$1
shift # Remove the directory path from the arguments list

# Initialize extras array
EXTRAS=()

# Parse remaining arguments for --extra flags
while (( "$#" )); do
    case "$1" in
        --extra)
            EXTRAS+=($2)
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Combine extras into a comma-separated string
EXTRAS_STR=$(IFS=, ; echo "${EXTRAS[*]}")

# Use ls and grep to find the first .whl file
WHEEL_FILE=$(ls $DIST | grep '\.whl$' | head -n 1)

if [ -z "$WHEEL_FILE" ]; then
    echo "No .whl file found in the specified directory."
    exit 1
else
    echo "Wheel file found: $WHEEL_FILE"
fi

# Build the pip install command with extras, if provided
if [ -n "$EXTRAS_STR" ]; then
    INSTALL_COMMAND="python3 -m pip install '$DIST/$WHEEL_FILE[$EXTRAS_STR]'"
else
    INSTALL_COMMAND="python3 -m pip install '$DIST/$WHEEL_FILE'"
fi

# Execute the pip install command
echo "Executing: $INSTALL_COMMAND"
eval $INSTALL_COMMAND
