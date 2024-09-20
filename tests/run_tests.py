import subprocess
import os
import sys
import time
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_colored(text, color=Fore.WHITE, style=Style.NORMAL):
    print(f"{style}{color}{text}")

def run_command(command, output_file):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for stdout_line in iter(process.stdout.readline, ""):
            f.write(stdout_line)
            yield stdout_line
    process.stdout.close()
    return_code = process.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, command)

def run_tests(options):
    base_command = f"pytest -v --tb=short --capture=no --log-cli-level=DEBUG {options.get('extra_args', '')}"
    
    if options.get('parallel', False):
        base_command += " -n auto"
    
    if options.get('html_report', False):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = f"test_report_{timestamp}.html"
        base_command += f" --html={report_name} --self-contained-html"
    
    if options.get('memory_test', False):
        base_command += " -m memory"
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"test_output_{timestamp}.txt"
    
    print_colored(f"Running command: {base_command}", Fore.CYAN)
    print_colored(f"Test output will be saved to: {output_file}", Fore.YELLOW)
    print_colored("Test output:", Fore.YELLOW)
    
    start_time = time.time()
    try:
        for line in run_command(base_command, output_file):
            if "PASSED" in line:
                print_colored(line.strip(), Fore.GREEN)
            elif "FAILED" in line:
                print_colored(line.strip(), Fore.RED)
            elif "SKIPPED" in line:
                print_colored(line.strip(), Fore.YELLOW)
            else:
                print(line.strip())
    except subprocess.CalledProcessError as e:
        print_colored(f"An error occurred while running the tests: {e}", Fore.RED)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print_colored(f"\nTests completed in {duration:.2f} seconds", Fore.CYAN)
    print_colored(f"Full test output saved to: {output_file}", Fore.GREEN)
    
    if options.get('html_report', False):
        print_colored(f"HTML report generated: {report_name}", Fore.GREEN)

def get_user_choice(prompt, options):
    while True:
        print_colored(prompt, Fore.CYAN)
        for i, option in enumerate(options, 1):
            print_colored(f"{i}. {option}", Fore.YELLOW)
        choice = input("Enter your choice (number): ")
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return int(choice)
        print_colored("Invalid choice. Please try again.", Fore.RED)

def main_menu():
    while True:
        clear_screen()
        print_colored("GynTree Interactive Test Runner", Fore.CYAN, Style.BRIGHT)
        print_colored("================================\n", Fore.CYAN, Style.BRIGHT)
        
        options = {}
        
        # Test Type
        test_type_choices = [
            "Run all tests",
            "Run only unit tests",
            "Run only integration tests",
            "Run memory tests",
            "Exit"
        ]
        test_type = get_user_choice("Select test type:", test_type_choices)
        if test_type == 5:
            print_colored("Exiting. Goodbye!", Fore.YELLOW)
            sys.exit(0)
        elif test_type == 2:
            options['extra_args'] = "-m 'not integration and not memory'"
        elif test_type == 3:
            options['extra_args'] = "-m integration"
        elif test_type == 4:
            options['memory_test'] = True
        
        # Execution Mode
        execution_mode_choices = [
            "Run tests sequentially",
            "Run tests in parallel"
        ]
        execution_mode = get_user_choice("Select execution mode:", execution_mode_choices)
        options['parallel'] = (execution_mode == 2)
        
        # Reporting
        reporting_choices = [
            "Console output only",
            "Generate HTML report"
        ]
        reporting = get_user_choice("Select reporting option:", reporting_choices)
        options['html_report'] = (reporting == 2)
        
        # Confirmation
        clear_screen()
        print_colored("Test Run Configuration:", Fore.CYAN, Style.BRIGHT)
        print_colored("-------------------------", Fore.CYAN)
        print_colored(f"Test Type: {test_type_choices[test_type - 1]}", Fore.YELLOW)
        print_colored(f"Execution Mode: {execution_mode_choices[execution_mode - 1]}", Fore.YELLOW)
        print_colored(f"Reporting: {reporting_choices[reporting - 1]}", Fore.YELLOW)
        print()
        
        confirm = input("Do you want to proceed with this configuration? (y/n): ")
        if confirm.lower() == 'y':
            run_tests(options)
        
        input("\nPress Enter to return to the main menu...")

if __name__ == "__main__":
    main_menu()