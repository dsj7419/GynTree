# runner_utils.py
import json
import os
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import psutil
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)


@dataclass
class TestResult:
    success: bool
    message: str
    duration: float = 0.0
    coverage: Optional[float] = None
    failed_tests: List[str] = None

    def __post_init__(self):
        if self.failed_tests is None:
            self.failed_tests = []


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_colored(text: str, color=Fore.WHITE, style=Style.NORMAL):
    print(f"{style}{color}{text}{Style.RESET_ALL}")


def load_config(config_file: str) -> Dict[str, Any]:
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            return json.load(f)
    return {}


def save_config(config_file: str, config: Dict[str, Any]):
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)


def run_command_with_timeout(
    command: List[str], output_file: str, timeout: int = 1800
) -> TestResult:
    """Run a command with timeout and output capture."""
    start_time = time.time()
    result = TestResult(success=False, message="")
    failed_tests = []

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            # Run the command with timeout
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                shell=False,
            )
            output_lines = []
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                output_lines.append(line)
                f.write(line)
                f.flush()

                # Analyze output
                if "FAILED" in line:
                    failed_tests.append(line.strip())
                    print_colored(line.strip(), Fore.RED)
                elif "PASSED" in line:
                    print_colored(line.strip(), Fore.GREEN)
                elif "WARNING" in line:
                    print_colored(line.strip(), Fore.YELLOW)
                else:
                    print(line.strip())

            # Wait for process to complete or timeout
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                print_colored(
                    f"\nTest execution timed out after {timeout} seconds.", Fore.RED
                )
                return TestResult(
                    success=False,
                    message=f"Test execution timed out after {timeout} seconds.",
                    duration=time.time() - start_time,
                )

            duration = time.time() - start_time
            success = process.returncode == 0

            result = TestResult(
                success=success,
                message="Tests completed successfully" if success else "Tests failed",
                duration=duration,
                failed_tests=failed_tests,
            )

            print_colored(f"\nTotal execution time: {duration:.2f} seconds", Fore.CYAN)
            return result

    except Exception as e:
        print_colored(f"Error during test execution: {str(e)}", Fore.RED)
        traceback.print_exc()
        return TestResult(success=False, message=str(e))


def discover_tests() -> List[str]:
    """Discover all test files in tests directory and subdirectories."""
    test_files = []
    for root, _, files in os.walk("tests"):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(os.path.join(root, file))
    return sorted(test_files)


def get_user_choice(prompt: str, options: List[str]) -> int:
    """Get user input for menu choices with validation."""
    while True:
        print_colored(prompt, Fore.CYAN)
        for i, option in enumerate(options, 1):
            print_colored(f"{i}. {option}", Fore.YELLOW)

        choice = input("Enter choice (number): ")
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return int(choice)

        print_colored("Invalid choice. Please try again.", Fore.RED)


def analyze_test_results(output_file: str) -> TestResult:
    """Analyze test output file and return results."""
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()

    passed_tests = content.count(" passed")
    failed_tests = content.count(" failed")
    skipped_tests = content.count(" skipped")
    error_tests = content.count(" error")

    total_tests = passed_tests + failed_tests + skipped_tests + error_tests

    print_colored(f"\nTest Results Summary:", Fore.CYAN)
    print_colored(f"Total tests: {total_tests}", Fore.CYAN)
    print_colored(f"Passed: {passed_tests}", Fore.GREEN)
    print_colored(f"Failed: {failed_tests}", Fore.RED)
    print_colored(f"Skipped: {skipped_tests}", Fore.YELLOW)
    print_colored(f"Errors: {error_tests}", Fore.MAGENTA)

    failed_test_list = []
    if failed_tests > 0 or error_tests > 0:
        print_colored("\nFailed or Error Tests:", Fore.RED)
        for line in content.split("\n"):
            if "FAILED" in line or "ERROR" in line:
                failed_test_list.append(line.strip())
                print_colored(line.strip(), Fore.RED)

    return TestResult(
        success=(failed_tests == 0 and error_tests == 0),
        message=f"{passed_tests}/{total_tests} tests passed",
        duration=0.0,  # Duration is set elsewhere
        failed_tests=failed_test_list,
    )


def setup_test_environment() -> None:
    """Setup necessary environment variables and configurations for testing."""
    os.environ["PYTEST_ADDOPTS"] = "--tb=short"
    if not os.path.exists("tests/reports"):
        os.makedirs("tests/reports")


def cleanup_test_environment() -> None:
    """Cleanup any resources after test execution."""
    # Kill any remaining test processes
    current_process = psutil.Process()
    for child in current_process.children(recursive=True):
        try:
            child.terminate()
            child.wait(timeout=3)
        except psutil.NoSuchProcess:
            pass
        except psutil.TimeoutExpired:
            child.kill()
