# Changelog

## [v0.3.1-pre]

- Implemented dark/light theme toggle
- Expanded testing for UI components
- More robust interface for theme management

## [v0.3.0-pre]

### GynTree is a Python desktop application designed to analyze and visualize directory structures, extracting meaningful descriptions from code comments. It provides insights into project structure and purpose, helping developers manage their codebases more efficiently

Key Features

- Directory Analysis: Generate hierarchical or flat structures of files and folders.
- Comment Parsing: Extract descriptions from comments across multiple programming languages.
- Exclusion Management: Manage files and directories to exclude from analysis.
- Project Management: Support for multiple projects with individual settings.
- Clipboard and Export: Export results to TXT or CSV formats.
- Threading: Perform background tasks without freezing the UI.
- Error Handling: Comprehensive logging and exception management for stability.

### Recent Changes in v0.3.0 Pre-release

- Refactored AppController: Separated functionality into specialized controllers (ProjectController, ThreadController, UIController), improving code maintainability and scalability.
- Enhanced Threading: Improved worker thread management to prevent memory leaks and keep the UI responsive.
- Rewritten CommentParser: Now handles both single-line and multiline comments more robustly, with better performance.
- Expanded Test Coverage: Added unit tests for critical components, ensuring reliability.
- Improved Error Handling: Global exception handling and detailed logging for better debugging.
- Startup Fixes: Resolved application startup issues by refining event loop management.
