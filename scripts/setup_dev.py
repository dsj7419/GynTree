#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

def run_command(command):
    """Run a command and return its success status"""
    try:
        subprocess.run(command, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(command)}: {e}")
        return False

def setup_dev_environment():
    """Set up the development environment"""
    print("Setting up development environment...")
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent
    
    # Create virtual environment if it doesn't exist
    venv_path = project_root / ".venv"
    if not venv_path.exists():
        print("Creating virtual environment...")
        if not run_command([sys.executable, "-m", "venv", str(venv_path)]):
            return False
    
    # Determine pip path
    pip_cmd = str(venv_path / "Scripts" / "pip.exe") if sys.platform == "win32" else str(venv_path / "bin" / "pip")
    
    # Install all requirements
    print("Installing requirements...")
    requirements_files = ["requirements.txt", "requirements-dev.txt", "requirements-docs.txt"]
    for req_file in requirements_files:
        if not run_command([pip_cmd, "install", "-r", req_file]):
            return False
    
    print("\nDevelopment environment setup complete!")
    print("\nTo activate your virtual environment:")
    if sys.platform == "win32":
        print(f"    {venv_path}\\Scripts\\activate")
    else:
        print(f"    source {venv_path}/bin/activate")
    
    return True

if __name__ == "__main__":
    sys.exit(0 if setup_dev_environment() else 1)