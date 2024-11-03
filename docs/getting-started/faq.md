# Frequently Asked Questions (FAQ)

## General Questions

### Q: How does GynTree handle large directory structures?

A: GynTree uses optimized algorithms to efficiently analyze large directory structures. For extremely large projects, you can use the "Exclude Directories" feature to focus on specific areas and improve performance.

### Q: Can GynTree analyze remote directories or cloud storage?

A: Currently, GynTree only supports local directory analysis. However, you can analyze directories synced from cloud storage services like Dropbox or Google Drive.

### Q: Is my project data sent anywhere when using GynTree?

A: No. GynTree operates entirely on your local machine and does not send any data externally.

## Features and Usage

### Q: How does the auto-exclude feature work?

A: The auto-exclude feature uses predefined patterns and intelligent detection to identify common directories and files that are typically excluded from analysis (e.g., build directories, cache files). You can review and modify these suggestions before applying them.

### Q: Can I use GynTree for non-code projects?

A: Absolutely! While GynTree has features tailored for code projects, it's equally effective for analyzing any type of directory structure, such as document repositories or media libraries.

### Q: How accurate is the comment extraction feature?

A: Comment extraction is highly accurate for supported file types. It looks for specially formatted comments (e.g., "GynTree: ...") to identify file purposes. The accuracy may vary for files without these specific comments.

## Troubleshooting

### Q: GynTree is running slowly on my large project. What can I do?

A: Try excluding unnecessary directories, use more specific start directories, or break your analysis into smaller sub-projects. Also, ensure your system meets the recommended specifications.

### Q: Why aren't some of my files showing up in the analysis?

A: Check your exclusion settings. Some files might be automatically excluded based on type or location. You can modify these settings in the configuration.

### Q: The tree visualization is not rendering correctly. How can I fix this?

A: Ensure you have the latest version of GynTree and all its dependencies installed. If the issue persists, try adjusting the display settings or export the tree as ASCII for an alternative view.

## Development and Contribution

### Q: How can I extend GynTree to support additional file types?

A: You can create a custom ExclusionService class for new file types. Refer to the [Contributing Guide](../contributing/guidelines.md) and [API Reference](../api/overview.md) for detailed instructions.

### Q: Is there a plugin system for GynTree?

A: Not currently, but it's on our roadmap. For now, you can extend functionality by modifying the source code directly.

For more detailed information, please refer to our [User Guide](../user-guide/basic-usage.md) and [Configuration Guide](../user-guide/configuration.md). If your question isn't answered here, feel free to [open an issue](https://github.com/dsj7419/GynTree/issues) on our GitHub repository.
