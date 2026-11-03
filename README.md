# Mr. Pipe - GitLab Pipelines Manager

A desktop application to monitor and control GitLab CI/CD pipelines across multiple projects, without keeping the GitLab web interface open.

It is for developers who follow the pipelines of several projects day to day.

Built with Python, PyQt6 and python-gitlab, and packaged with PyInstaller for Windows and macOS.

## Features

- Visualize the latest pipeline for selected projects on the left panel.
- Display all jobs of the pipeline with their status, updated in real-time.
- View logs of selected jobs on the right panel, updated in real-time.
- Manual job launching with visual feedback.
- Start, retry and cancel jobs and pipelines, with timestamps and target environments displayed.
- **Hipster Pipe**: Celebration animation when pipelines succeed (optional feature).

## Hipster Pipe Feature

Mr. Pipe includes a "Hipster Pipe" feature that plays a short video when a pipeline succeeds or fails. The videos are in `assets/` and are included in the packaged applications.

To enable it, go to Settings > Configure and set the "Hipster Pipe" option to "Yes" or "Yes with sound".

## Requirements

- Python 3.9+ (the Windows build was tested with Python 3.12)
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
   - Select the projects to monitor (up to 10)

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

**Note**: The script deletes the existing `build` and `dist` folders first.

### Windows Executable

To create a Windows executable (.exe) that runs on any Windows system:

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Run the Windows build script (it deletes the existing `build` and `dist` folders first):
   ```bash
   ./build_windows.sh
   ```

3. The `Mr. Pipe.exe` will be created in the `dist` folder.

4. Copy `Mr. Pipe.exe` to another Windows system - it runs without installation.

**Note**: The executable includes all dependencies and uses `assets/logo.ico` as its icon.

## Notes

- Status updates every 3 seconds after initial 10-second delay.
- Log updates every second when a job is selected.
- Ensure your token has read access to the projects.
- Manual jobs can be launched directly from the interface.

## Roadmap

Planned work is listed in [TODO.md](TODO.md).

## License

Mr. Pipe is released under the [MIT License](LICENSE).
