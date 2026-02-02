#!/bin/bash
# MySpeech Installer
# Downloads and installs MySpeech, bypassing Gatekeeper
#
# Usage: install.sh [--force|-f] [--dir|-d <path>]
#   --force, -f        Force reinstall even if same version is installed
#   --dir, -d <path>   Install to a custom directory instead of /Applications

set -e

# Parse arguments
FORCE=false
INSTALL_DIR="/Applications"
while [[ $# -gt 0 ]]; do
    case $1 in
        --force|-f)
            FORCE=true
            shift
            ;;
        --dir|-d)
            INSTALL_DIR="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

APP_NAME="MySpeech"
REPO="antonpetrovmain/myspeech"

echo "Installing $APP_NAME..."

# Create install dir if it doesn't exist
mkdir -p "$INSTALL_DIR"

# Check if we need sudo
NEEDS_SUDO=false
if [ ! -w "$INSTALL_DIR" ]; then
    NEEDS_SUDO=true
    echo "Administrator privileges required to install to $INSTALL_DIR"
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
RELEASE_URL=$(curl -s "https://api.github.com/repos/$REPO/releases/latest" | grep "browser_download_url.*\.zip" | cut -d '"' -f 4)

if [ -z "$RELEASE_URL" ]; then
    echo "Error: Could not find latest release"
    exit 1
fi

# Extract version from filename (e.g., MySpeech-v0.3.0.zip)
NEW_VERSION=$(echo "$RELEASE_URL" | sed -n 's/.*MySpeech-v\([0-9.]*\).*\.zip/\1/p')

# Check currently installed version
CURRENT_VERSION="not installed"
if [ -d "$INSTALL_DIR/$APP_NAME.app" ]; then
    PLIST="$INSTALL_DIR/$APP_NAME.app/Contents/Info.plist"
    if [ -f "$PLIST" ]; then
        CURRENT_VERSION=$(defaults read "$PLIST" CFBundleShortVersionString 2>/dev/null || echo "unknown")
    fi
fi

echo "Current version: $CURRENT_VERSION"
echo "Installing version: $NEW_VERSION"

# Skip if already up to date (unless --force)
if [ "$CURRENT_VERSION" = "$NEW_VERSION" ] && [ "$FORCE" = false ]; then
    echo "Already up to date! Use --force to reinstall."
    rm -rf "$TEMP_DIR"
    exit 0
fi

# Download latest release
echo "Downloading..."
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
echo "Run with: open $INSTALL_DIR/MySpeech.app"
