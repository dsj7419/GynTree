# Contributing to GynTree

First off, thank you for considering contributing to GynTree! I welcome contributions from everyone, whether it's a bug report, feature suggestion, or code contribution.

## Code of Conduct

By participating in this project, you are expected to uphold our [Code of Conduct](../../CODE_OF_CONDUCT.md). Please report unacceptable behavior to [dsj7419@gmail.com](mailto:dsj7419@gmail.com).

## How Can I Contribute?

## 🤝 Contributing

We welcome contributions from the community! Whether you're submitting a bug report, suggesting an enhancement, or contributing code, please follow the guidelines below to ensure a smooth and productive collaboration.

### Reporting Bugs

To submit a bug report, please follow our [Bug Report Template](../../.github/ISSUE_TEMPLATE/bug_report.md). This helps maintainers and the community understand your report, reproduce the issue, and identify related problems.

- **Title**: Use a clear and descriptive title for the issue.
- **Steps to Reproduce**: Provide a step-by-step description of how to reproduce the issue in as much detail as possible.
- **Expected Behavior**: Explain what you expected to happen.
- **Screenshots**: Include any relevant screenshots that might help explain the problem.
- **Additional Context**: Include your system details (e.g., OS version) and any other context that may be useful.

You can submit a bug report using this [Bug Report Template](../../.github/ISSUE_TEMPLATE/bug_report.md).

### Suggesting Enhancements

To suggest an enhancement or new feature, please follow our [Feature Request Template](../../.github/ISSUE_TEMPLATE/feature_request.md). This ensures your suggestion is well understood by maintainers and other contributors.

- **Title**: Use a clear and descriptive title for the suggestion.
- **Description**: Provide a detailed description of the suggested enhancement, including any steps required to implement it.
- **Use Case**: Explain why this enhancement would be useful for most GynTree users.
- **Additional Context**: Include any relevant details or screenshots to clarify your suggestion.

You can submit an enhancement suggestion using this [Feature Request Template](../../.github/ISSUE_TEMPLATE/feature_request.md).

### Your First Code Contribution

Unsure where to begin contributing to GynTree? You can start by looking through these `beginner` and `help-wanted` issues:

- [Beginner issues](https://github.com/dsj7419/GynTree/labels/beginner) - issues which should only require a few lines of code, and a test or two.
- [Help wanted issues](https://github.com/dsj7419/GynTree/labels/help%20wanted) - issues which should be a bit more involved than `beginner` issues.

### Pull Requests

- Fill in the required template
- Do not include issue numbers in the PR title
- Follow the [Python style guide](https://www.python.org/dev/peps/pep-0008/)
- Include thoughtfully-worded, well-structured tests
- Document new code based on the [Documentation Styleguide](#documentation-styleguide)
- End all files with a newline

## Styleguides

### Git Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

### Python Styleguide

All Python code must adhere to the [PEP 8 style guide](https://www.python.org/dev/peps/pep-0008/).

### Documentation Styleguide

- Use [Markdown](https://daringfireball.net/projects/markdown/) for documentation.
- Reference function names, module names, and classes within backticks.

### Dependency Management

We maintain three separate requirement files to keep our dependencies organized:

- `requirements.txt` - Core application dependencies required to run GynTree
- `requirements-dev.txt` - Development dependencies (testing, linting, etc.)
- `requirements-docs.txt` - Documentation-related dependencies

#### Adding Dependencies

When adding new dependencies:

1. Determine which requirements file is appropriate:

   - Runtime dependencies → `requirements.txt`
   - Development tools → `requirements-dev.txt`
   - Documentation tools → `requirements-docs.txt`

2. Add the dependency with an exact version:

```bash
# For runtime dependencies
pip install package_name
echo "package_name==x.y.z" >> requirements.txt

# For development dependencies
pip install package_name
echo "package_name==x.y.z" >> requirements-dev.txt
```

1. Document why the dependency is needed in a comment above the requirement

#### Development Environment Setup

To set up your development environment:

1. Clone the repository
2. Run the setup script:

```bash
python setup_dev.py
```

1. Activate the virtual environment:

- Windows: `.venv\Scripts\activate`
- Unix/MacOS: `source .venv/bin/activate`

#### Dependency Guidelines

1. Always pin dependency versions (use `==` instead of `>=`)
2. Minimize the number of dependencies
3. Regular security updates are encouraged
4. Document non-obvious dependencies
5. Test with the minimum required versions of dependencies

#### Updating Dependencies

Before submitting a PR that updates dependencies:

1. Document the reason for the update
2. Test the application with the new versions
3. Update all affected requirements files
4. Include dependency updates in their own commits

## Additional Notes

### Issue and Pull Request Labels

We use labels to categorize and prioritize issues and pull requests. Here's a breakdown of the labels we use:

#### **Type of Issue**

- `bug` - Something isn't working as expected or is broken.
- `enhancement` - New feature requests or improvements to existing functionality.
- `documentation` - Improvements or additions to the project's documentation.
- `question` - Further information is requested to clarify an issue or pull request.
- `duplicate` - This issue or pull request already exists or has been addressed.
- `invalid` - The issue or pull request is not valid or does not follow the guidelines.
- `wontfix` - Issues or features that have been decided will not be worked on.

#### **Priority**

- `high-priority` - Critical tasks that need to be addressed urgently.
- `medium-priority` - Tasks that are of moderate importance.
- `low-priority` - Issues that are less urgent but still need attention.

#### **Status and Assistance**

- `good first issue` - Ideal for newcomers or first-time contributors.
- `help wanted` - Extra attention or assistance is needed on this issue.
- `backend` - Issues specifically related to backend functionality.
- `UI` - Issues related to the user interface design and functionality.
- `test-suite` - Issues concerning the testing framework, test coverage, or failing tests.
- `performance` - Tasks related to improving application performance.

This labeling system helps us efficiently manage and prioritize issues and pull requests, ensuring that tasks are clearly categorized and receive the appropriate attention.

## Questions?

Don't hesitate to reach out if you have any questions! Feel free to [open an issue](https://github.com/dsj7419/GynTree/issues) or contact me directly.

Thank you in advance for contributing to GynTree!
