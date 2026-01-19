#!/bin/bash
# MySpeech Installer
# Downloads and installs MySpeech, bypassing Gatekeeper

set -e

APP_NAME="MySpeech"
INSTALL_DIR="/Applications"
REPO="antonpetrovmain/myspeech"

echo "Installing $APP_NAME..."

# Check if we need sudo for /Applications
NEEDS_SUDO=false
if [ ! -w "$INSTALL_DIR" ] || [ -d "$INSTALL_DIR/$APP_NAME.app" ]; then
    NEEDS_SUDO=true
    echo "Administrator privileges required to install to /Applications"
fi

# Helper to run commands with sudo if needed
run_cmd() {
    if [ "$NEEDS_SUDO" = true ]; then
        sudo "$@"
    else
        "$@"
    fi
}

# Create temp directory
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Get latest release download URL
echo "Finding latest release..."
RELEASE_URL=$(curl -s "https://api.github.com/repos/$REPO/releases/latest" | grep "browser_download_url.*macos-arm64.zip" | cut -d '"' -f 4)

if [ -z "$RELEASE_URL" ]; then
    echo "Error: Could not find latest release"
    exit 1
fi

# Download latest release
echo "Downloading from $RELEASE_URL..."
curl -L -o myspeech.zip "$RELEASE_URL"

# Extract
echo "Extracting..."
unzip -q myspeech.zip

# Remove old version if exists
if [ -d "$INSTALL_DIR/$APP_NAME.app" ]; then
    echo "Removing old version..."
    run_cmd rm -rf "$INSTALL_DIR/$APP_NAME.app"
fi

# Move to Applications
echo "Installing to $INSTALL_DIR..."
run_cmd mv "$APP_NAME.app" "$INSTALL_DIR/"

# Remove quarantine attribute (bypasses Gatekeeper)
echo "Removing quarantine..."
run_cmd xattr -cr "$INSTALL_DIR/$APP_NAME.app"

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "Done! MySpeech installed to $INSTALL_DIR/$APP_NAME.app"
echo ""
echo "NOTE: You need to grant Accessibility permission:"
echo "  System Settings > Privacy & Security > Accessibility > Add MySpeech"
echo ""
echo "Run with: open /Applications/MySpeech.app"
