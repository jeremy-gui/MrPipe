# Mr. Pipe - GitLab Pipelines Manager

A desktop application to manage GitLab pipelines for multiple projects.

## Features

- Visualize the latest pipeline for selected projects on the left panel.
- Display all jobs of the pipeline with their status, updated in real-time.
- View logs of selected jobs on the right panel, updated in real-time.
- Manual job launching with visual feedback.

## Requirements

- Python 3.8+
- PyQt6
- python-gitlab

## Installation

1. Clone or download the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python main.py
   ```

2. Configure GitLab settings:
   - Go to Settings > Configure
   - Enter your GitLab URL (e.g., https://gitlab.com)
   - Enter your private access token
   - Enter project IDs separated by commas

3. The left panel will show projects and their latest pipelines with jobs.
4. Click on a job to view its log on the right panel.
5. For manual jobs, use the "Launch Job" button that appears.

## Building Applications

### macOS App

To create a native macOS application (.app) that shows "Mr. Pipe" in the menu bar:

1. Install PyInstaller:
   ```bash
   pip3 install --user pyinstaller
   ```

2. Run the build script:
   ```bash
   ./build_app.sh
   ```

3. The `Mr. Pipe.app` will be created in the `dist` folder with your custom logo.

4. Copy `Mr. Pipe.app` to your Applications folder.

**Note**: The app will use the `logo.png` file in the project root as its icon.

### Windows Executable

To create a Windows executable (.exe) that runs on any Windows system:

1. **Prepare the icon** (if not already done):
   ```bash
   # Convert PNG to ICO (requires Pillow)
   pip install Pillow
   python3 -c "from PIL import Image; Image.open('logo.png').save('logo.ico', format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])"
   ```

2. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

3. Run the Windows build script:
   ```bash
   ./build_windows.sh
   ```

4. The `Mr. Pipe.exe` will be created in the `dist` folder.

5. Copy `Mr. Pipe.exe` to any Windows system - it runs without installation!

**Note**: The executable includes all dependencies and will work on Windows 7+. It will show proper version information and use your logo as the application icon.

## Notes

- Status updates every 3 seconds after initial 10-second delay.
- Log updates every second when a job is selected.
- Ensure your token has read access to the projects.
- Manual jobs can be launched directly from the interface.
