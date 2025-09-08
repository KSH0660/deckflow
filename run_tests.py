#!/usr/bin/env python3
"""Test runner script for deckflow business logic tests."""

import sys
import subprocess
from pathlib import Path


def run_command(cmd: list[str]) -> int:
    """Run command and return exit code."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def main():
    """Main test runner."""
    print("🧪 Deckflow Business Logic Test Suite")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Error: Must run from project root directory")
        return 1
    
    # Parse command line arguments
    test_type = "all"
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
    
    exit_code = 0
    
    if test_type in ("all", "unit"):
        print("\n🔧 Running Unit Tests")
        print("-" * 30)
        cmd = [
            "python", "-m", "pytest", 
            "tests/unit/", 
            "-v",
            "--tb=short",
            "-x"  # Stop on first failure
        ]
        exit_code = run_command(cmd)
        
        if exit_code != 0:
            print("❌ Unit tests failed")
            if test_type == "all":
                print("Skipping integration tests due to unit test failures")
                return exit_code
    
    if test_type in ("all", "integration"):
        print("\n🔗 Running Integration Tests")
        print("-" * 35)
        cmd = [
            "python", "-m", "pytest", 
            "tests/integration/",
            "-v",
            "--tb=short",
            "-m", "integration"
        ]
        integration_exit = run_command(cmd)
        exit_code = max(exit_code, integration_exit)
    
    if test_type == "coverage":
        print("\n📊 Running Tests with Coverage")
        print("-" * 35)
        cmd = [
            "python", "-m", "pytest", 
            "tests/",
            "--cov=app.service",
            "--cov-report=html",
            "--cov-report=term-missing",
            "-v"
        ]
        exit_code = run_command(cmd)
    
    if test_type == "specific":
        if len(sys.argv) < 3:
            print("❌ Error: Specify test path for 'specific' mode")
            print("Example: python run_tests.py specific tests/unit/service/deck_planning/")
            return 1
        
        test_path = sys.argv[2]
        print(f"\n🎯 Running Specific Tests: {test_path}")
        print("-" * 40)
        cmd = [
            "python", "-m", "pytest", 
            test_path,
            "-v",
            "--tb=short"
        ]
        exit_code = run_command(cmd)
    
    # Summary
    print("\n" + "=" * 50)
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    
    print("\n📖 Test Commands Reference:")
    print("  python run_tests.py              # Run all tests")  
    print("  python run_tests.py unit         # Run unit tests only")
    print("  python run_tests.py integration  # Run integration tests only") 
    print("  python run_tests.py coverage     # Run with coverage report")
    print("  python run_tests.py specific <path>  # Run specific test file/directory")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
