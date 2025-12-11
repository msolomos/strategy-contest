#!/usr/bin/env python3
"""
COMPREHENSIVE SECURITY AUDIT FRAMEWORK V2
Trading Strategy Contest - Final Evaluation

Enhanced framework with:
- True allow-list import checking
- AST-based file/network access detection
- Non-Python executable detection
- Obfuscation/self-modifying code detection
- Secrets/environment access detection
- Full JSON issue details export
- CLI parameterization
"""

import os
import re
import sys
import ast
import json
import base64
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class SecurityIssue:
    """Represents a security vulnerability or risk."""
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # Code Injection, File System, Network, etc.
    description: str
    file_path: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    recommendation: Optional[str] = None

@dataclass
class SecurityAuditResult:
    """Complete security audit results for one submission."""
    submission_id: str
    participant: str
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    security_score: float  # 0-100, higher is better
    passed: bool
    issues: List[SecurityIssue]
    scan_timestamp: str
    files_scanned: List[str]

class SecurityAuditor:
    """Comprehensive security scanner for trading strategy submissions."""

    def __init__(self):
        self.dangerous_patterns = self._initialize_patterns()
        self.safe_imports = self._initialize_safe_imports()
        self.executable_extensions = {'.sh', '.bat', '.ps1', '.cmd', '.exe', '.dll', '.so', '.pyd', '.jar', '.class'}
        self.suspicious_extensions = {'.bin', '.dat', '.tmp', '.log'}
        self.results = []

    def _initialize_patterns(self) -> Dict[str, Dict]:
        """Define dangerous code patterns to detect."""
        return {
            'code_injection': {
                'patterns': [
                    r'\bexec\s*\(',
                    r'\beval\s*\(',
                    r'\bcompile\s*\(',
                    r'__import__\s*\(',
                ],
                'severity': 'CRITICAL',
                'category': 'Code Injection'
            },
            'system_access': {
                'patterns': [
                    r'\bos\.system\s*\(',
                    r'\bos\.popen\s*\(',
                    r'\bos\.spawn\w*\s*\(',
                    r'\bcommands\.',
                ],
                'severity': 'CRITICAL',
                'category': 'System Access'
            },
            'file_system_write': {
                'patterns': [
                    r'open\s*\([^)]*["\'][wa]["\']',
                ],
                'severity': 'MEDIUM',  # Reduced from HIGH
                'category': 'File System Write'
            },
            'network_access': {
                'patterns': [
                    r'\brequests\.',
                    r'\burllib\.',
                    r'\bsocket\.',
                    r'\bhttp\.',
                    r'\bsmtplib\.',
                    r'\bftplib\.',
                ],
                'severity': 'HIGH',
                'category': 'Network Access'
            },
            'reflection': {
                'patterns': [
                    r'\bgetattr\s*\(',
                    r'\bsetattr\s*\(',
                    r'\bhasattr\s*\(',
                    r'\bdelattr\s*\(',
                    r'\bglobals\s*\(\)',
                    r'\blocals\s*\(\)',
                    r'\bvars\s*\(',
                ],
                'severity': 'LOW',
                'category': 'Reflection/Dynamic Access'
            }
        }

    def _initialize_safe_imports(self) -> List[str]:
        """Define whitelist of safe imports for trading strategies."""
        return [
            # Python standard library - core
            'os', 'sys', 'datetime', 'time', 'math', 'statistics',
            'collections', 'typing', 'dataclasses', 'pathlib',
            'json', 'csv', 'logging', 'argparse', 'warnings',

            # Python standard library - data structures
            'queue', 'heapq', 'bisect', 'array', 'copy',
            'pickle', 'shelve', 'gzip', 'zipfile',

            # Numerical and data analysis
            'numpy', 'pandas', 'scipy', 'sklearn', 'statsmodels',

            # Finance and market data
            'yfinance', 'ccxt', 'alpha_vantage', 'quandl', 'bloomberg',
            'investpy', 'fredapi', 'pandas_datareader',

            # Technical analysis
            'talib', 'ta', 'finta', 'tulip', 'tulipy',

            # Plotting and visualization
            'matplotlib', 'seaborn', 'plotly', 'bokeh',

            # Base template imports
            'strategy_interface', 'exchange_interface', 'universal_bot',

            # Encoding (but monitored for obfuscation)
            'base64', 'hashlib', 'hmac', 'uuid',

            # Testing
            'unittest', 'pytest', 'mock',

            # Development
            '__future__', 'abc', 'enum', 'functools', 'itertools',
            'operator', 'random', 'secrets', 'string', 're'
        ]

    def scan_submission(self, submission_path: Path) -> SecurityAuditResult:
        """Scan a complete submission directory for security issues."""
        print(f"[SCAN] Starting security audit of {submission_path.name}...")

        # Extract submission ID and participant from path
        submission_id = submission_path.name
        participant = self._extract_participant_name(submission_path)

        all_issues = []
        files_scanned = []

        # 1. Check for suspicious non-Python files
        non_python_issues = self._check_non_python_files(submission_path)
        all_issues.extend(non_python_issues)

        # 2. Scan all Python files (exclude base-bot-template)
        python_files = [f for f in submission_path.rglob("*.py")
                       if "base-bot-template" not in str(f)]
        files_scanned = [str(f.relative_to(submission_path)) for f in python_files]

        for py_file in python_files:
            try:
                file_issues = self._scan_python_file(py_file)
                all_issues.extend(file_issues)
            except Exception as e:
                all_issues.append(SecurityIssue(
                    severity='HIGH',
                    category='Scan Error',
                    description=f'Failed to scan file: {str(e)}',
                    file_path=str(py_file.relative_to(submission_path)),
                    recommendation='Αρχείο μη αναγνώσιμο ή κατεστραμμένο'
                ))

        # Calculate security metrics
        critical_count = sum(1 for issue in all_issues if issue.severity == 'CRITICAL')
        high_count = sum(1 for issue in all_issues if issue.severity == 'HIGH')
        medium_count = sum(1 for issue in all_issues if issue.severity == 'MEDIUM')
        low_count = sum(1 for issue in all_issues if issue.severity == 'LOW')

        # Security scoring: Start at 100, subtract points based on severity
        security_score = 100.0
        security_score -= critical_count * 40  # CRITICAL: -40 points each
        security_score -= high_count * 15      # HIGH: -15 points each
        security_score -= medium_count * 5     # MEDIUM: -5 points each
        security_score -= low_count * 1        # LOW: -1 point each
        security_score = max(0.0, security_score)

        # Pass/fail criteria: No CRITICAL issues, security score >= 60
        passed = critical_count == 0 and security_score >= 60.0

        result = SecurityAuditResult(
            submission_id=submission_id,
            participant=participant,
            total_issues=len(all_issues),
            critical_issues=critical_count,
            high_issues=high_count,
            medium_issues=medium_count,
            low_issues=low_count,
            security_score=security_score,
            passed=passed,
            issues=all_issues,
            scan_timestamp=datetime.now().isoformat(),
            files_scanned=files_scanned
        )

        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {submission_id}: {security_score:.1f}/100 "
              f"({critical_count}C/{high_count}H/{medium_count}M/{low_count}L)")

        return result

    def _check_non_python_files(self, submission_path: Path) -> List[SecurityIssue]:
        """Check for suspicious non-Python executable files."""
        issues = []

        for file_path in submission_path.rglob("*"):
            if not file_path.is_file():
                continue

            # Skip base-bot-template folder
            if "base-bot-template" in str(file_path):
                continue

            file_ext = file_path.suffix.lower()
            file_size = file_path.stat().st_size
            relative_path = str(file_path.relative_to(submission_path))

            # Check for executable files
            if file_ext in self.executable_extensions:
                issues.append(SecurityIssue(
                    severity='CRITICAL',
                    category='Executable Artifact',
                    description=f'Executable file present in submission: {file_ext}',
                    file_path=relative_path,
                    recommendation='Αφαίρεσε όλα τα εκτελέσιμα αρχεία - μόνο Python κώδικας επιτρέπεται'
                ))

            # Check for suspiciously large files (>1MB) that aren't Python
            elif file_ext != '.py' and file_size > 1024 * 1024:
                issues.append(SecurityIssue(
                    severity='HIGH',
                    category='Suspicious Large File',
                    description=f'Large non-Python file ({file_size/1024/1024:.1f}MB): {file_path.name}',
                    file_path=relative_path,
                    recommendation='Εξήγησε την ανάγκη για αυτό το μεγάλο αρχείο ή αφαίρεσέ το'
                ))

            # Check for suspicious file types
            elif file_ext in self.suspicious_extensions:
                issues.append(SecurityIssue(
                    severity='MEDIUM',
                    category='Suspicious File Type',
                    description=f'Potentially suspicious file type: {file_ext}',
                    file_path=relative_path,
                    recommendation='Τεκμηρίωσε την ανάγκη για αυτό το αρχείο'
                ))

        return issues

    def _scan_python_file(self, file_path: Path) -> List[SecurityIssue]:
        """Perform comprehensive security scan of a Python file."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                content = file_path.read_text(encoding='latin-1')
            except Exception:
                return [SecurityIssue(
                    severity='HIGH',
                    category='File Read Error',
                    description='Cannot read file - potential encoding issues or corruption',
                    file_path=str(file_path),
                    recommendation='Επιβεβαίωσε ότι το αρχείο είναι έγκυρος Python κώδικας'
                )]

        all_issues = []

        # 1. Regex pattern matching (excluding comments)
        pattern_issues = self._check_dangerous_patterns(content, str(file_path))
        all_issues.extend(pattern_issues)

        # 2. AST analysis for deeper inspection
        ast_issues = self._analyze_ast(content, str(file_path))
        all_issues.extend(ast_issues)

        # 3. Check for obfuscation
        obfuscation_issues = self._check_obfuscation(content, str(file_path))
        all_issues.extend(obfuscation_issues)

        return all_issues

    def _check_dangerous_patterns(self, content: str, file_path: str) -> List[SecurityIssue]:
        """Check for dangerous patterns using regex, excluding comments."""
        issues = []
        lines = content.splitlines()

        for category_name, category_info in self.dangerous_patterns.items():
            for pattern in category_info['patterns']:
                for line_num, line in enumerate(lines, 1):
                    # Skip comment lines
                    stripped_line = line.strip()
                    if stripped_line.startswith('#'):
                        continue

                    if re.search(pattern, line, re.IGNORECASE):
                        issues.append(SecurityIssue(
                            severity=category_info['severity'],
                            category=category_info['category'],
                            description=f'Dangerous pattern detected: {pattern}',
                            file_path=file_path,
                            line_number=line_num,
                            code_snippet=line.strip(),
                            recommendation=f'Αφαίρεσε ή τεκμηρίωσε την ανάγκη για {category_name}'
                        ))

        return issues

    def _analyze_ast(self, content: str, file_path: str) -> List[SecurityIssue]:
        """Perform AST-based analysis for security issues."""
        issues = []

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return [SecurityIssue(
                severity='HIGH',
                category='Syntax Error',
                description=f'Python syntax error: {str(e)}',
                file_path=file_path,
                line_number=getattr(e, 'lineno', None),
                recommendation='Διόρθωσε τα syntax errors'
            )]

        content_lines = content.splitlines()

        for node in ast.walk(tree):
            # Check imports (allow-list enforcement)
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                import_issues = self._check_imports_allowlist(node, content_lines, file_path)
                issues.extend(import_issues)

            # Check function calls for dangerous operations
            elif isinstance(node, ast.Call):
                call_issues = self._check_dangerous_calls(node, content_lines, file_path)
                issues.extend(call_issues)

            # Check attribute access (environment, file operations)
            elif isinstance(node, ast.Attribute):
                attr_issues = self._check_attribute_access(node, content_lines, file_path)
                issues.extend(attr_issues)

        return issues

    def _check_imports_allowlist(self, node: ast.AST, content_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check imports against allow-list."""
        issues = []
        modules = []

        if isinstance(node, ast.Import):
            modules = [alias.name.split('.')[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules = [node.module.split('.')[0]]

        for mod in modules:
            full_line = content_lines[node.lineno - 1].strip() if node.lineno <= len(content_lines) else ""

            # Check against allow-list (skip common contest submission modules)
            is_contest_common = mod in ['your_strategy', 'startup', 'backtest_runner', 'optimizer']

            # Check if it's a strategy import pattern (suspicious if importing multiple strategies)
            is_strategy_import = any(pattern in mod.lower() for pattern in [
                'strategy', 'champion', 'winner', 'ultimate', 'final', 'victory',
                'hybrid', 'aggressive', 'rapid', 'smart', 'breakout', 'momentum'
            ])

            if not any(mod.startswith(safe) for safe in self.safe_imports) and not is_contest_common:
                if is_strategy_import:
                    # Strategy imports are more suspicious - MEDIUM instead of LOW
                    issues.append(SecurityIssue(
                        severity='MEDIUM',
                        category='Strategy Import Collection',
                        description=f'Import of strategy module: {mod} (potential strategy collection)',
                        file_path=file_path,
                        line_number=node.lineno,
                        code_snippet=full_line,
                        recommendation='Contest submissions should contain one strategy, not collections'
                    ))
                else:
                    issues.append(SecurityIssue(
                        severity='LOW',  # Reduced from MEDIUM
                        category='Unapproved Imports',
                        description=f'Import of non-whitelisted module: {mod}',
                        file_path=file_path,
                        line_number=node.lineno,
                        code_snippet=full_line,
                        recommendation='Αφαίρεσε ή τεκμηρίωσε ρητά την ανάγκη χρήσης αυτού του module'
                    ))

        return issues

    def _check_dangerous_calls(self, node: ast.Call, content_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check for dangerous function calls via AST."""
        issues = []
        full_line = content_lines[node.lineno - 1].strip() if node.lineno <= len(content_lines) else ""

        # Check for exec/eval/compile
        if isinstance(node.func, ast.Name):
            if node.func.id in ('exec', 'eval', 'compile', '__import__'):
                issues.append(SecurityIssue(
                    severity='CRITICAL',
                    category='Code Injection',
                    description=f'Dangerous code execution function: {node.func.id}',
                    file_path=file_path,
                    line_number=node.lineno,
                    code_snippet=full_line,
                    recommendation='Αφαίρεσε την χρήση δυναμικής εκτέλεσης κώδικα'
                ))

        # Check for subprocess calls (with yfinance exception)
        elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if node.func.value.id == 'subprocess':
                # Check if it's a yfinance install
                is_yfinance_install = False
                if node.args:
                    # Look for yfinance in the command arguments
                    for arg in node.args:
                        if isinstance(arg, ast.List):
                            arg_strings = []
                            for item in arg.elts:
                                if isinstance(item, ast.Constant):
                                    arg_strings.append(str(item.value))
                            command_line = ' '.join(arg_strings)
                            if ('pip' in command_line and 'install' in command_line and
                                'yfinance' in command_line and 'yfinance' == command_line.split()[-1]):
                                is_yfinance_install = True
                                break

                if is_yfinance_install:
                    issues.append(SecurityIssue(
                        severity='LOW',
                        category='Dependency Management',
                        description='Runtime pip install for yfinance (contest acceptable)',
                        file_path=file_path,
                        line_number=node.lineno,
                        code_snippet=full_line,
                        recommendation='Καλύτερα να προ-εγκαταστήσεις τα dependencies, αλλά αποδεκτό για yfinance'
                    ))
                else:
                    issues.append(SecurityIssue(
                        severity='CRITICAL',
                        category='System Access',
                        description='Subprocess call detected - potential system access',
                        file_path=file_path,
                        line_number=node.lineno,
                        code_snippet=full_line,
                        recommendation='Αφαίρεσε τις subprocess calls εκτός αν είναι απολύτως απαραίτητες'
                    ))

        # Check for file operations (more intelligent detection)
        elif isinstance(node.func, ast.Name) and node.func.id == 'open':
            if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                mode = str(node.args[1].value)
                if any(m in mode for m in ('w', 'a', 'x')):
                    # Check if it's a report/log file (less severe)
                    is_report_file = False
                    if len(node.args) >= 1 and isinstance(node.args[0], ast.Constant):
                        filename = str(node.args[0].value).lower()
                        if any(report_ext in filename for report_ext in ['.md', '.txt', '.log', '.csv', '.json', 'report', 'backtest']):
                            is_report_file = True

                    severity = 'MEDIUM' if is_report_file else 'HIGH'
                    issues.append(SecurityIssue(
                        severity=severity,
                        category='File System Write',
                        description=f'File write operation detected: mode={mode}' + (' (report file)' if is_report_file else ''),
                        file_path=file_path,
                        line_number=node.lineno,
                        code_snippet=full_line,
                        recommendation='Αφαίρεσε την εγγραφή αρχείων εκτός αν είναι απολύτως απαραίτητη' if not is_report_file else 'Report file write - αποδεκτό αν είναι για backtest results'
                    ))

        return issues

    def _check_attribute_access(self, node: ast.Attribute, content_lines: List[str], file_path: str) -> List[SecurityIssue]:
        """Check for dangerous attribute access."""
        issues = []
        full_line = content_lines[node.lineno - 1].strip() if node.lineno <= len(content_lines) else ""

        # Check for os.environ access
        if (isinstance(node.value, ast.Name) and node.value.id == 'os' and
            node.attr in ('environ', 'getenv')):
            issues.append(SecurityIssue(
                severity='MEDIUM',
                category='Environment Access',
                description='Access to environment variables detected',
                file_path=file_path,
                line_number=node.lineno,
                code_snippet=full_line,
                recommendation='Αφαίρεσε την πρόσβαση σε environment variables εκτός αν είναι απαραίτητη'
            ))

        return issues

    def _check_obfuscation(self, content: str, file_path: str) -> List[SecurityIssue]:
        """Check for obfuscated or self-modifying code."""
        issues = []
        lines = content.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Check for long base64-like strings
            if re.search(r'["\'][A-Za-z0-9+/]{100,}={0,2}["\']', line):
                # Check if it's used with base64.decode and exec/eval
                surrounding_lines = lines[max(0, line_num-3):min(len(lines), line_num+3)]
                context = '\n'.join(surrounding_lines)

                if ('base64' in context and ('exec' in context or 'eval' in context)):
                    issues.append(SecurityIssue(
                        severity='CRITICAL',
                        category='Code Obfuscation',
                        description='Potential obfuscated code execution detected',
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=line.strip()[:100] + "...",
                        recommendation='Αφαίρεσε τον obfuscated κώδικα - όλος ο κώδικας πρέπει να είναι αναγνώσιμος'
                    ))
                elif len([c for c in line if c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/']) > 200:
                    issues.append(SecurityIssue(
                        severity='HIGH',
                        category='Suspicious Encoding',
                        description='Very long encoded string detected',
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=line.strip()[:100] + "...",
                        recommendation='Εξήγησε την ανάγκη για αυτό το encoded string'
                    ))

        return issues

    def _extract_participant_name(self, submission_path: Path) -> str:
        """Extract participant name from submission path or README."""
        # Try to extract from folder name (format: #ID (Name))
        folder_name = submission_path.name
        match = re.search(r'#\d+\s*\(([^)]+)\)', folder_name)
        if match:
            return match.group(1).strip()

        # Try to read from README or similar files
        for readme_file in ['README.md', 'README.txt', 'readme.md', 'readme.txt']:
            readme_path = submission_path / readme_file
            if readme_path.exists():
                try:
                    content = readme_path.read_text(encoding='utf-8')
                    # Look for author/participant info
                    for line in content.splitlines()[:10]:  # Check first 10 lines
                        if any(keyword in line.lower() for keyword in ['author:', 'participant:', 'by:']):
                            return line.split(':', 1)[1].strip()
                except Exception:
                    pass

        return "Unknown"

    def save_results(self, output_dir: Path, include_issues: bool = True):
        """Save audit results to files."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Summary report
        summary_data = []
        for result in self.results:
            summary_data.append({
                'submission_id': result.submission_id,
                'participant': result.participant,
                'security_score': result.security_score,
                'passed': result.passed,
                'critical_issues': result.critical_issues,
                'high_issues': result.high_issues,
                'medium_issues': result.medium_issues,
                'low_issues': result.low_issues,
                'total_issues': result.total_issues,
                'files_scanned': len(result.files_scanned),
                'scan_timestamp': result.scan_timestamp
            })

        # Save summary JSON
        with open(output_dir / 'security_audit_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)

        # Save detailed issues if requested
        if include_issues:
            detailed_data = []
            for result in self.results:
                result_dict = asdict(result)
                detailed_data.append(result_dict)

            with open(output_dir / 'security_audit_detailed.json', 'w', encoding='utf-8') as f:
                json.dump(detailed_data, f, indent=2, ensure_ascii=False)

        # Generate markdown report
        self._generate_markdown_report(output_dir / 'security_audit_report.md')

        print(f"\n[SAVE] Results saved to {output_dir}")
        print(f"       - security_audit_summary.json")
        if include_issues:
            print(f"       - security_audit_detailed.json")
        print(f"       - security_audit_report.md")

    def _generate_markdown_report(self, output_path: Path):
        """Generate a comprehensive markdown report."""
        passed_count = sum(1 for r in self.results if r.passed)
        total_count = len(self.results)

        report_lines = [
            "# Security Audit Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"**Submissions Analyzed:** {total_count}",
            f"**Security Passed:** {passed_count}/{total_count}",
            "",
            "## Executive Summary",
            "",
        ]

        if passed_count == total_count:
            report_lines.append("✅ **ALL SUBMISSIONS PASSED** security audit.")
        elif passed_count == 0:
            report_lines.append("🚨 **NO SUBMISSIONS PASSED** security audit.")
        else:
            report_lines.append(f"⚠️ **{passed_count} out of {total_count} submissions passed** security audit.")

        report_lines.extend([
            "",
            "## Detailed Results",
            "",
            "| Submission | Participant | Score | Status | Critical | High | Medium | Low | Total |",
            "|------------|-------------|--------|--------|----------|------|---------|-----|-------|"
        ])

        # Sort results by security score (descending)
        sorted_results = sorted(self.results, key=lambda x: x.security_score, reverse=True)

        for result in sorted_results:
            status_emoji = "✅ PASS" if result.passed else "❌ FAIL"
            report_lines.append(
                f"| {result.submission_id} | {result.participant} | "
                f"{result.security_score:.1f}/100 | {status_emoji} | "
                f"{result.critical_issues} | {result.high_issues} | "
                f"{result.medium_issues} | {result.low_issues} | {result.total_issues} |"
            )

        # Add failed submissions details
        failed_results = [r for r in self.results if not r.passed]
        if failed_results:
            report_lines.extend([
                "",
                "## Failed Submissions - Issue Details",
                ""
            ])

            for result in failed_results:
                report_lines.extend([
                    f"### {result.submission_id} ({result.participant})",
                    f"Score: {result.security_score:.1f}/100",
                    ""
                ])

                # Group issues by severity
                critical_issues = [i for i in result.issues if i.severity == 'CRITICAL']
                high_issues = [i for i in result.issues if i.severity == 'HIGH']

                if critical_issues:
                    report_lines.append("**CRITICAL Issues:**")
                    for issue in critical_issues[:5]:  # Show top 5
                        report_lines.append(f"- {issue.category}: {issue.description}")
                    report_lines.append("")

                if high_issues:
                    report_lines.append("**HIGH Issues:**")
                    for issue in high_issues[:5]:  # Show top 5
                        report_lines.append(f"- {issue.category}: {issue.description}")
                    report_lines.append("")

        report_lines.extend([
            "",
            "## Security Criteria",
            "",
            "**Pass Requirements:**",
            "- No CRITICAL severity issues",
            "- Security score ≥ 60/100",
            "",
            "**Scoring:**",
            "- Start at 100 points",
            "- CRITICAL issue: -40 points",
            "- HIGH issue: -15 points",
            "- MEDIUM issue: -5 points",
            "- LOW issue: -1 point",
            "",
            "---",
            "Generated by Security Audit Framework v2.0"
        ])

        output_path.write_text('\n'.join(report_lines), encoding='utf-8')

def main():
    """Main execution function with CLI arguments."""
    parser = argparse.ArgumentParser(description="Security Audit Framework v2.0 for Trading Strategy Contest")
    parser.add_argument(
        '--base-path',
        type=Path,
        default=Path("final_evaluation"),
        help='Base directory containing submissions (default: final_evaluation)'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path("security_audit_results"),
        help='Output directory for results (default: security_audit_results)'
    )
    parser.add_argument(
        '--fail-on-critical',
        action='store_true',
        help='Exit with code 1 if any CRITICAL issues found (useful for CI)'
    )
    parser.add_argument(
        '--no-detailed-json',
        action='store_true',
        help='Skip generating detailed JSON with full issue lists (faster, smaller files)'
    )

    args = parser.parse_args()

    if not args.base_path.exists():
        print(f"Error: Base path {args.base_path} does not exist")
        sys.exit(1)

    auditor = SecurityAuditor()

    # Find all submission directories
    submission_dirs = [d for d in args.base_path.iterdir() if d.is_dir() and d.name.startswith('#')]

    if not submission_dirs:
        print(f"No submission directories found in {args.base_path}")
        sys.exit(1)

    print(f"[START] Security audit of {len(submission_dirs)} submissions")
    print(f"        Base path: {args.base_path}")
    print(f"        Output: {args.output_dir}")
    print("")

    # Scan each submission
    for submission_dir in sorted(submission_dirs, key=lambda x: x.name):
        result = auditor.scan_submission(submission_dir)
        auditor.results.append(result)

    # Save results
    auditor.save_results(args.output_dir, include_issues=not args.no_detailed_json)

    # Summary
    passed_count = sum(1 for r in auditor.results if r.passed)
    total_count = len(auditor.results)
    critical_count = sum(r.critical_issues for r in auditor.results)

    print(f"\n[SUMMARY] Security Audit Complete")
    print(f"          Passed: {passed_count}/{total_count}")
    print(f"          Critical issues found: {critical_count}")

    # Exit with error code if requested and critical issues found
    if args.fail_on_critical and critical_count > 0:
        print(f"\n[EXIT] Exiting with error code due to {critical_count} CRITICAL issues")
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()