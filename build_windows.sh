#!/bin/bash

# Script to build Mr. Pipe Windows executable

echo "Building Mr. Pipe Windows executable..."

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing..."
    pip3 install --user pyinstaller
fi

# Clean previous build
rm -rf build dist

# Build the executable using the Windows .spec file
pyinstaller --clean --noconfirm MrPipe-Windows.spec

echo "Build completed! The executable should be in the 'dist' folder."
echo "You can now run Mr. Pipe.exe on Windows systems."

# Check if the executable was created
if [ -f "dist/Mr. Pipe.exe" ] || [ -f "dist/Mr. Pipe" ]; then
    echo "✅ Success: Mr. Pipe executable created successfully!"
    ls -lh dist/Mr.* | grep -E "(Mr\. Pipe|Mr\. Pipe\.exe)"
else
    echo "❌ Error: Mr. Pipe executable was not created. Check the build output above for errors."
fi
