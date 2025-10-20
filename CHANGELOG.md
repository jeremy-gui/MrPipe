# Changelog

All notable changes to Mr. Pipe will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2024-10-20

### ✨ Added
- **Pipeline timestamps**: Display creation/execution timestamps for pipelines with formatted date/time
- **Job timestamps**: Show creation and update dates in job tooltips for better tracking
- **Environment target display**: Display target environment (staging, production, etc.) as colored pill labels next to pipeline timestamps
- **Pipeline deletion**: Hide pipelines from display with trash icon button (🗑️) - pipelines remain hidden across updates
- **Job control buttons**: 
  - Retry button (▶️) to restart failed jobs
  - Cancel button (⏹️) to stop running jobs (visible only when job is running)
- **Pipeline control buttons**:
  - Start button (▶️) to create new pipeline from current branch
  - Cancel button (⏹️) to stop running pipelines (visible only when pipeline is running)
- **Project/Pipeline info display**: Click on tree items to display detailed information in log header
- **HTTP error filtering**: Filter and handle specific HTTP error codes more gracefully

### 🐛 Fixed
- **Auto-expansion prevention**: Projects manually collapsed by user no longer auto-expand during updates
- **Success animation**: Hipster Pipe success animation now only triggers for the currently selected pipeline

### 🎨 UI Improvements
- **Material Design theme**: Complete UI overhaul with modern Material Design inspired theme
- **Environment pills**: Color-coded environment labels (staging, production, development, etc.)
- **Action buttons**: SVG-based start/stop/trash icons for better visual clarity
- **Improved layout**: Better spacing and visual hierarchy for pipeline and job information

---

## [1.0.0] - 2024-10-01

### 🎉 Initial Release
- GitLab pipeline monitoring and management
- Real-time pipeline status updates
- Job logs viewer
- Multi-project support
- Hipster Pipe success animation
- Configuration management
