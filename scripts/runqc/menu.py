import os
import subprocess
import sys
from typing import List
from .checkers import CheckerFactory
from .reporters import Reporter
from .models import CheckResult
from .logger import setup_logging
import logging

logger = logging.getLogger(__name__)

class QualityCheckMenu:
    def __init__(self, debug: bool = False, non_interactive: bool = False):
        self.checker_factory = CheckerFactory()
        self.reporter = Reporter()
        self.debug = debug
        self.non_interactive = non_interactive
        self.setup()

    def setup(self):
        # Initialize logging
        setup_logging(debug=self.debug)
        logger.info("QualityCheckMenu initialized.")

    def display_menu(self):
        print("\nQuality Check Menu:")
        print("1. Run all checks")
        print("2. Run a specific check")
        print("3. Fix issues")
        print("4. View Detailed Report")
        print("5. Exit")

    def run(self):
        if self.non_interactive:
            self.run_all_checks()
            # Exit with appropriate status code
            sys.exit(0 if self.all_checks_passed else 1)
        else:
            while True:
                self.display_menu()
                choice = input("\nEnter your choice: ").strip()
                if choice == '1':
                    self.run_all_checks()
                elif choice == '2':
                    self.run_specific_check()
                elif choice == '3':
                    self.fix_issues()
                elif choice == '4':
                    self.view_detailed_report()
                elif choice == '5':
                    print("Exiting...")
                    sys.exit(0)
                else:
                    print("Invalid choice. Please try again.")

    def run_all_checks(self):
        print("\nRunning all checks...")
        checkers = self.checker_factory.get_all_checkers()
        results: List[CheckResult] = []
        self.all_checks_passed = True  # Track if all checks passed
        for checker in checkers:
            result = checker.run()
            results.append(result)
            if not result.success:
                self.all_checks_passed = False
            status = "PASSED" if result.success else "FAILED"
            print(
                f"{checker.name}: {status} ({result.error_count} issues)"
            )
        self.reporter.report(results)
        if self.non_interactive:
            # Exit with appropriate status code
            sys.exit(0 if self.all_checks_passed else 1)

    def run_specific_check(self):
        print("\nAvailable Checkers:")
        checkers = self.checker_factory.get_all_checkers()
        for idx, checker in enumerate(checkers, start=1):
            print(f"{idx}. {checker.name}")
        choice = input(
            "\nEnter the number of the checker to run: "
        ).strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(checkers):
                checker = checkers[idx]
                print(f"\nRunning {checker.name}...")
                result = checker.run()
                status = "PASSED" if result.success else "FAILED"
                print(
                    f"{checker.name}: {status} ({result.error_count} issues)"
                )
                self.reporter.report([result])
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a valid number.")

    def fix_issues(self):
        print("\nFixing issues...")
        fixable_checkers = self.checker_factory.get_fixable_checkers()
        if not fixable_checkers:
            print("No fixable checkers available.")
            return

        proceed = input(
            "Do you want to proceed with fixing issues? (y/n): "
        ).strip().lower()
        if proceed != 'y':
            print("Fixing aborted.")
            return

        results: List[CheckResult] = []
        for checker in fixable_checkers:
            result = checker.fix()
            results.append(result)
            status = "FIXED" if result.success else "FAILED TO FIX"
            print(f"{checker.name}: {status}")
        self.reporter.report(results)

    def view_detailed_report(self):
        detailed_report = self.reporter.detailed_report_file
        if not detailed_report.exists():
            print("\nNo detailed report found. Please run the checks first.")
            return
        print(
            f"\nOpening detailed report at {detailed_report.resolve()}..."
        )
        try:
            if sys.platform.startswith('darwin'):
                subprocess.call(('open', str(detailed_report)))
            elif os.name == 'nt':
                os.startfile(str(detailed_report))
            elif os.name == 'posix':
                subprocess.call(('xdg-open', str(detailed_report)))
        except Exception as e:
            logger.error(f"Failed to open detailed report: {e}")
            print("Failed to open detailed report.")
