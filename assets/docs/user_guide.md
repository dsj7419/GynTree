# GynTree User Guide

Welcome to the GynTree User Guide. This document will walk you through the main features of GynTree and how to use them effectively.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Main Interface](#main-interface)
3. [Analyzing a Directory](#analyzing-a-directory)
4. [Managing Exclusions](#managing-exclusions)
5. [Visualizing Directory Structure](#visualizing-directory-structure)
6. [Exporting Results](#exporting-results)
7. [Project Management](#project-management)
8. [Advanced Features](#advanced-features)

## Getting Started

After [installing GynTree](INSTALL.md), launch the application by running:

```bash
python src/App.py
```

## Main Interface

The main interface consists of:

- Project management buttons (Create, Load, Save)
- Directory analysis controls
- Exclusion management
- Visualization options

## Analyzing a Directory

1. Click "Create Project" or "Load Project"
2. Select the root directory you want to analyze
3. Click "Analyze Directory"
4. Review the analysis results in the Results panel

## Managing Exclusions

### Auto-Exclude

1. After analysis, GynTree will suggest auto-exclusions
2. Review the suggestions in the Auto-Exclude panel
3. Check/uncheck items as needed
4. Click "Apply" to confirm exclusions

### Manual Exclusions

1. Go to "Manage Exclusions"
2. Use "Add Directory" or "Add File" to manually exclude items
3. Use "Remove" to delete existing exclusions
4. Click "Save & Exit" to apply changes

## Visualizing Directory Structure

1. After analysis, click "View Directory Tree"
2. Use the tree view to explore your directory structure
3. Expand/collapse nodes to focus on specific areas

## Exporting Results

### Exporting as PNG

1. In the Directory Tree view, click "Export as PNG"
2. Choose a save location
3. The entire tree structure will be saved as a PNG image

### Exporting as ASCII

1. In the Directory Tree view, click "Export as ASCII"
2. Choose a save location
3. The tree structure will be saved as a text file in ASCII format

### Exporting Analysis Results

1. In the Results view, click "Export as CSV" or "Export as TXT"
2. Choose a save location
3. The detailed analysis results will be saved in the chosen format

## Project Management

### Saving a Project

1. After making changes, click "Save Project"
2. Choose a name and location for your project file

### Loading a Project

1. Click "Load Project"
2. Select a previously saved project file
3. All settings and exclusions will be restored

## Advanced Features

### Comment Extraction

GynTree automatically extracts and displays specially formatted comments from your files. To use this feature:

1. In your source files, add comments in the format: `# GynTree: [Your comment here]`
2. Run the analysis
3. View extracted comments in the Results panel

### Custom Exclusion Rules

For advanced exclusion patterns:

1. Go to "Manage Exclusions"
2. Click "Add Custom Rule"
3. Enter a regex pattern for files or directories to exclude

For more detailed information on configuration options, refer to our [Configuration Guide](configuration.md). If you encounter any issues, check our [FAQ](faq.md) or [open an issue](https://github.com/dsj7419/GynTree/issues) on GitHub.
