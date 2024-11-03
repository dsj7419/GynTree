# Installing GynTree

GynTree offers two installation methods: a standalone executable for most users and installation from source for developers or those who want to customize the application. Choose the method that best suits your needs.

## Standalone Executable (Recommended for most users)

1. Download the latest GynTree executable from our [releases page](https://github.com/dsj7419/GynTree/releases).
2. Extract the zip file to your desired location.
3. Run the `GynTree.exe` file.

No additional installation steps are required for the standalone executable.

## Installing from Source

If you prefer to run GynTree from source or want to contribute to its development, follow these steps:

### Prerequisites

Before you begin, ensure you have the following installed on your system:

- Python 3.8 or higher
- pip (Python package installer)

### Installation Steps

1. **Clone the Repository**

   Clone the GynTree repository to your local machine:

   ```bash
   git clone https://github.com/dsj7419/GynTree.git
   cd GynTree
   ```

2. **Set Up a Virtual Environment (Recommended)**

   It's a good practice to use a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install Dependencies**

   Install all required packages using pip:

   ```bash
   pip install -r requirements.txt
   ```

4. **Run GynTree**

   You're all set! Launch GynTree with:

   ```bash
   python src/App.py
   ```

## Building the Standalone Executable (For developers)

To build the standalone executable:

1. Ensure you're in your virtual environment and have all dependencies installed.

2. Install PyInstaller:

   ```bash
   pip install pyinstaller
   ```

3. Run the build script:

   ```bash
   python scripts/build_executable.py
   ```

4. The executable will be created in the `dist` directory as `GynTree.exe`.

5. Test the executable by running it directly from the `dist` directory.

Note: Building the executable may take several minutes. The resulting file will be large (100MB+) as it includes all necessary dependencies.

## Troubleshooting

If you encounter any issues during installation or when running the executable, try the following:

- Ensure your Python version is 3.8 or higher: `python --version`
- Update pip to the latest version: `pip install --upgrade pip`
- If you're on Linux or macOS, you might need to use `python3` and `pip3` instead of `python` and `pip`
- When building the executable, ensure you're running the script from a non-administrator command prompt
- If the executable fails to run, try rebuilding it with the latest versions of PyInstaller and your dependencies

For more detailed troubleshooting, check our [FAQ](faq.md) or [open an issue](https://github.com/dsj7419/GynTree/issues) on our GitHub repository.

## Next Steps

Now that you have GynTree installed, why not:

- Read through our [User Guide](../user-guide/basic-usage.md) to learn about all the features
- Check out the [Configuration Guide](../user-guide/configuration.md) options to customize GynTree
- [Contributing](../contributing/guidelines.md) to the project and help make GynTree even better!

For more detailed information on configuration and usage, please refer to our [User Guide](../user-guide/basic-usage.md) and [Configuration Guide](../user-guide/configuration.md).
