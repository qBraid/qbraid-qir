#!/bin/bash

# Copyright (C) 2024 qBraid Development Team.
# Distributed under terms of the GNU General Public License v3.

CONTAINER_NAME=$1

if [ -n "$CONTAINER_NAME" ]; then
  echo "Entering container $CONTAINER_NAME..."
  docker exec -it $CONTAINER_NAME /bin/bash
else
  echo "Please provide the container name to exec into."
  echo "Usage: ./entrypoint.sh <container_name>"
fi
