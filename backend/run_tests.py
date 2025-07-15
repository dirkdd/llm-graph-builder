#!/usr/bin/env python3
"""
Test runner for document type slots functionality.

Runs all tests related to the document type slots feature including:
- Backend unit tests
- Integration tests
- API endpoint tests

Usage:
    python run_tests.py
    python run_tests.py --verbose
    python run_tests.py --specific test_document_type_slots
"""

import sys
import os
import subprocess
import argparse

def run_tests(verbose=False, specific_test=None, coverage=False):
    """Run the test suite with specified options."""
    
    # Ensure we're in the backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    # Activate virtual environment
    venv_activate = os.path.join('venv', 'bin', 'activate')
    if os.path.exists(venv_activate):
        print("Virtual environment found, activating...")
        # For Unix-like systems
        activate_cmd = f"source {venv_activate}"
    else:
        print("Virtual environment not found, using system Python")
        activate_cmd = ""
    
    # Build test command
    test_cmd_parts = []
    
    if activate_cmd:
        test_cmd_parts.append(activate_cmd)
        test_cmd_parts.append("&&")
    
    # Use pytest if available, otherwise unittest
    try:
        import pytest
        if coverage:
            test_cmd_parts.extend(["python3", "-m", "pytest", "tests/", "--cov=src", "--cov-report=html"])
        else:
            test_cmd_parts.extend(["python3", "-m", "pytest", "tests/"])
        
        if verbose:
            test_cmd_parts.append("-v")
        
        if specific_test:
            test_cmd_parts.extend(["-k", specific_test])
            
    except ImportError:
        # Fall back to unittest
        if specific_test:
            test_cmd_parts.extend(["python3", "-m", "unittest", f"tests.{specific_test}"])
        else:
            test_cmd_parts.extend(["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"])
        
        if verbose:
            test_cmd_parts.append("-v")
    
    test_cmd = " ".join(test_cmd_parts)
    
    print(f"Running command: {test_cmd}")
    print("-" * 50)
    
    # Execute the test command
    try:
        result = subprocess.run(test_cmd, shell=True, check=False)
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run document type slots tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-s", "--specific", help="Run specific test (e.g., test_document_type_slots)")
    parser.add_argument("-c", "--coverage", action="store_true", help="Run with coverage report")
    parser.add_argument("--list", action="store_true", help="List available tests")
    
    args = parser.parse_args()
    
    if args.list:
        print("Available test files:")
        test_dir = os.path.join(os.path.dirname(__file__), "tests")
        for file in os.listdir(test_dir):
            if file.startswith("test_") and file.endswith(".py"):
                print(f"  - {file[:-3]}")  # Remove .py extension
        return 0
    
    print("Document Type Slots Test Runner")
    print("=" * 40)
    
    # Run the tests
    exit_code = run_tests(
        verbose=args.verbose,
        specific_test=args.specific,
        coverage=args.coverage
    )
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code: {exit_code}")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())