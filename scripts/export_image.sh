#!/usr/bin/env bash

CONTAINER_NAME="vsc-gazebo-simulations"
OUTPUT_DIR="images"
OUTPUT_FILE="$OUTPUT_DIR/trickfire-sim.tar"

# Find container ID by image name
CONTAINER_ID=$(
    docker ps --format "{{.ID}} {{.Image}}" |
        grep "^.* $CONTAINER_NAME" |
        awk '{print $1}' |
        head -n 1
)

echo "Container ID: $CONTAINER_ID"

if [ -z "$CONTAINER_ID" ]; then
    echo "Error: Container not found."
    exit 1
fi

# Get the image ID from the container
IMAGE_ID=$(docker inspect --format='{{.Image}}' "$CONTAINER_ID")

if [ -z "$IMAGE_ID" ]; then
    echo "Error: Could not retrieve image ID."
    exit 1
fi

# Ensure output directory exists
if [ ! -d "$OUTPUT_DIR" ]; then
    mkdir -p "$OUTPUT_DIR"
fi

# Export image
echo "Saving image $IMAGE_ID to $OUTPUT_FILE ..."
docker save -o "$OUTPUT_FILE" "$IMAGE_ID"

echo "Done"
