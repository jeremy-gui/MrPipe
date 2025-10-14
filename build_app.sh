#!/bin/bash

# Script to build Mr. Pipe macOS app with PyInstaller

echo "Building Mr. Pipe macOS app with PyInstaller..."

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing..."
    pip3 install --user pyinstaller
fi

# Clean previous build
rm -rf build dist

# Build the app using the .spec file
pyinstaller --clean --noconfirm MrPipe.spec

echo "Build completed! The app should be in the 'dist' folder."
echo "You can now copy Mr. Pipe.app to your Applications folder."

# Check if the app was created
if [ -d "dist/Mr. Pipe.app" ]; then
    echo "✅ Success: Mr. Pipe.app created successfully!"
else
    echo "❌ Error: Mr. Pipe.app was not created. Check the build output above for errors."
fi
