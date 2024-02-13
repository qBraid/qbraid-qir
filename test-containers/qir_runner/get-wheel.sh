#!/bin/bash

REPO="qir-alliance/pyqir"

# Fetch the latest release asset URLs
urls=$(curl -s https://api.github.com/repos/$REPO/releases/latest)
if [ $? -ne 0 ]; then
    echo "Error fetching the latest release information."
    exit 1
fi

# Check if the response contains assets
if ! echo "$urls" | jq -e '.assets[]' > /dev/null; then
    echo "No assets found in the latest release."
    exit 1
fi

urls=$(echo "$urls" | jq -r '.assets[] | .browser_download_url')

# Filter for the manylinux wheel URL
manylinux_url=$(echo "$urls" | grep 'manylinux')
if [[ -z "$manylinux_url" ]]; then
    echo "Manylinux wheel not found."
    exit 1
fi

# Downloads the file with curl
filename=$(basename "$manylinux_url")
curl -L -o "$filename" "$manylinux_url"
if [ $? -ne 0 ]; then
    echo "Error downloading the file."
    exit 1
fi

echo "Downloaded $filename successfully."
