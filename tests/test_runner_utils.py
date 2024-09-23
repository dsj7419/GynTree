import os
import sys
import json
import subprocess
import threading
import queue
from datetime import datetime
import re
import time
import pytest
from pytest import Config
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_colored(text, color=Fore.WHITE, style=Style.NORMAL):
    print(f"{style}{color}{text}{Style.RESET_ALL}")

def load_config(config_file):
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return {}

def save_config(config_file, config):
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

def run_command_with_timeout(command, output_file, timeout=1800):  # 30 minutes timeout
    def target(queue):
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
            for line in iter(process.stdout.readline, ''):
                queue.put(line)
            process.stdout.close()
            process.wait()
            queue.put(None)
        except Exception as e:
            queue.put(f"Error: {str(e)}")
            queue.put(None)

    q = queue.Queue()
    thread = threading.Thread(target=target, args=(q,))
    thread.start()

    start_time = time.time()
    with open(output_file, 'w', encoding='utf-8') as f:
        while True:
            try:
                line = q.get(timeout=1)
                if line is None:
                    break
                if "PASSED" in line:
                    print_colored(line.strip(), Fore.GREEN)
                elif "FAILED" in line or "ERROR" in line:
                    print_colored(line.strip(), Fore.RED)
                else:
                    print(line.strip())
                f.write(line)
                f.flush()
            except queue.Empty:
                if time.time() - start_time > timeout:
                    print_colored(f"Test execution timed out after {timeout} seconds.", Fore.RED)
                    break

    thread.join(timeout=5)
    if thread.is_alive():
        print_colored("Failed to terminate process gracefully. Forcing termination.", Fore.RED)

    print_colored(f"Total execution time: {time.time() - start_time:.2f} seconds", Fore.CYAN)

def run_tests(options, selected_tests, reports_dir):
    if not os.path.exists('tests/conftest.py'):
        print_colored("Error: conftest.py not found in tests directory. Please run the script from the project root.", Fore.RED)
        return

    pytest_args = ["-v", "--tb=short", "--capture=no", "--log-cli-level=DEBUG"]
    
    if options.get('parallel', False):
        pytest_args.append("-n auto")
    
    if options.get('html_report', False):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = os.path.join(reports_dir, f"test_report_{timestamp}.html")
        pytest_args.extend([f"--html={report_name}", "--self-contained-html"])
    
    if options.get('extra_args'):
        pytest_args.extend(options['extra_args'].split())
    
    if options.get('debug', False):
        pytest_args.append("-vv")
    
    if selected_tests:
        pytest_args.extend(selected_tests)
    else:
        pytest_args.append("tests")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(reports_dir, f"test_output_{timestamp}.txt")

    print_colored(f"Running pytest with arguments: {' '.join(pytest_args)}", Fore.CYAN)
    print_colored(f"Test output will be saved to: {output_file}", Fore.YELLOW)
    print_colored("Test output:", Fore.YELLOW)

    start_time = datetime.now()

    try:
        if options.get('coverage', False):
            coverage_command = f"coverage run -m pytest {' '.join(pytest_args)}"
            run_command_with_timeout(coverage_command, output_file, timeout=3600)  # 1 hour timeout
        else:
            run_command_with_timeout(f"pytest {' '.join(pytest_args)}", output_file, timeout=3600)  # 1 hour timeout
    except subprocess.CalledProcessError as e:
        print_colored(f"An error occurred while running tests: {e}", Fore.RED)
    except Exception as e:
        print_colored(f"An unexpected error occurred: {str(e)}", Fore.RED)
    finally:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print_colored(f"\nTests completed in {duration:.2f} seconds", Fore.CYAN)
        print_colored(f"Full test output saved to: {output_file}", Fore.GREEN)

        if options.get('html_report', False):
            print_colored(f"HTML report generated: {report_name}", Fore.GREEN)

        if options.get('coverage', False):
            subprocess.run("coverage report", shell=True)
            coverage_html = os.path.join(reports_dir, "coverage_html")
            subprocess.run(f"coverage html -d {coverage_html}", shell=True)
            print_colored(f"Coverage report generated: {coverage_html}/index.html", Fore.GREEN)

    print_colored("\nAnalyzing test results...", Fore.CYAN)
    analyze_test_results(output_file)

def analyze_test_results(output_file):
    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()

    passed_tests = len(re.findall(r"PASSED", content))
    failed_tests = len(re.findall(r"FAILED", content))
    skipped_tests = len(re.findall(r"SKIPPED", content))
    error_tests = len(re.findall(r"ERROR", content))

    total_tests = passed_tests + failed_tests + skipped_tests + error_tests

    print_colored(f"Total tests: {total_tests}", Fore.CYAN)
    print_colored(f"Passed: {passed_tests}", Fore.GREEN)
    print_colored(f"Failed: {failed_tests}", Fore.RED)
    print_colored(f"Skipped: {skipped_tests}", Fore.YELLOW)
    print_colored(f"Errors: {error_tests}", Fore.MAGENTA)

    if failed_tests > 0 or error_tests > 0:
        print_colored("\nFailed and Error tests:", Fore.RED)
        for line in content.split('\n'):
            if "FAILED" in line or "ERROR" in line:
                print_colored(line.strip(), Fore.RED)

def discover_tests():
    """Discover test files in the tests directory and its subdirectories."""
    test_files = []
    for root, _, files in os.walk('tests'):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                test_files.append(os.path.join(root, file))
    return test_files

def get_user_choice(prompt, options):
    while True:
        print_colored(prompt, Fore.CYAN)
        for i, option in enumerate(options, 1):
            print_colored(f"{i}. {option}", Fore.YELLOW)
        choice = input("Enter your choice (number): ")
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return int(choice)
        print_colored("Invalid choice. Please try again.", Fore.RED)