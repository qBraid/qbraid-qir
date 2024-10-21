#!/bin/bash

# Copyright (C) 2024 qBraid Development Team.
# Distributed under terms of the GNU General Public License v3.

CONTAINER_NAME=$1

if [ -n "$CONTAINER_NAME" ]; then
  if [ "$(docker ps -a -q -f name=$CONTAINER_NAME)" ]; then
    echo "Removing existing container $CONTAINER_NAME..."
    docker rm -f $CONTAINER_NAME
  fi

  echo "Starting container $CONTAINER_NAME in detached mode..."
  docker run --platform linux/amd64 --name $CONTAINER_NAME -d qbraid/qir-runner tail -f /dev/null > /dev/null 2>&1
  echo "Container $CONTAINER_NAME started in detached mode."
else
  echo "Starting unnamed container in detached mode..."
  CONTAINER_ID=$(docker run --platform linux/amd64 -d qbraid/qir-runner tail -f /dev/null > /dev/null 2>&1)
  echo "Started container with ID: $CONTAINER_ID in detached mode."
fi
