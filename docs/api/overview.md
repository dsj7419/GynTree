# 📚 GynTree API Reference

This API reference provides detailed information about the core components of the GynTree application. Each section describes the available modules, classes, and functions, with usage examples where appropriate.

---

## Modules Overview

### 1. **AppController**

Manages the core functionality of the GynTree application, orchestrating the workflow between different controllers.

**start()**  
Initializes the application and loads the initial UI.  
**Returns**: `None`

**shutdown()**  
Properly terminates the application and cleans up resources before exit.  
**Returns**: `None`

**load_project(project_path: str)**  
Loads a project configuration from the specified path.  
**Arguments**:

- `project_path` _(str)_: The path to the project configuration file.  
**Returns**: `None`

---

### 2. **ProjectController**

Handles loading, saving, and managing project configurations and data.

**create_project(project_name: str, directory: str)**  
Creates a new project with the specified name and root directory.  
**Arguments**:

- `project_name` _(str)_: The name of the project.
- `directory` _(str)_: The root directory of the project.  
**Returns**: `None`

**save_project(project_path: str)**  
Saves the current project configuration to the specified path.  
**Arguments**:

- `project_path` _(str)_: The path to save the project configuration file.  
**Returns**: `None`

**delete_project(project_name: str)**  
Deletes the project configuration from the system.  
**Arguments**:

- `project_name` _(str)_: The name of the project to delete.  
**Returns**: `None`

---

### 3. **DirectoryAnalyzer**

Responsible for scanning and analyzing directory structures to provide hierarchical or flat representations.

**analyze(directory: str, exclude_patterns: List[str])**  
Analyzes the specified directory while excluding files or directories matching the patterns.  
**Arguments**:

- `directory` _(str)_: The path of the directory to analyze.
- `exclude_patterns` _(List[str])_: A list of patterns to exclude during the analysis.  
**Returns**: `Dict[str, Any]` _(Directory structure representation)_

---

### 4. **CommentParser**

Extracts purpose comments from source code files that start with `GynTree:`.

**parse_file(file_path: str)**  
Parses the file for comments starting with `GynTree:` to extract descriptions.  
**Arguments**:

- `file_path` _(str)_: The path of the file to parse.  
**Returns**: `List[str]` _(List of extracted comments)_

**parse_directory(directory: str)**  
Scans all files in a directory for comments starting with `GynTree:` and returns a summary.  
**Arguments**:

- `directory` _(str)_: The directory path to scan.  
**Returns**: `Dict[str, List[str]]` _(Mapping of filenames to extracted comments)_

---

### 5. **ThemeManager**

Handles the application's light and dark theming.

**set_theme(theme: str)**  
Switches between light and dark themes.  
**Arguments**:

- `theme` _(str)_: Must be either `"light"` or `"dark"`.  
**Returns**: `None`

**apply_theme(window: QWidget)**  
Applies the current theme to the specified window or UI element.  
**Arguments**:

- `window` _(QWidget)_: The UI window or component to apply the theme to.  
**Returns**: `None`

---

### 6. **ExclusionManager**

Allows users to define files or directories to exclude from the analysis.

**add_exclusion(pattern: str)**  
Adds a file or directory pattern to the exclusion list.  
**Arguments**:

- `pattern` _(str)_: The pattern (e.g., `*.log`, `__pycache__`) to exclude from the analysis.  
**Returns**: `None`

**remove_exclusion(pattern: str)**  
Removes a file or directory pattern from the exclusion list.  
**Arguments**:

- `pattern` _(str)_: The pattern to remove from the exclusion list.  
**Returns**: `None`

**get_exclusions()**  
Retrieves the list of current exclusions.  
**Returns**: `List[str]` _(List of exclusion patterns)_

---

### 7. **AutoExcludeManager**

Automatically suggests files and directories to exclude based on the project type.

**suggest_exclusions(project_type: str)**  
Suggests common exclusions for a specific project type (e.g., Python, Node.js).  
**Arguments**:

- `project_type` _(str)_: The type of project (e.g., `"python"`, `"nodejs"`).  
**Returns**: `List[str]` _(List of suggested exclusions)_

---

## Error Handling

Most GynTree components will raise exceptions if they encounter critical issues, such as:

- **`FileNotFoundError`**: Raised when trying to access a non-existent file or directory.
- **`ValueError`**: Raised when invalid arguments are passed to a method.
- **`PermissionError`**: Raised if the application lacks permissions to access a file or directory.

---

## Future API Extensions

This API reference will be expanded as more functionality is added to GynTree, including:

- **Directory comparison**: Compare two directory structures and highlight differences.
- **Plugin system**: Allow developers to extend the functionality of GynTree with custom plugins.
- **Cloud integration**: Support for analyzing cloud directories such as Dropbox or Google Drive.
