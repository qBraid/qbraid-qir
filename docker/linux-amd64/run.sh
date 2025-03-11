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
  echo "Starting container in detached mode..."
  docker run --platform linux/amd64 -d qbraid/qir-runner tail -f /dev/null > /dev/null 2>&1
  echo "Container started in detached mode."
fi
