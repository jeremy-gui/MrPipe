# GitLab Pipelines Manager

A desktop application to manage GitLab pipelines for multiple projects.

## Features

- Visualize the latest pipeline for selected projects on the left panel.
- Display all jobs of the pipeline with their status, updated in real-time.
- View logs of selected jobs on the right panel, updated in real-time.

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

## Notes

- Status updates every 10 seconds.
- Log updates every 5 seconds when a job is selected.
- Ensure your token has read access to the projects.
