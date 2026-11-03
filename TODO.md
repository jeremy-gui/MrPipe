# TODO - User Interface Improvements

## Improvements to implement

### Fixes (fix)
- [x] **Project collapse**: Prevent a project from automatically expanding on update if the user manually collapsed it
- [ ] **Hipster pipe**: Do not show the success animation for a pipeline that is not currently selected
- [ ] **Inactivity**: After a long period of inactivity, pipelines stop loading automatically
- [x] **HTTP error code filter**: Filter out HTTP error codes
- [ ] **Empty pipeline line**: If the empty pipeline message is displayed and a pipeline arrives, this message must be removed
- [ ] **Outdated log header**: The header does not update as the stage changes
### New features (feat)
- [x] **Pipeline timestamp**: Show the pipeline creation/execution timestamp + job tooltip: job update date + job creation date
- [x] **Delete pipeline**: Remove a pipeline from the display with a small trash icon on the right of the row
- [x] **Target environment**: Show the pipelines' target environment just before the timestamp
- [x] **Retry button**: Implement a button to restart a pipeline
- [ ] **Expired token detection**: Expired token detection does not work correctly
- [ ] **Context menu**: Add a context menu (right click) with quick actions
- [ ] **Project information**: Show the project details when it is selected
- [ ] **Pipeline information**: Show the pipeline details when it is selected
- [ ] **Job information**: Show the job details when it is selected
- [ ] **History information**: In the "project" selection, show the latest pipelines
- [ ] **Information for jobs failed due to a YAML syntax error**:
- [ ] **GitHub workflows**: Adapt the application to also support GitHub Actions workflows
- [ ] **Secure token storage**: Store the GitLab token in the OS keychain (keyring) instead of plain text in the .ini file

### Interface improvements (ui)
- [ ] **Alternating colors**: Use alternating color shades for pipelines of the same project for better visual differentiation

## Notes
- Priority: Items are listed in suggested priority order
- Format: Follow the [conventional commits](https://www.conventionalcommits.org/) format for commit messages (fix:, feat:, ui:)
