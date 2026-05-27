#!/bin/bash
#
# build.sh — Production-quality build script for the CosURLHandler.app bundle.
#
# Usage (from within macos-helper/ directory or via `cos setup-macos-handler`):
#   ./build.sh
#   ./build.sh --clean
#   ./build.sh --install          # also copies to ~/Applications and registers
#
# Requirements:
#   - Xcode Command Line Tools (swiftc, codesign, lipo, etc.)
#   - macOS 11+ SDK (for the minimum deployment target in the source)
#
# Output:
#   build/CosURLHandler.app   (ready to copy to /Applications or ~/Applications)
#
# The resulting app:
#   - Is ad-hoc signed (sufficient for local / personal distribution)
#   - Declares the cos:// URL scheme
#   - Runs as a background accessory app (LSUIElement)
#   - Self-terminates after handling a URL
#
# For universal binary (Apple Silicon + Intel) you can extend this script with
# two swiftc invocations + lipo. Current default: native architecture only.
# This is perfect for personal use and keeps the script simple and fast.
#
# After build, the .app can be opened manually or via LaunchServices (any cos:// link).
# See macos-helper/README.md and the root README for one-time setup and Ghostty tips.

set -euo pipefail

# --- Configuration -----------------------------------------------------------

APP_NAME="CosURLHandler.app"
BUNDLE_ID="com.wedge.cos-url-handler"
MIN_MACOS="11.0"

# Source layout (relative to this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_FILE="$SCRIPT_DIR/Sources/CosURLHandler.swift"
INFO_PLIST="$SCRIPT_DIR/Info.plist"

# Output
BUILD_DIR="$SCRIPT_DIR/build"
APP_BUNDLE="$BUILD_DIR/$APP_NAME"
EXECUTABLE_PATH="$APP_BUNDLE/Contents/MacOS/CosURLHandler"

# --- Helpers -----------------------------------------------------------------

log() {
    printf '\033[1;36m[build]\033[0m %s\n' "$*"
}

err() {
    printf '\033[1;31m[build error]\033[0m %s\n' "$*" >&2
}

die() {
    err "$*"
    exit 1
}

# --- Argument Parsing --------------------------------------------------------

CLEAN=0
INSTALL=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --clean)
            CLEAN=1
            shift
            ;;
        --install)
            INSTALL=1
            shift
            ;;
        -h|--help)
            cat <<'EOF'
CosURLHandler build script

  ./build.sh                 Build the .app bundle (default)
  ./build.sh --clean         Clean previous build then build
  ./build.sh --install       Build + copy to ~/Applications + register scheme

The resulting app is ad-hoc signed and ready for personal use.
See README.md for full installation and Ghostty profile recommendations.
EOF
            exit 0
            ;;
        *)
            die "Unknown argument: $1 (try --help)"
            ;;
    esac
done

# --- Clean -------------------------------------------------------------------

if [[ $CLEAN -eq 1 ]]; then
    log "Cleaning previous build..."
    rm -rf "$BUILD_DIR"
fi

# --- Prepare Directories -----------------------------------------------------

mkdir -p "$APP_BUNDLE/Contents/MacOS" "$APP_BUNDLE/Contents/Resources"

# --- Compile Swift -----------------------------------------------------------

log "Compiling CosURLHandler.swift (deployment target macOS $MIN_MACOS)..."

# Use the host architecture (arm64 or x86_64). For a personal tool this is ideal.
# Add -target x86_64-apple-macos$MIN_MACOS or universal logic if you need it later.
SWIFT_TARGET="$(uname -m)-apple-macos$MIN_MACOS"

swiftc \
    -O \
    -parse-as-library \
    -target "$SWIFT_TARGET" \
    -o "$EXECUTABLE_PATH" \
    "$SRC_FILE"

log "Compiled executable: $EXECUTABLE_PATH"

# --- Assemble Bundle ---------------------------------------------------------

log "Assembling app bundle..."

cp "$INFO_PLIST" "$APP_BUNDLE/Contents/Info.plist"

# (Optional) Add a minimal icon here in the future:
# cp "$SCRIPT_DIR/Resources/AppIcon.icns" "$APP_BUNDLE/Contents/Resources/" || true

# Make sure the binary is executable (swiftc usually does this, but be explicit)
chmod +x "$EXECUTABLE_PATH"

# --- Ad-hoc Code Signing (required on modern macOS) --------------------------

log "Ad-hoc code signing the bundle..."

codesign --force --deep --sign - "$APP_BUNDLE"

# Verify the signature (informational)
codesign --verify --deep --strict --verbose=2 "$APP_BUNDLE" 2>&1 | head -5 || true

# --- Success -----------------------------------------------------------------

log "✅ Build complete: $APP_BUNDLE"
log ""
log "Bundle contents:"
find "$APP_BUNDLE" -type f | sort

log ""
log "To install for development / one-time use:"
log "  cp -r '$APP_BUNDLE' ~/Applications/"
log "  open ~/Applications/$APP_NAME"
log ""
log "Then test with:"
log "  open 'cos://brief'"
log "  open 'cos://research?ticker=NVDA'"
log ""
log "Or run the binary directly for CLI testing:"
log "  '$EXECUTABLE_PATH' --help"
log "  '$EXECUTABLE_PATH' 'cos://capture'"

# --- Optional Install Step ---------------------------------------------------

if [[ $INSTALL -eq 1 ]]; then
    log ""
    log "Installing to ~/Applications and registering with Launch Services..."

    mkdir -p ~/Applications
    rm -rf "~/Applications/$APP_NAME" 2>/dev/null || true
    cp -R "$APP_BUNDLE" ~/Applications/

    # Force Launch Services to notice the new handler
    /System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister \
        -f "~/Applications/$APP_NAME" || true

    open "~/Applications/$APP_NAME"

    log "✅ Installed to ~/Applications/$APP_NAME"
    log "The cos:// scheme is now registered. Trigger a link from the dashboard or run:"
    log "  open 'cos://dashboard'"
fi

log ""
log "Done."