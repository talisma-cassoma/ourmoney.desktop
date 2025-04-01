
# Run PyInstaller to Create the .app Bundle
pyinstaller app.spec 

# --- Prerequisites ---
# 1. Ensure 'create-dmg' is installed:
#    brew install create-dmg
# 2. Ensure your working '.app' bundle exists in the 'dist' folder.
#    Example: 'dist/OurMoney.app'

# --- Define Variables (Makes the command cleaner) ---
APP_NAME="OurMoney" # IMPORTANT: Change this if your .app file has a different name
APP_BUNDLE_PATH="dist/${APP_NAME}.app"
ICON_FILE="assets/logo_icon.icns"
DMG_OUTPUT_FILE="dist/${APP_NAME}-Installer.dmg"
SOURCE_FOLDER="dist" # The folder containing your .app bundle

# --- Check if App Bundle and Icon Exist ---
if [ ! -d "${APP_BUNDLE_PATH}" ]; then
    echo "Error: Application bundle not found at ${APP_BUNDLE_PATH}"
    echo "Make sure you ran PyInstaller successfully and check the APP_NAME variable."
    exit 1
fi

if [ ! -f "${ICON_FILE}" ]; then
    echo "Error: Icon file not found at ${ICON_FILE}"
    exit 1
fi

echo "Creating DMG installer..."

# --- Run create-dmg ---
create-dmg \
  --volname "${APP_NAME} Installer" \
  --volicon "${ICON_FILE}" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "${APP_NAME}.app" 150 190 \
  --hide-extension "${APP_NAME}.app" \
  --app-drop-link 450 190 \
  "${DMG_OUTPUT_FILE}" \
  "${SOURCE_FOLDER}/"

# --- Confirmation ---
if [ $? -eq 0 ]; then
    echo "Successfully created DMG: ${DMG_OUTPUT_FILE}"
else
    echo "Error creating DMG."
    exit 1
fi

echo "Done."