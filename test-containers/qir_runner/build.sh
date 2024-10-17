#!/bin/bash

CONTAINER_NAME=$1

docker build --platform linux/amd64 -t qbraid-qir .

if [ $? -ne 0 ]; then
  echo "Error: Docker build failed."
  exit 1
fi

if [ -z "$QBRAID_API_KEY" ]; then
  echo "Warning: QBRAID_API_KEY environment variable is not set. The container may not have access to the qBraid Quantum Jobs API."
fi

if [ -n "$CONTAINER_NAME" ]; then
  if [ "$(docker ps -a -q -f name=$CONTAINER_NAME)" ]; then
    echo "Removing existing container $CONTAINER_NAME..."
    docker rm -f $CONTAINER_NAME
  fi

  docker run --platform linux/amd64 --name $CONTAINER_NAME -e QBRAID_API_KEY=$QBRAID_API_KEY qbraid-qir tail -f /dev/null > /dev/null 2>&1
else
  docker run --platform linux/amd64 -e QBRAID_API_KEY=$QBRAID_API_KEY qbraid-qir tail -f /dev/null > /dev/null 2>&1
fi
