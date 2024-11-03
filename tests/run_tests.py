import argparse
import atexit
import json
import logging
import os
import platform
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from queue import Queue
from typing import Dict, List, Optional

import psutil
from colorama import AnsiToWin32, Fore, Style, init

# Initialize colorama with Windows-specific settings
init(wrap=False)
stream = AnsiToWin32(sys.stderr).stream

# Constants with Windows-safe paths
CONFIG_FILE = Path("tests/test_config.json")
REPORTS_DIR = Path("tests/reports")
COVERAGE_DIR = REPORTS_DIR / "coverage"
HTML_REPORT_DIR = REPORTS_DIR / "html"
LOG_DIR = REPORTS_DIR / "logs"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(stream),
        logging.FileHandler(LOG_DIR / "test_runner.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


class TestResult:
    def __init__(
        self,
        success: bool = False,
        message: str = "",
        duration: float = 0.0,
        coverage: Optional[float] = None,
        failed_tests: List[str] = None,
    ):
        self.success = success
        self.message = message
        self.duration = duration
        self.coverage = coverage
        self.failed_tests = failed_tests or []
        self.timestamp = datetime.now()
        self.platform_info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        }

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "message": self.message,
            "duration": self.duration,
            "coverage": self.coverage,
            "failed_tests": self.failed_tests,
            "timestamp": self.timestamp.isoformat(),
            "platform_info": self.platform_info,
        }


@contextmanager
def windows_process_handler():
    """Context manager for handling Windows processes"""
    processes = []

    def cleanup_processes():
        for proc in processes:
            try:
                if proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
            except Exception as e:
                logger.warning(f"Error cleaning up process: {e}")

    try:
        yield processes
    finally:
        cleanup_processes()


class TestRunner:
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.initialize_directories()
        self.load_last_config()
        self.running_processes = []
        atexit.register(self.cleanup)

        # Create event for handling interrupts
        self.stop_event = threading.Event()

        # Setup signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGBREAK):
            try:
                signal.signal(sig, self.handle_signal)
            except (AttributeError, ValueError):
                continue

    def handle_signal(self, signum, frame):
        """Handle interruption signals"""
        logger.info(f"Received signal {signum}, initiating cleanup...")
        self.stop_event.set()
        self.cleanup()
        sys.exit(1)

    def initialize_directories(self):
        """Initialize necessary directories for test reports"""
        for directory in [REPORTS_DIR, COVERAGE_DIR, HTML_REPORT_DIR, LOG_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

    def load_last_config(self):
        """Load the last used configuration from test_config.json"""
        try:
            if CONFIG_FILE.exists():
                with CONFIG_FILE.open("r") as f:
                    config = json.load(f)
                    self.last_config = config.get("last_config", {})
            else:
                self.last_config = {}
        except Exception as e:
            logger.warning(f"Error loading config: {e}")
            self.last_config = {}

    def cleanup(self):
        """Clean up resources when runner exits"""
        logger.info("Cleaning up resources...")

        # Clean up processes
        for process in self.running_processes:
            try:
                if isinstance(process, subprocess.Popen) and process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
            except Exception as e:
                logger.warning(f"Error cleaning up process: {e}")

        # Clean up temporary files
        temp_dir = Path(tempfile.gettempdir())
        for item in temp_dir.glob("gyntree_test_*"):
            try:
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Error cleaning up temporary file {item}: {e}")

    def run_tests(
        self, options: Dict, selected_tests: Optional[List[str]] = None
    ) -> TestResult:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = LOG_DIR / f"test_run_{timestamp}.log"
        report_file = HTML_REPORT_DIR / f"report_{timestamp}.html"

        # Build pytest command
        cmd = ["pytest", "-v"]

        if options.get("parallel", False):
            cpu_count = os.cpu_count() or 1
            worker_count = min(cpu_count, 4)  # Limit to 4 workers
            cmd.extend(["-n", str(worker_count)])

        if options.get("html_report", True):
            cmd.extend(["--html", str(report_file), "--self-contained-html"])

        if options.get("coverage", True):
            cmd.extend(
                [
                    "--cov=src",
                    "--cov-report=term-missing",
                    f"--cov-report=html:{COVERAGE_DIR}",
                    "--cov-report=json:coverage.json",
                    "--cov-branch",  # Enable branch coverage
                ]
            )

        # Add timeout configurations
        timeout = options.get("timeout", self.last_config.get("timeout", 300))
        cmd.extend([f"--timeout={timeout}", "--timeout-method=thread"])

        # Add extra args if any
        extra_args = options.get("extra_args")
        if extra_args:
            cmd.extend(extra_args.split())

        # Add test selection
        if selected_tests:
            cmd.extend(selected_tests)
        else:
            cmd.append("tests")

        # Setup environment
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(
            [
                str(Path("src").absolute()),
                str(Path("tests").absolute()),
                env.get("PYTHONPATH", ""),
            ]
        )

        try:
            start_time = time.time()

            # Run tests with output capturing
            with log_file.open("w", encoding="utf-8") as log:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    env=env,
                    creationflags=subprocess.CREATE_NO_WINDOW
                    if platform.system() == "Windows"
                    else 0,
                )

                self.running_processes.append(process)
                failed_tests = []

                while True:
                    if self.stop_event.is_set():
                        raise KeyboardInterrupt("Test execution interrupted")

                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break

                    log.write(line)
                    log.flush()

                    # Print with color coding
                    if "FAILED" in line:
                        print(Fore.RED + line.strip(), file=stream)
                        failed_tests.append(line.strip())
                    elif "PASSED" in line:
                        print(Fore.GREEN + line.strip(), file=stream)
                    elif "WARNING" in line:
                        print(Fore.YELLOW + line.strip(), file=stream)
                    elif "ERROR" in line:
                        print(Fore.RED + line.strip(), file=stream)
                        failed_tests.append(line.strip())
                    else:
                        print(line.strip(), file=stream)

            duration = time.time() - start_time
            success = process.returncode == 0

            # Get coverage if available
            coverage = None
            coverage_file = Path("coverage.json")
            if coverage_file.exists():
                try:
                    with coverage_file.open("r") as f:
                        coverage_data = json.load(f)
                        coverage = coverage_data.get("totals", {}).get(
                            "percent_covered", 0
                        )
                    coverage_file.unlink()
                except Exception as e:
                    logger.warning(f"Error processing coverage data: {e}")

            result = TestResult(
                success=success,
                message="Tests completed successfully" if success else "Tests failed",
                duration=duration,
                coverage=coverage,
                failed_tests=failed_tests,
            )

            # Save test results
            self.save_test_results(result, timestamp)

            return result

        except subprocess.TimeoutExpired:
            return TestResult(
                success=False,
                message=f"Tests timed out after {timeout} seconds",
                duration=time.time() - start_time,
            )
        except KeyboardInterrupt:
            logger.info("Test execution interrupted by user")
            return TestResult(
                success=False,
                message="Test execution interrupted by user",
                duration=time.time() - start_time,
            )
        except Exception as e:
            logger.exception("Error during test execution")
            return TestResult(
                success=False,
                message=f"Error running tests: {str(e)}\n{traceback.format_exc()}",
            )
        finally:
            if process in self.running_processes:
                self.running_processes.remove(process)

    def save_test_results(self, result: TestResult, timestamp: str):
        """Save test results to JSON file and update last configuration"""
        try:
            results_file = REPORTS_DIR / f"results_{timestamp}.json"
            with results_file.open("w") as f:
                json.dump(result.to_dict(), f, indent=2)

            # Save the last configuration
            config_data = {"last_config": self.last_config}
            with CONFIG_FILE.open("w") as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Error saving test results: {e}")


def clear_screen():
    """Clear screen cross-platform"""
    os.system("cls" if platform.system() == "Windows" else "clear")


def print_colored(text: str, color=Fore.WHITE, style=Style.NORMAL):
    """Print colored text to Windows console"""
    print(f"{style}{color}{text}{Style.RESET_ALL}", file=stream)


def get_user_choice(prompt: str, options: List[str]) -> int:
    """Get user input for menu choices with validation"""
    while True:
        print_colored(prompt, Fore.CYAN)
        for i, option in enumerate(options, 1):
            print_colored(f"{i}. {option}", Fore.YELLOW)

        try:
            choice = int(input("Enter choice (number): "))
            if 1 <= choice <= len(options):
                return choice
            print_colored(
                "Invalid choice. Please enter a number within the range.", Fore.RED
            )
        except ValueError:
            print_colored("Invalid input. Please enter a number.", Fore.RED)


def main(debug_mode: bool = False, ci_mode: bool = False):
    runner = TestRunner(debug_mode=debug_mode)

    if ci_mode:
        # Run with default options in CI mode
        options = {
            "parallel": True,
            "html_report": True,
            "coverage": True,
            "timeout": runner.last_config.get("timeout", 300),
            "debug": debug_mode,
        }
        result = runner.run_tests(options)
        sys.exit(0 if result.success else 1)

    while True:
        clear_screen()
        print_colored("GynTree Interactive Test Runner", Fore.CYAN, Style.BRIGHT)
        print_colored("================================\n", Fore.CYAN, Style.BRIGHT)

        test_type_choices = [
            "Run All Tests",
            "Run Unit Tests",
            "Run Integration Tests",
            "Run Performance Tests",
            "Run Functional Tests",
            "Run GUI Tests",
            "Run Single Test",
            "View Last Test Report",
            "Clean Test Reports",
            "Exit",
        ]

        choice = get_user_choice("Select operation:", test_type_choices)

        if choice == len(test_type_choices):  # Exit
            print_colored("\nExiting. Goodbye!", Fore.YELLOW)
            break

        if choice == len(test_type_choices) - 1:  # Clean reports
            if (
                input(
                    "Are you sure you want to clean all test reports? (y/n): "
                ).lower()
                == "y"
            ):
                try:
                    shutil.rmtree(REPORTS_DIR)
                    runner.initialize_directories()
                    print_colored("Test reports cleaned.", Fore.GREEN)
                except Exception as e:
                    print_colored(f"Error cleaning reports: {e}", Fore.RED)
            continue

        if choice == len(test_type_choices) - 2:  # View last report
            reports = sorted(HTML_REPORT_DIR.glob("*.html"))
            if reports:
                latest_report = reports[-1]
                try:
                    if platform.system() == "Windows":
                        os.startfile(latest_report)
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", latest_report])
                    else:
                        subprocess.run(["xdg-open", latest_report])
                except Exception as e:
                    print_colored(f"Error opening report: {e}", Fore.RED)
            else:
                print_colored("No test reports found.", Fore.YELLOW)
            input("\nPress Enter to continue...")
            continue

        # Configure test run
        options = {
            "debug": debug_mode,
            "parallel": True,
            "html_report": True,
            "coverage": True,
            "timeout": runner.last_config.get("timeout", 300),
        }

        # Set test type
        selected_tests = None
        if choice == 7:  # Run Single Test
            excluded_files = {"test_runner_utils.py", "test_runners.py"}
            test_files = sorted(
                [
                    test.resolve()
                    for test in Path("tests").rglob("test_*.py")
                    if test.name not in excluded_files
                ]
            )

            if not test_files:
                print_colored("No test files found!", Fore.RED)
                continue

            # Use absolute path for 'tests' directory
            tests_dir = Path("tests").resolve()
            # Display test files relative to the 'tests' directory
            test_choices = ["Return to Main Menu"] + [
                str(test.relative_to(tests_dir)) for test in test_files
            ]

            test_choice = get_user_choice("Select test file to run:", test_choices)
            if test_choice == 1:
                continue  # Return to main menu

            selected_test = test_files[test_choice - 2]  # Adjust index
            # Pass the test path relative to current working directory
            selected_tests = [str(selected_test.relative_to(Path.cwd()))]
        else:
            if choice == 1:
                pass  # Run all tests
            elif choice == 2:
                options["extra_args"] = "-m unit"
            elif choice == 3:
                options["extra_args"] = "-m integration"
            elif choice == 4:
                options["extra_args"] = "-m performance"
            elif choice == 5:
                options["extra_args"] = "-m functional"
            elif choice == 6:
                options["extra_args"] = "-m gui"

        # Run tests
        print_colored("\nRunning tests...\n", Fore.CYAN)
        result = runner.run_tests(options, selected_tests)

        # Print summary
        print_colored("\nTest Run Summary:", Fore.CYAN, Style.BRIGHT)
        print_colored(
            f"Status: {'Success' if result.success else 'Failed'}",
            Fore.GREEN if result.success else Fore.RED,
        )
        print_colored(f"Duration: {result.duration:.2f} seconds", Fore.YELLOW)

        if result.coverage is not None:
            print_colored(f"Coverage: {result.coverage:.1f}%", Fore.YELLOW)

        if result.failed_tests:
            print_colored("\nFailed Tests:", Fore.RED)
            for test in result.failed_tests:
                print_colored(f"  {test}", Fore.RED)

        # Save last run configuration
        runner.last_config.update(
            {
                "last_run_type": test_type_choices[choice - 1],
                "last_run_time": datetime.now().isoformat(),
                "last_run_success": result.success,
            }
        )

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GynTree Test Runner")
    parser.add_argument(
        "--ci", action="store_true", help="Run in CI mode with last saved configuration"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Run in debug mode with extra logging"
    )
    parser.add_argument("--config", type=str, help="Path to custom configuration file")
    parser.add_argument(
        "--test-type",
        choices=["all", "unit", "integration", "performance", "functional", "gui"],
        help="Specific type of tests to run",
    )
    parser.add_argument("--test-file", type=str, help="Specific test file to run")
    args = parser.parse_args()

    try:
        # Configure logging based on debug mode
        log_level = logging.DEBUG if args.debug else logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(stream),
                logging.FileHandler(
                    LOG_DIR / f"test_runner_{datetime.now():%Y%m%d_%H%M%S}.log",
                    encoding="utf-8",
                ),
            ],
        )

        # Handle custom configuration
        if args.config:
            config_path = Path(args.config)
            if config_path.exists():
                with config_path.open("r") as f:
                    custom_config = json.load(f)
                    if "test_options" in custom_config:
                        logger.info(f"Loading custom configuration from {config_path}")
                        args.config = custom_config["test_options"]

        # Handle specific test type or file
        if args.test_type or args.test_file:
            runner = TestRunner(debug_mode=args.debug)
            options = {
                "parallel": True,
                "html_report": True,
                "coverage": True,
                "timeout": 300,
                "debug": args.debug,
            }

            if args.test_type:
                options["extra_args"] = f"-m {args.test_type}"

            selected_tests = [args.test_file] if args.test_file else None

            result = runner.run_tests(options, selected_tests)
            sys.exit(0 if result.success else 1)
        else:
            main(debug_mode=args.debug, ci_mode=args.ci)

    except KeyboardInterrupt:
        print_colored("\nTest run interrupted by user.", Fore.YELLOW)
        sys.exit(1)
    except Exception as e:
        print_colored(f"\nError: {str(e)}", Fore.RED)
        if args.debug:
            traceback.print_exc()
        sys.exit(1)
    finally:
        # Ensure proper cleanup
        logging.shutdown()
