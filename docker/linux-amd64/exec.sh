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
  echo "Entering container $CONTAINER_NAME..."
  docker exec -it $CONTAINER_NAME /bin/bash
else
  echo "Please provide the container name to exec into."
  echo "Usage: ./entrypoint.sh <container_name>"
fi
