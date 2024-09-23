import os
import sys
import argparse
import traceback
from colorama import init, Fore, Style
from test_runner_utils import (
    clear_screen, print_colored, load_config, save_config,
    discover_tests, get_user_choice
)
from test_runners import TestRunnerFactory, AllTestsRunner, SingleTestRunner

init(autoreset=True)

CONFIG_FILE = os.path.join('tests', 'test_config.json')
REPORTS_DIR = os.path.join('tests', 'reports')

def main_menu(debug_mode):
    config = load_config(CONFIG_FILE)
    while True:
        clear_screen()
        print_colored("GynTree Interactive Test Runner", Fore.CYAN, Style.BRIGHT)
        print_colored("================================\n", Fore.CYAN, Style.BRIGHT)
        options = {'debug': debug_mode}
        tests = discover_tests()
        if not tests:
            print_colored("No test files found!", Fore.RED)
            sys.exit(1)
        test_type_choices = [
            "Run all tests",
            "Run unit tests",
            "Run integration tests",
            "Run performance tests",
            "Run functional tests",
            "Run single test",
            "Exit"
        ]
        test_type = get_user_choice("Select test type:", test_type_choices)
        if test_type == 7:
            print_colored("Exiting. Goodbye!", Fore.YELLOW)
            sys.exit(0)
        selected_tests = None
        if test_type == 6:
            test_file_choice = get_user_choice("Select test file to run:", tests)
            selected_tests = [tests[test_file_choice - 1]]
            runner = SingleTestRunner()
        else:
            test_type_name = test_type_choices[test_type - 1].lower().split()[1]
            if test_type_name == "all":
                runner = AllTestsRunner()
            else:
                runner = TestRunnerFactory.create_runner(test_type_name)
        if test_type != 6:
            execution_mode_choices = ["Run tests sequentially", "Run tests in parallel"]
            execution_mode = get_user_choice("Select execution mode:", execution_mode_choices)
            options['parallel'] = (execution_mode == 2)
        reporting_choices = ["Console output only", "Generate HTML report"]
        reporting = get_user_choice("Select reporting option:", reporting_choices)
        options['html_report'] = (reporting == 2)
        coverage_choices = ["No coverage", "Generate coverage report"]
        coverage = get_user_choice("Select coverage option:", coverage_choices)
        options['coverage'] = (coverage == 2)
        clear_screen()
        print_colored("Test Run Configuration:", Fore.CYAN, Style.BRIGHT)
        print_colored("-------------------------", Fore.CYAN)
        print_colored(f"Test type: {test_type_choices[test_type - 1]}", Fore.YELLOW)
        if selected_tests:
            print_colored(f"Selected test: {selected_tests[0]}", Fore.YELLOW)
        else:
            print_colored(f"Execution mode: {execution_mode_choices[execution_mode - 1]}", Fore.YELLOW)
        print_colored(f"Reporting: {reporting_choices[reporting - 1]}", Fore.YELLOW)
        print_colored(f"Coverage: {coverage_choices[coverage - 1]}", Fore.YELLOW)
        print_colored(f"Debug mode: {'Enabled' if debug_mode else 'Disabled'}", Fore.YELLOW)
        print()
        confirm = input("Do you want to proceed with this configuration? (y/n): ")
        if confirm.lower() == 'y':
            try:
                runner.run(options, selected_tests, REPORTS_DIR)
            except Exception as e:
                print_colored("An error occurred during test execution:", Fore.RED)
                print_colored(str(e), Fore.RED)
                print_colored("\nTraceback:", Fore.RED)
                traceback.print_exc()
            finally:
                input("\nPress Enter to return to the main menu...")
        
        config['last_config'] = options
        save_config(CONFIG_FILE, config)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GynTree Test Runner")
    parser.add_argument("--ci", action="store_true", help="Run in CI mode with last saved configuration")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode with extra logging")
    args = parser.parse_args()

    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)

    if args.ci:
        config = load_config(CONFIG_FILE)
        last_config = config.get('last_config', {})
        if last_config:
            print_colored("Running tests with last saved configuration in CI mode", Fore.CYAN)
            last_config['debug'] = args.debug
            AllTestsRunner().run(last_config, None, REPORTS_DIR)
        else:
            print_colored("No saved configuration found. Please run in interactive mode first.", Fore.RED)
            sys.exit(1)
    else:
        main_menu(args.debug)