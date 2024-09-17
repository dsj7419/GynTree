# GynTree: This file configures the test environment for pytest. It adds the src directory to the Python path so that the tests can access the main modules.

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
