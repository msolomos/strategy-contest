#!/usr/bin/env python3
"""
STRICT CONTEST COMPLIANCE CHECKER
Stage 2: Enforce exact contest framework requirements

Based on official contest requirements from:
https://github.com/msolomos/strategy-contest/

STRICT REQUIREMENTS:
1. Exact folder structure: your-strategy-template/ and reports/
2. Exact file names: your_strategy.py, startup.py, etc.
3. BaseStrategy inheritance with correct interface
4. Signal class usage with proper dataclass structure
5. Required abstract method implementation: generate_signal()
6. Strategy registration with register_strategy()
7. Proper constructor signature
"""

import os
import sys
import ast
import json
import re
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from dataclasses import dataclass, asdict

@dataclass
class ComplianceIssue:
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str
    description: str
    file_path: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    recommendation: str = ""

@dataclass
class ComplianceResult:
    submission_id: str
    participant: str
    passed: bool
    compliance_score: float
    issues: List[ComplianceIssue]

    # Detailed compliance checks
    required_structure_compliance: bool
    base_strategy_inheritance: bool
    generate_signal_method: bool
    signal_class_usage: bool
    strategy_registration: bool
    constructor_compliance: bool

    # File structure details
    required_files_found: int
    required_files_total: int
    scan_timestamp: str

class StrictComplianceChecker:
    """Strict compliance checker enforcing exact contest requirements."""

    def __init__(self):
        # EXACT required files as per contest rules
        self.required_files = {
            "your-strategy-template/your_strategy.py": "CRITICAL",
            "your-strategy-template/startup.py": "HIGH",
            "your-strategy-template/Dockerfile": "HIGH",
            "your-strategy-template/requirements.txt": "HIGH",
            "your-strategy-template/README.md": "MEDIUM",
            "reports/backtest_runner.py": "CRITICAL",
            "reports/backtest_report.md": "HIGH",
            "trade_logic_explanation.md": "LOW"  # Optional documentation
        }

        # Required BaseStrategy interface compliance
        self.required_methods = {
            "__init__": "CRITICAL",
            "generate_signal": "CRITICAL"
        }

        # Expected constructor signature patterns
        self.constructor_patterns = [
            r"def __init__\s*\(\s*self\s*,.*config.*:.*Dict.*,.*exchange",
            r"def __init__\s*\(\s*self\s*,.*\*.*,.*config.*:.*Dict.*,.*exchange"
        ]

    def check_submission(self, submission_path: Path) -> ComplianceResult:
        """Perform strict compliance check on submission."""
        print(f"[STRICT CHECK] {submission_path.name}...")

        submission_id = submission_path.name
        participant = self._extract_participant_name(submission_path)
        issues = []

        # 1. STRICT FILE STRUCTURE CHECK
        files_found = 0
        structure_compliance = self._check_exact_file_structure(submission_path, issues)
        files_found = sum(1 for file_path in self.required_files.keys()
                         if (submission_path / file_path).exists())

        # 2. BASESTRATEGY INHERITANCE CHECK
        base_strategy_inheritance = self._check_base_strategy_inheritance(submission_path, issues)

        # 3. GENERATE_SIGNAL METHOD CHECK
        generate_signal_method = self._check_generate_signal_method(submission_path, issues)

        # 4. SIGNAL CLASS USAGE CHECK
        signal_usage = self._check_signal_class_usage(submission_path, issues)

        # 5. STRATEGY REGISTRATION CHECK
        strategy_registration = self._check_strategy_registration(submission_path, issues)

        # 6. CONSTRUCTOR COMPLIANCE CHECK
        constructor_compliance = self._check_constructor_compliance(submission_path, issues)

        # Calculate compliance score
        compliance_score = self._calculate_compliance_score(issues)

        # Pass criteria: All CRITICAL requirements met AND score >= 80
        critical_failed = any(issue.severity == "CRITICAL" for issue in issues)
        passed = not critical_failed and compliance_score >= 80.0

        result = ComplianceResult(
            submission_id=submission_id,
            participant=participant,
            passed=passed,
            compliance_score=compliance_score,
            issues=issues,
            required_structure_compliance=structure_compliance,
            base_strategy_inheritance=base_strategy_inheritance,
            generate_signal_method=generate_signal_method,
            signal_class_usage=signal_usage,
            strategy_registration=strategy_registration,
            constructor_compliance=constructor_compliance,
            required_files_found=files_found,
            required_files_total=len(self.required_files),
            scan_timestamp=datetime.now().isoformat()
        )

        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {submission_id}: {compliance_score:.1f}/100")

        # Detailed compliance breakdown
        print(f"        Structure: {'OK' if structure_compliance else 'FAIL'}")
        print(f"        BaseStrategy: {'OK' if base_strategy_inheritance else 'FAIL'}")
        print(f"        generate_signal: {'OK' if generate_signal_method else 'FAIL'}")
        print(f"        Signal usage: {'OK' if signal_usage else 'FAIL'}")
        print(f"        Registration: {'OK' if strategy_registration else 'FAIL'}")
        print(f"        Constructor: {'OK' if constructor_compliance else 'FAIL'}")

        if not passed:
            critical_count = sum(1 for issue in issues if issue.severity == "CRITICAL")
            if critical_count > 0:
                print(f"        CRITICAL FAILURES: {critical_count}")

        return result

    def _check_exact_file_structure(self, submission_path: Path, issues: List[ComplianceIssue]) -> bool:
        """Check exact file structure compliance."""
        all_files_present = True

        for required_file, severity in self.required_files.items():
            file_path = submission_path / required_file

            if not file_path.exists():
                all_files_present = False
                issues.append(ComplianceIssue(
                    severity=severity,
                    category="Missing Required File",
                    description=f"Required file missing: {required_file}",
                    file_path=required_file,
                    recommendation=f"Create {required_file} exactly as specified in contest requirements"
                ))

        return all_files_present

    def _check_base_strategy_inheritance(self, submission_path: Path, issues: List[ComplianceIssue]) -> bool:
        """Check BaseStrategy inheritance compliance."""
        strategy_file = submission_path / "your-strategy-template" / "your_strategy.py"

        if not strategy_file.exists():
            issues.append(ComplianceIssue(
                severity="CRITICAL",
                category="Missing Strategy File",
                description="Main strategy file your_strategy.py not found",
                file_path="your-strategy-template/your_strategy.py",
                recommendation="Create your_strategy.py in your-strategy-template/ folder"
            ))
            return False

        try:
            content = strategy_file.read_text(encoding='utf-8')

            # Parse AST to check class inheritance
            tree = ast.parse(content)

            strategy_classes = []
            base_strategy_inherited = False

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    strategy_classes.append(node.name)

                    # Check if class inherits from BaseStrategy
                    for base in node.bases:
                        if isinstance(base, ast.Name) and base.id == "BaseStrategy":
                            base_strategy_inherited = True
                            break

            if not base_strategy_inherited:
                issues.append(ComplianceIssue(
                    severity="CRITICAL",
                    category="BaseStrategy Inheritance",
                    description="Strategy class does not inherit from BaseStrategy",
                    file_path="your-strategy-template/your_strategy.py",
                    recommendation="Ensure your strategy class inherits from BaseStrategy: class MyStrategy(BaseStrategy):"
                ))
                return False

            # Check BaseStrategy import
            if "from strategy_interface import" not in content or "BaseStrategy" not in content:
                issues.append(ComplianceIssue(
                    severity="CRITICAL",
                    category="BaseStrategy Import",
                    description="BaseStrategy not properly imported from strategy_interface",
                    file_path="your-strategy-template/your_strategy.py",
                    recommendation="Add: from strategy_interface import BaseStrategy, Signal, Portfolio"
                ))
                return False

            return True

        except Exception as e:
            issues.append(ComplianceIssue(
                severity="CRITICAL",
                category="Strategy File Error",
                description=f"Error parsing strategy file: {str(e)}",
                file_path="your-strategy-template/your_strategy.py",
                recommendation="Fix syntax errors in your_strategy.py"
            ))
            return False

    def _check_generate_signal_method(self, submission_path: Path, issues: List[ComplianceIssue]) -> bool:
        """Check generate_signal method implementation."""
        strategy_file = submission_path / "your-strategy-template" / "your_strategy.py"

        if not strategy_file.exists():
            return False

        try:
            content = strategy_file.read_text(encoding='utf-8')
            tree = ast.parse(content)

            generate_signal_found = False
            correct_signature = False
            returns_signal = False

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == "generate_signal":
                    generate_signal_found = True

                    # Check method signature
                    arg_names = [arg.arg for arg in node.args.args]
                    if len(arg_names) >= 3 and "self" in arg_names and "market" in arg_names and "portfolio" in arg_names:
                        correct_signature = True

                    # Check return annotation
                    if node.returns and isinstance(node.returns, ast.Name) and node.returns.id == "Signal":
                        returns_signal = True

            if not generate_signal_found:
                issues.append(ComplianceIssue(
                    severity="CRITICAL",
                    category="Missing Method",
                    description="generate_signal method not implemented",
                    file_path="your-strategy-template/your_strategy.py",
                    recommendation="Implement: def generate_signal(self, market: MarketSnapshot, portfolio: Portfolio) -> Signal:"
                ))
                return False

            if not correct_signature:
                issues.append(ComplianceIssue(
                    severity="HIGH",
                    category="Method Signature",
                    description="generate_signal method has incorrect signature",
                    file_path="your-strategy-template/your_strategy.py",
                    recommendation="Use correct signature: def generate_signal(self, market: MarketSnapshot, portfolio: Portfolio) -> Signal:"
                ))

            if not returns_signal:
                issues.append(ComplianceIssue(
                    severity="HIGH",
                    category="Return Type",
                    description="generate_signal method should return Signal type",
                    file_path="your-strategy-template/your_strategy.py",
                    recommendation="Add return type annotation: -> Signal"
                ))

            return generate_signal_found

        except Exception as e:
            issues.append(ComplianceIssue(
                severity="HIGH",
                category="Method Check Error",
                description=f"Error checking generate_signal method: {str(e)}",
                file_path="your-strategy-template/your_strategy.py",
                recommendation="Fix syntax errors in generate_signal method"
            ))
            return False

    def _check_signal_class_usage(self, submission_path: Path, issues: List[ComplianceIssue]) -> bool:
        """Check proper Signal class usage."""
        strategy_file = submission_path / "your-strategy-template" / "your_strategy.py"

        if not strategy_file.exists():
            return False

        try:
            content = strategy_file.read_text(encoding='utf-8')

            # Check Signal import
            if "Signal" not in content:
                issues.append(ComplianceIssue(
                    severity="CRITICAL",
                    category="Signal Import",
                    description="Signal class not imported",
                    file_path="your-strategy-template/your_strategy.py",
                    recommendation="Import Signal: from strategy_interface import BaseStrategy, Signal"
                ))
                return False

            # Check Signal instantiation
            if "Signal(" not in content and "return Signal" not in content:
                issues.append(ComplianceIssue(
                    severity="HIGH",
                    category="Signal Usage",
                    description="Signal class not used in strategy",
                    file_path="your-strategy-template/your_strategy.py",
                    recommendation="Return Signal objects from generate_signal method: return Signal('buy', size=100, reason='Entry signal')"
                ))
                return False

            return True

        except Exception:
            return False

    def _check_strategy_registration(self, submission_path: Path, issues: List[ComplianceIssue]) -> bool:
        """Check strategy registration compliance."""
        strategy_file = submission_path / "your-strategy-template" / "your_strategy.py"

        if not strategy_file.exists():
            return False

        try:
            content = strategy_file.read_text(encoding='utf-8')

            # Check register_strategy import and usage
            if "register_strategy" not in content:
                issues.append(ComplianceIssue(
                    severity="HIGH",
                    category="Strategy Registration",
                    description="Strategy not registered using register_strategy()",
                    file_path="your-strategy-template/your_strategy.py",
                    recommendation="Add strategy registration: register_strategy('your_strategy_name', lambda config, exchange: YourStrategy(config, exchange))"
                ))
                return False

            return True

        except Exception:
            return False

    def _check_constructor_compliance(self, submission_path: Path, issues: List[ComplianceIssue]) -> bool:
        """Check constructor signature compliance."""
        strategy_file = submission_path / "your-strategy-template" / "your_strategy.py"

        if not strategy_file.exists():
            return False

        try:
            content = strategy_file.read_text(encoding='utf-8')

            # Check for proper constructor signature
            constructor_compliant = False
            for pattern in self.constructor_patterns:
                if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                    constructor_compliant = True
                    break

            if not constructor_compliant:
                issues.append(ComplianceIssue(
                    severity="HIGH",
                    category="Constructor Signature",
                    description="Constructor does not match required signature",
                    file_path="your-strategy-template/your_strategy.py",
                    recommendation="Use correct constructor: def __init__(self, *, config: Dict[str, Any], exchange: Exchange):"
                ))
                return False

            return True

        except Exception:
            return False

    def _calculate_compliance_score(self, issues: List[ComplianceIssue]) -> float:
        """Calculate compliance score based on issues."""
        score = 100.0

        for issue in issues:
            if issue.severity == "CRITICAL":
                score -= 25  # Heavy penalty for critical issues
            elif issue.severity == "HIGH":
                score -= 10
            elif issue.severity == "MEDIUM":
                score -= 5
            elif issue.severity == "LOW":
                score -= 2

        return max(0.0, score)

    def _extract_participant_name(self, submission_path: Path) -> str:
        """Extract participant name from submission path."""
        folder_name = submission_path.name
        match = re.search(r'#\d+\s*\(([^)]+)\)', folder_name)
        if match:
            return match.group(1).strip()
        return "Unknown"

def main():
    parser = argparse.ArgumentParser(description="Strict Contest Compliance Checker")
    parser.add_argument("--base-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--submissions", type=str, required=True, help="Comma-separated submission IDs")

    args = parser.parse_args()

    # re is already imported at module level

    checker = StrictComplianceChecker()
    results = []

    submission_ids = [s.strip() for s in args.submissions.split(',')]

    print(f"STRICT COMPLIANCE CHECK: {len(submission_ids)} submissions")
    print("=" * 60)

    for submission_id in submission_ids:
        submission_path = args.base_path / submission_id
        if submission_path.exists():
            result = checker.check_submission(submission_path)
            results.append(asdict(result))
        else:
            print(f"[ERROR] Submission not found: {submission_id}")

    # Save results
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with open(args.output_dir / "strict_compliance_results.json", 'w') as f:
        json.dump(results, f, indent=2)

    # Summary
    passed_count = sum(1 for r in results if r['passed'])
    print()
    print("=" * 60)
    print(f"STRICT COMPLIANCE SUMMARY: {passed_count}/{len(results)} PASSED")
    print("=" * 60)

    if passed_count < len(results):
        print("\nFAILED SUBMISSIONS:")
        for r in results:
            if not r['passed']:
                critical_issues = sum(1 for issue in r['issues'] if issue['severity'] == 'CRITICAL')
                print(f"  - {r['submission_id']}: {critical_issues} CRITICAL issues")

if __name__ == "__main__":
    main()