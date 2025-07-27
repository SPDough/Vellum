#!/usr/bin/env python3
"""
Security vulnerability scanner for Otomeshon Banking Platform

Usage:
    python scripts/security_scan.py                    # Run all security checks
    python scripts/security_scan.py --config-only      # Check configuration only
    python scripts/security_scan.py --dependencies     # Check dependencies for vulnerabilities
    python scripts/security_scan.py --code-analysis    # Static code analysis
    python scripts/security_scan.py --fix              # Auto-fix security issues where possible
"""

import sys
import os
import subprocess
import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any
import requests

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


class SecurityScanner:
    """Comprehensive security scanner for banking applications"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.fixed_issues = []
    
    def scan_all(self, fix_issues: bool = False) -> Tuple[bool, List[str], List[str]]:
        """Run all security scans"""
        print("🔒 Otomeshon Banking Platform - Security Scan")
        print("=" * 50)
        
        # Configuration security
        self.scan_configuration_security()
        
        # Dependency vulnerabilities
        self.scan_dependency_vulnerabilities()
        
        # Code security issues
        self.scan_code_security()
        
        # File permissions
        self.scan_file_permissions(fix_issues)
        
        # Secrets detection
        self.scan_for_secrets()
        
        # Banking-specific security
        self.scan_banking_compliance()
        
        return len(self.issues) == 0, self.issues, self.warnings
    
    def scan_configuration_security(self):
        """Scan configuration for security issues"""
        print("\n🔧 Scanning Configuration Security...")
        
        # Check .env files
        env_files = ['.env', '.env.example', '.env.dev', '.env.prod']
        
        for env_file in env_files:
            if os.path.exists(env_file):
                self._check_env_file_security(env_file)
        
        # Check main configuration
        try:
            from app.core.config import get_settings
            settings = get_settings()
            self._check_config_settings(settings)
        except Exception as e:
            self.issues.append(f"Failed to load configuration: {e}")
    
    def _check_env_file_security(self, file_path: str):
        """Check environment file for security issues"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for weak secrets
            weak_patterns = [
                (r'SECRET_KEY=.*changeme', "Weak SECRET_KEY contains 'changeme'"),
                (r'JWT_SECRET_KEY=.*changeme', "Weak JWT_SECRET_KEY contains 'changeme'"),
                (r'PASSWORD=.*password', "Weak password detected"),
                (r'PASSWORD=.*admin', "Weak password detected"),
                (r'PASSWORD=.*123', "Weak password detected"),
                (r'API_KEY=.*test', "Test API key in configuration"),
                (r'=.*\bpassword\b', "Literal 'password' found in config"),
            ]
            
            for pattern, message in weak_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    self.issues.append(f"{file_path}: {message}")
            
            # Check for exposed secrets in non-example files
            if not file_path.endswith('.example'):
                secret_patterns = [
                    (r'sk-[a-zA-Z0-9]{48}', "OpenAI API key detected"),
                    (r'sk-ant-[a-zA-Z0-9]{48}', "Anthropic API key detected"),
                    (r'AKIA[0-9A-Z]{16}', "AWS access key detected"),
                    (r'[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4}', "Potential credit card number"),
                ]
                
                for pattern, message in secret_patterns:
                    if re.search(pattern, content):
                        self.issues.append(f"{file_path}: {message}")
            
            # Check file permissions
            file_stat = os.stat(file_path)
            if file_stat.st_mode & 0o044:  # World or group readable
                self.warnings.append(f"{file_path}: File is readable by others")
                
        except Exception as e:
            self.warnings.append(f"Could not check {file_path}: {e}")
    
    def _check_config_settings(self, settings):
        """Check configuration settings for security issues"""
        # Check secret keys
        if hasattr(settings, 'secret_key'):
            if len(settings.secret_key) < 32:
                self.issues.append("SECRET_KEY is shorter than 32 characters")
            
            if 'changeme' in settings.secret_key.lower():
                self.issues.append("SECRET_KEY contains 'changeme'")
        
        # Check JWT settings
        if hasattr(settings, 'jwt_secret_key'):
            if len(settings.jwt_secret_key) < 32:
                self.issues.append("JWT_SECRET_KEY is shorter than 32 characters")
        
        # Check production settings
        if hasattr(settings, 'environment') and settings.environment == 'production':
            if hasattr(settings, 'cors_origins') and '*' in str(settings.cors_origins):
                self.issues.append("CORS origins include '*' in production")
            
            if hasattr(settings, 'log_level') and settings.log_level.upper() == 'DEBUG':
                self.warnings.append("DEBUG logging enabled in production")
    
    def scan_dependency_vulnerabilities(self):
        """Scan dependencies for known vulnerabilities"""
        print("\n📦 Scanning Dependencies for Vulnerabilities...")
        
        # Check if safety is installed
        try:
            result = subprocess.run(['python', '-m', 'pip', 'list'], 
                                  capture_output=True, text=True, check=True)
            
            if 'safety' not in result.stdout:
                self.warnings.append("'safety' package not installed - cannot check for vulnerabilities")
                return
            
            # Run safety check
            safety_result = subprocess.run(['python', '-m', 'safety', 'check'], 
                                         capture_output=True, text=True)
            
            if safety_result.returncode != 0:
                # Parse safety output for vulnerabilities
                lines = safety_result.stdout.split('\n')
                for line in lines:
                    if 'vulnerability' in line.lower() or 'cve' in line.lower():
                        self.issues.append(f"Dependency vulnerability: {line.strip()}")
            else:
                print("✅ No known vulnerabilities found in dependencies")
                
        except subprocess.CalledProcessError as e:
            self.warnings.append(f"Failed to check dependencies: {e}")
        except FileNotFoundError:
            self.warnings.append("Python/pip not found in PATH")
    
    def scan_code_security(self):
        """Scan code for security issues"""
        print("\n💻 Scanning Code for Security Issues...")
        
        # Check for bandit (security linter)
        try:
            result = subprocess.run(['python', '-m', 'bandit', '--version'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                # Run bandit security scan
                bandit_result = subprocess.run([
                    'python', '-m', 'bandit', '-r', 'app/', '-f', 'json'
                ], capture_output=True, text=True)
                
                if bandit_result.stdout:
                    try:
                        bandit_data = json.loads(bandit_result.stdout)
                        for result in bandit_data.get('results', []):
                            severity = result.get('issue_severity', 'UNKNOWN')
                            confidence = result.get('issue_confidence', 'UNKNOWN')
                            issue_text = result.get('issue_text', 'Unknown issue')
                            filename = result.get('filename', 'Unknown file')
                            line_number = result.get('line_number', 0)
                            
                            if severity in ['HIGH', 'MEDIUM']:
                                self.issues.append(
                                    f"{filename}:{line_number} [{severity}] {issue_text}"
                                )
                            else:
                                self.warnings.append(
                                    f"{filename}:{line_number} [{severity}] {issue_text}"
                                )
                    except json.JSONDecodeError:
                        self.warnings.append("Failed to parse bandit output")
            else:
                self.warnings.append("Bandit not installed - install with: pip install bandit")
                
        except FileNotFoundError:
            self.warnings.append("Bandit security scanner not found")
        
        # Manual security checks
        self._check_hardcoded_secrets()
        self._check_sql_injection_patterns()
        self._check_xss_patterns()
    
    def _check_hardcoded_secrets(self):
        """Check for hardcoded secrets in code"""
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret"),
            (r'token\s*=\s*["\'][^"\']+["\']', "Hardcoded token"),
        ]
        
        for root, dirs, files in os.walk('app'):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        for pattern, message in secret_patterns:
                            matches = re.finditer(pattern, content, re.IGNORECASE)
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                self.warnings.append(f"{file_path}:{line_num} {message}")
                    except Exception:
                        continue
    
    def _check_sql_injection_patterns(self):
        """Check for potential SQL injection vulnerabilities"""
        sql_patterns = [
            (r'execute\s*\(\s*["\'][^"\']*%[sd][^"\']*["\']', "Potential SQL injection"),
            (r'query\s*\(\s*["\'][^"\']*\+[^"\']*["\']', "SQL string concatenation"),
            (r'\.format\s*\([^)]*\).*execute', "String formatting in SQL"),
        ]
        
        for root, dirs, files in os.walk('app'):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        for pattern, message in sql_patterns:
                            matches = re.finditer(pattern, content, re.IGNORECASE)
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                self.warnings.append(f"{file_path}:{line_num} {message}")
                    except Exception:
                        continue
    
    def _check_xss_patterns(self):
        """Check for potential XSS vulnerabilities"""
        xss_patterns = [
            (r'render_template_string\s*\([^)]*request\.[^)]*\)', "Template injection risk"),
            (r'Markup\s*\([^)]*request\.[^)]*\)', "Unsafe markup from request"),
            (r'innerHTML\s*=\s*[^;]*request', "Direct HTML injection"),
        ]
        
        for root, dirs, files in os.walk('app'):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        for pattern, message in xss_patterns:
                            matches = re.finditer(pattern, content, re.IGNORECASE)
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                self.warnings.append(f"{file_path}:{line_num} {message}")
                    except Exception:
                        continue
    
    def scan_file_permissions(self, fix_issues: bool = False):
        """Scan and optionally fix file permissions"""
        print("\n📁 Scanning File Permissions...")
        
        sensitive_files = [
            '.env', '.env.dev', '.env.prod',
            'app/core/config.py',
            'scripts/*.py'
        ]
        
        for pattern in sensitive_files:
            if '*' in pattern:
                import glob
                files = glob.glob(pattern)
            else:
                files = [pattern] if os.path.exists(pattern) else []
            
            for file_path in files:
                try:
                    file_stat = os.stat(file_path)
                    mode = file_stat.st_mode
                    
                    # Check if file is world-readable or group-readable
                    if mode & 0o044:
                        self.issues.append(f"{file_path}: File is readable by others")
                        
                        if fix_issues:
                            os.chmod(file_path, 0o600)  # Owner read/write only
                            self.fixed_issues.append(f"Fixed permissions for {file_path}")
                    
                    # Check if Python scripts are not executable
                    if file_path.endswith('.py') and file_path.startswith('scripts/'):
                        if not mode & 0o100:
                            self.warnings.append(f"{file_path}: Script not executable")
                            
                            if fix_issues:
                                os.chmod(file_path, 0o700)  # Owner rwx
                                self.fixed_issues.append(f"Made {file_path} executable")
                                
                except Exception as e:
                    self.warnings.append(f"Could not check permissions for {file_path}: {e}")
    
    def scan_for_secrets(self):
        """Scan for exposed secrets in code and config"""
        print("\n🔍 Scanning for Exposed Secrets...")
        
        secret_patterns = {
            'OpenAI API Key': r'sk-[a-zA-Z0-9]{48}',
            'Anthropic API Key': r'sk-ant-[a-zA-Z0-9]{48}',
            'AWS Access Key': r'AKIA[0-9A-Z]{16}',
            'AWS Secret Key': r'[A-Za-z0-9/+=]{40}',
            'JWT Token': r'eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*',
            'Private Key': r'-----BEGIN (?:RSA )?PRIVATE KEY-----',
            'Generic Password': r'password["\s]*[:=]["\s]*[^"\s]+',
        }
        
        excluded_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv'}
        
        for root, dirs, files in os.walk('.'):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.json', '.yml', '.yaml', '.env')):
                    file_path = os.path.join(root, file)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        for secret_type, pattern in secret_patterns.items():
                            matches = re.finditer(pattern, content, re.IGNORECASE)
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                # Don't report secrets in example files
                                if not file_path.endswith('.example'):
                                    self.issues.append(
                                        f"{file_path}:{line_num} Potential {secret_type} detected"
                                    )
                    except Exception:
                        continue
    
    def scan_banking_compliance(self):
        """Scan for banking-specific security compliance"""
        print("\n🏦 Scanning Banking Security Compliance...")
        
        # Check audit logging implementation
        audit_patterns = [
            'audit_logger',
            'log_transaction',
            'log_access',
            'AuditLogger'
        ]
        
        audit_found = False
        for root, dirs, files in os.walk('app'):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        for pattern in audit_patterns:
                            if pattern in content:
                                audit_found = True
                                break
                    except Exception:
                        continue
        
        if not audit_found:
            self.issues.append("No audit logging implementation found")
        
        # Check for transaction signing
        signing_patterns = ['digital_signature', 'hash_transaction', 'sign_transaction']
        signing_found = any(
            pattern in open(f'app/{file}', 'r').read() 
            for file in os.listdir('app') 
            if file.endswith('.py')
            for pattern in signing_patterns
        )
        
        if not signing_found:
            self.warnings.append("No transaction signing implementation found")
        
        # Check for data encryption
        encryption_patterns = ['encrypt', 'decrypt', 'cipher', 'cryptography']
        encryption_found = False
        
        try:
            for root, dirs, files in os.walk('app'):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        for pattern in encryption_patterns:
                            if pattern in content.lower():
                                encryption_found = True
                                break
        except Exception:
            pass
        
        if not encryption_found:
            self.warnings.append("No data encryption implementation found")


def main():
    parser = argparse.ArgumentParser(description="Security scanner for Otomeshon")
    parser.add_argument("--config-only", action="store_true", help="Check configuration only")
    parser.add_argument("--dependencies", action="store_true", help="Check dependencies only")
    parser.add_argument("--code-analysis", action="store_true", help="Static code analysis only")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues where possible")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    scanner = SecurityScanner()
    
    if args.config_only:
        scanner.scan_configuration_security()
    elif args.dependencies:
        scanner.scan_dependency_vulnerabilities()
    elif args.code_analysis:
        scanner.scan_code_security()
    else:
        success, issues, warnings = scanner.scan_all(args.fix)
    
    # Report results
    print("\n" + "=" * 50)
    print("🔒 Security Scan Results")
    print("=" * 50)
    
    if scanner.issues:
        print("\n❌ SECURITY ISSUES:")
        for issue in scanner.issues:
            print(f"  • {issue}")
    
    if scanner.warnings:
        print("\n⚠️  SECURITY WARNINGS:")
        for warning in scanner.warnings:
            print(f"  • {warning}")
    
    if scanner.fixed_issues:
        print("\n🔧 ISSUES FIXED:")
        for fix in scanner.fixed_issues:
            print(f"  • {fix}")
    
    if not scanner.issues and not scanner.warnings:
        print("\n✅ No security issues found!")
    
    # Security recommendations
    print("\n📋 Security Recommendations:")
    print("  • Install security tools: pip install bandit safety")
    print("  • Run regular dependency vulnerability scans")
    print("  • Enable audit logging in production")
    print("  • Implement data encryption for sensitive fields")
    print("  • Use secure session management")
    print("  • Regular security penetration testing")
    
    # Exit with appropriate code
    sys.exit(1 if scanner.issues else 0)


if __name__ == "__main__":
    main()