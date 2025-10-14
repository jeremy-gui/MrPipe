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

## Building macOS App

To create a native macOS application (.app) that shows "Mr. Pipe" in the menu bar:

1. Install PyInstaller:
   ```bash
   pip3 install --user pyinstaller
   ```

2. Run the build script:
   ```bash
   ./build_app.sh
   ```

3. The `Mr. Pipe.app` will be created in the `dist` folder.

4. Copy `Mr. Pipe.app` to your Applications folder.

**Note**: If the build fails, you can try running PyInstaller directly:
```bash
pyinstaller --clean --noconfirm MrPipe.spec
```

## Notes

- Status updates every 3 seconds after initial 10-second delay.
- Log updates every second when a job is selected.
- Ensure your token has read access to the projects.
- Manual jobs can be launched directly from the interface.
