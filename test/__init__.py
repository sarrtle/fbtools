"""Append root folder to test folder for easy imports."""

import sys
import os

# Get the root directory of the project
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))
