#!/usr/bin/env bash
set -euo pipefail

APP_NAME="OurMoney"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ -n "${PYTHON:-}" ]]; then
    PYTHON="$PYTHON"
elif [[ -x "$SCRIPT_DIR/env/bin/python" ]]; then
    PYTHON="$SCRIPT_DIR/env/bin/python"
elif [[ -x "$SCRIPT_DIR/.venv/bin/python" ]]; then
    PYTHON="$SCRIPT_DIR/.venv/bin/python"
else
    PYTHON="python3"
fi
DIST_DIR="$SCRIPT_DIR/dist"
APP_BUNDLE_PATH="$DIST_DIR/${APP_NAME}.app"
ICON_FILE="$SCRIPT_DIR/assets/logo_icon.icns"
DMG_OUTPUT_FILE="$DIST_DIR/${APP_NAME}-Installer.dmg"

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "Error: The macOS installer must be built on macOS." >&2
    exit 1
fi

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "Error: Python interpreter '$PYTHON' was not found. Set PYTHON to the desired interpreter." >&2
    exit 1
fi

if ! "$PYTHON" -m PyInstaller --version >/dev/null 2>&1; then
    echo "Error: PyInstaller is not installed for '$PYTHON'." >&2
    echo "Install the build dependency with: $PYTHON -m pip install -r requirements-build.txt" >&2
    exit 1
fi

if ! command -v create-dmg >/dev/null 2>&1; then
    echo "Error: create-dmg is not installed. Install it with: brew install create-dmg" >&2
    exit 1
fi

if [[ ! -f "$ICON_FILE" ]]; then
    echo "Error: App icon not found at $ICON_FILE" >&2
    exit 1
fi

"$PYTHON" -m PyInstaller --noconfirm --clean --distpath "$DIST_DIR" app.spec

if [[ ! -d "$APP_BUNDLE_PATH" ]]; then
    echo "Error: PyInstaller completed without creating $APP_BUNDLE_PATH" >&2
    exit 1
fi

STAGING_DIR="$(mktemp -d "${TMPDIR:-/tmp}/${APP_NAME}-dmg.XXXXXX")"
DMG_BUILD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/${APP_NAME}-dmg-output.XXXXXX")"
DMG_BUILD_FILE="$DMG_BUILD_DIR/${APP_NAME}-Installer.dmg"
trap 'rm -rf -- "$STAGING_DIR" "$DMG_BUILD_DIR"' EXIT
ditto "$APP_BUNDLE_PATH" "$STAGING_DIR/${APP_NAME}.app"

echo "Creating DMG installer..."
create-dmg \
    --volname "${APP_NAME} Installer" \
    --volicon "$ICON_FILE" \
    --window-pos 200 120 \
    --window-size 600 400 \
    --icon-size 100 \
    --icon "${APP_NAME}.app" 150 190 \
    --hide-extension "${APP_NAME}.app" \
    --app-drop-link 450 190 \
    "$DMG_BUILD_FILE" \
    "$STAGING_DIR"

mv -f -- "$DMG_BUILD_FILE" "$DMG_OUTPUT_FILE"
echo "Successfully created DMG: $DMG_OUTPUT_FILE"