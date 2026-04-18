import sys
import argparse
from runqc.menu import QualityCheckMenu

def parse_args():
    parser = argparse.ArgumentParser(description="GynTree Quality Checker")
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode with detailed logging'
    )
    parser.add_argument(
        '--run-all',
        action='store_true',
        help='Run all checks non-interactively'
    )
    return parser.parse_args()

def main():
    args = parse_args()
    menu = QualityCheckMenu(debug=args.debug, non_interactive=args.run_all)
    menu.run()

if __name__ == "__main__":
    main()
