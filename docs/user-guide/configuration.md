# GynTree Configuration Guide

This guide covers the various configuration options available in GynTree, allowing you to customize the tool to your specific needs.

## Table of Contents

1. [General Settings](#general-settings)
2. [Analysis Configuration](#analysis-configuration)
3. [Exclusion Rules](#exclusion-rules)
4. [Visualization Options](#visualization-options)
5. [Performance Tuning](#performance-tuning)
6. [Advanced Configuration](#advanced-configuration)

## General Settings

### Application Preferences

Location: `config/preferences.json`

- `language`: Set the interface language (e.g., "en" for English)
- `theme`: Choose between "light" and "dark" themes
- `auto_save`: Enable/disable automatic saving of projects (true/false)

Example:

```json
{
  "language": "en",
  "theme": "dark",
  "auto_save": true
}
```

## Analysis Configuration

### Scan Depth

Location: `config/analysis_settings.json`

- `max_depth`: Set the maximum directory depth for analysis (-1 for unlimited)
- `follow_symlinks`: Choose whether to follow symbolic links (true/false)

Example:

```json
{
  "max_depth": 10,
  "follow_symlinks": false
}
```

## Exclusion Rules

### Global Exclusions

Location: `config/global_exclusions.json`

Define patterns for files and directories to be excluded globally:

```json
{
  "directories": ["node_modules", ".git", "__pycache__"],
  "files": ["*.pyc", ".DS_Store"]
}
```

### Project-Specific Exclusions

These are managed through the GUI and stored in individual project files.

## Visualization Options

### Tree View Settings

Location: `config/visualization_settings.json`

- `default_expanded_levels`: Number of levels to expand by default
- `node_spacing`: Adjust the spacing between tree nodes

Example:

```json
{
  "default_expanded_levels": 3,
  "node_spacing": 20
}
```

## Performance Tuning

### Analysis Optimization

Location: `config/performance_settings.json`

- `chunk_size`: Adjust the number of items processed in each batch
- `use_multiprocessing`: Enable/disable multiprocessing for large directories

Example:

```json
{
  "chunk_size": 1000,
  "use_multiprocessing": true
}
```

## Advanced Configuration

### Custom Exclusion Services

To add support for new file types or specialized exclusion rules:

1. Create a new Python file in `src/services/auto_exclude/`
2. Implement a class that inherits from `ExclusionService`
3. Add the new service to `ExclusionServiceFactory` in `src/services/ExclusionServiceFactory.py`

Example:

```python
from services.ExclusionService import ExclusionService

class CustomExclusionService(ExclusionService):
    def get_exclusions(self):
        # Implement custom exclusion logic here
        pass

# Add to ExclusionServiceFactory
service_map['custom'] = CustomExclusionService
```

### Logging Configuration

Location: `config/logging_config.json`

Adjust logging levels and output formats:

```json
{
  "version": 1,
  "disable_existing_loggers": false,
  "handlers": {
    "file": {
      "class": "logging.FileHandler",
      "filename": "gyntree.log",
      "level": "DEBUG",
      "formatter": "detailed"
    }
  },
  "root": {
    "level": "INFO",
    "handlers": ["file"]
  }
}
```

For more information on using these configurations, refer to the [User Guide](basic-usage.md). If you encounter any issues, check our [FAQ](../getting-started/faq.md) or [open an issue](https://github.com/dsj7419/GynTree/issues) on GitHub.
