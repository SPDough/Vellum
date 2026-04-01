#!/usr/bin/env python3
"""
Configuration validation CLI tool for Otomeshon Banking Platform

Usage:
    python scripts/validate_config.py                    # Basic validation
    python scripts/validate_config.py --health-check     # Include health checks
    python scripts/validate_config.py --env production   # Validate specific environment
    python scripts/validate_config.py --fix-permissions  # Fix file permissions
"""

import sys
import os
import argparse
import asyncio
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from app.core.config import get_settings, validate_settings
    from app.core.config_validator import ConfigValidator, ConfigHealthChecker
except ImportError as e:
    print(f"❌ Failed to import configuration modules: {e}")
    print("Make sure you're running this from the backend directory and dependencies are installed.")
    sys.exit(1)


def print_header():
    """Print application header"""
    print("🏦 Otomeshon Banking Platform - Configuration Validation")
    print("=" * 60)


def validate_file_permissions():
    """Check and fix file permissions for configuration files"""
    config_files = [
        ".env",
        ".env.example",
        "app/core/config.py",
        "requirements*.txt"
    ]

    issues = []

    for file_pattern in config_files:
        if "*" in file_pattern:
            # Handle glob patterns
            from glob import glob
            files = glob(file_pattern)
        else:
            files = [file_pattern] if os.path.exists(file_pattern) else []

        for file_path in files:
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                # Check if file is world-readable (dangerous for config files)
                if stat.st_mode & 0o044:  # Other-read or group-read
                    issues.append(f"⚠️  {file_path} is readable by others (security risk)")

                    # Fix permissions
                    try:
                        os.chmod(file_path, 0o600)  # Owner read/write only
                        print(f"✅ Fixed permissions for {file_path}")
                    except PermissionError:
                        print(f"❌ Cannot fix permissions for {file_path} (permission denied)")

    return issues


async def main():
    parser = argparse.ArgumentParser(description="Validate Otomeshon configuration")
    parser.add_argument("--health-check", action="store_true",
                       help="Run health checks for external services")
    parser.add_argument("--env", type=str,
                       help="Override environment for validation")
    parser.add_argument("--fix-permissions", action="store_true",
                       help="Check and fix file permissions")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")

    args = parser.parse_args()

    print_header()

    # Fix permissions if requested
    if args.fix_permissions:
        print("🔒 Checking file permissions...")
        permission_issues = validate_file_permissions()
        if not permission_issues:
            print("✅ File permissions are secure")
        print()

    # Override environment if specified
    if args.env:
        os.environ["ENVIRONMENT"] = args.env
        print(f"🔧 Environment override: {args.env}")

    try:
        # Load and validate settings
        settings = get_settings()

        print(f"Environment: {settings.environment}")
        print(f"App Name: {settings.app_name}")
        print(f"Log Level: {settings.log_level}")
        print()

        # Run configuration validation
        validator = ConfigValidator(settings)
        is_valid, errors, warnings = validator.validate_all()

        # Display errors
        if errors:
            print("❌ CONFIGURATION ERRORS:")
            for error in errors:
                print(f"  • {error}")
            print()

        # Display warnings
        if warnings:
            print("⚠️  CONFIGURATION WARNINGS:")
            for warning in warnings:
                print(f"  • {warning}")
            print()

        if is_valid:
            print("✅ Configuration validation passed!")
        else:
            print("❌ Configuration validation failed!")
            if not args.verbose:
                print("Run with --verbose for more details")

        # Run health checks if requested
        if args.health_check:
            print("\n🔍 Running health checks...")
            health_checker = ConfigHealthChecker(settings)

            try:
                results = await health_checker.check_all_services()

                healthy_count = 0
                total_count = len(results)

                for service, result in results.items():
                    status_icon = "✅" if result['status'] == 'healthy' else "❌"
                    print(f"  {status_icon} {service}: {result['message']}")

                    if result['status'] == 'healthy':
                        healthy_count += 1

                    if args.verbose and 'error' in result:
                        print(f"    Error: {result['error']}")

                print(f"\n📊 Health Summary: {healthy_count}/{total_count} services healthy")

            except Exception as e:
                print(f"❌ Health check failed: {e}")
                if args.verbose:
                    import traceback
                    traceback.print_exc()

        # Banking-specific checks
        if settings.environment == "production":
            print("\n🏛️  Banking Compliance Checks:")

            # Audit retention
            if settings.audit_log_retention_days >= 2555:
                print("  ✅ Audit log retention meets 7-year requirement")
            else:
                print("  ❌ Audit log retention below 7-year requirement")

            # Compliance mode
            if settings.compliance_mode != "test":
                print(f"  ✅ Compliance mode: {settings.compliance_mode}")
            else:
                print("  ❌ Compliance mode is 'test' in production")

            # Transaction limits
            if settings.max_transaction_amount <= 100000000:  # $100M
                print(f"  ✅ Transaction limit: ${settings.max_transaction_amount:,}")
            else:
                print(f"  ⚠️  High transaction limit: ${settings.max_transaction_amount:,}")

        # Exit with appropriate code
        if not is_valid:
            sys.exit(1)
        elif args.health_check and healthy_count < total_count:
            print("\n⚠️  Some health checks failed - review service connectivity")
            sys.exit(2)  # Different exit code for health check failures
        else:
            print("\n🎉 All checks passed!")
            sys.exit(0)

    except Exception as e:
        print(f"❌ Configuration error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())