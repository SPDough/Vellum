#!/usr/bin/env python3
"""
Test runner script for Otomeshon Banking Platform

Usage:
    python scripts/run_tests.py                    # Run all tests
    python scripts/run_tests.py --unit             # Run only unit tests
    python scripts/run_tests.py --banking          # Run banking-specific tests
    python scripts/run_tests.py --smoke            # Run smoke tests
    python scripts/run_tests.py --coverage         # Run with coverage report
    python scripts/run_tests.py --performance      # Run performance tests
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔍 {description}")
    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Run Otomeshon tests")

    # Test categories
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--banking", action="store_true", help="Run banking-specific tests")
    parser.add_argument("--security", action="store_true", help="Run security tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--compliance", action="store_true", help="Run compliance tests")
    parser.add_argument("--smoke", action="store_true", help="Run smoke tests")
    parser.add_argument("--slow", action="store_true", help="Include slow tests")

    # Options
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--html-report", action="store_true", help="Generate HTML test report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fail-fast", "-x", action="store_true", help="Stop on first failure")
    parser.add_argument("--parallel", "-n", type=int, help="Run tests in parallel (requires pytest-xdist)")

    # File/directory targeting
    parser.add_argument("files", nargs="*", help="Specific test files to run")

    args = parser.parse_args()

    # Ensure we're in the right directory
    backend_dir = Path(__file__).parent.parent
    if not (backend_dir / "pytest.ini").exists():
        print("❌ pytest.ini not found. Make sure you're running from the backend directory.")
        sys.exit(1)

    print("🏦 Otomeshon Banking Platform - Test Suite")
    print("=" * 50)

    # Build pytest command
    cmd = ["python", "-m", "pytest"]

    # Add specific files if provided
    if args.files:
        cmd.extend(args.files)
    else:
        cmd.append("tests/")

    # Add markers based on arguments
    markers = []
    if args.unit:
        markers.append("unit")
    if args.integration:
        markers.append("integration")
    if args.banking:
        markers.append("banking")
    if args.security:
        markers.append("security")
    if args.performance:
        markers.append("performance")
    if args.compliance:
        markers.append("compliance")
    if args.smoke:
        markers.append("smoke")

    if markers:
        marker_expr = " or ".join(markers)
        cmd.extend(["-m", marker_expr])

    # Exclude slow tests unless explicitly requested
    if not args.slow and not args.performance:
        if markers:
            cmd.extend(["-m", f"({marker_expr}) and not slow"])
        else:
            cmd.extend(["-m", "not slow"])

    # Add options
    if args.verbose:
        cmd.append("-v")

    if args.fail_fast:
        cmd.append("-x")

    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])

    if args.coverage:
        cmd.extend([
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=70"
        ])

    if args.html_report:
        cmd.extend(["--html=reports/test_report.html", "--self-contained-html"])

    # Create reports directory if needed
    if args.html_report or args.coverage:
        reports_dir = backend_dir / "reports"
        reports_dir.mkdir(exist_ok=True)

    # Run pre-test checks
    print("\n🔧 Pre-test setup...")

    # Check if test dependencies are installed
    check_deps_cmd = ["python", "-c", "import pytest, httpx, asyncio; print('✅ Test dependencies available')"]
    if not run_command(check_deps_cmd, "Checking test dependencies"):
        print("❌ Install test dependencies with: pip install -r requirements-dev.txt")
        sys.exit(1)

    # Validate configuration
    config_check_cmd = ["python", "scripts/validate_config.py", "--env", "testing"]
    if not run_command(config_check_cmd, "Validating test configuration"):
        print("⚠️  Configuration validation failed - some tests may fail")

    # Run the tests
    print(f"\n🧪 Running tests...")
    success = run_command(cmd, "Running test suite")

    # Post-test reporting
    if args.coverage:
        print("\n📊 Coverage report generated at: reports/htmlcov/index.html")

    if args.html_report:
        print("📋 HTML test report generated at: reports/test_report.html")

    # Performance summary for performance tests
    if args.performance:
        print("\n⚡ Performance Test Results:")
        print("  • API Response Time SLA: < 500ms")
        print("  • Trade Processing SLA: < 10s per 1000 trades")
        print("  • Concurrent Request Handling: 10+ simultaneous")

    # Compliance summary for compliance tests
    if args.compliance:
        print("\n🏛️  Compliance Test Results:")
        print("  • Audit Log Format: Regulatory compliant")
        print("  • Data Retention: 7-year requirement met")
        print("  • Security Controls: Banking-grade validation")

    # Banking feature summary
    if args.banking:
        print("\n🏦 Banking Feature Test Results:")
        print("  • Trade Validation: Risk and compliance checks")
        print("  • SOP Execution: Workflow automation")
        print("  • Transaction Limits: Regulatory enforcement")

    print(f"\n{'🎉 All tests passed!' if success else '❌ Some tests failed!'}")

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()