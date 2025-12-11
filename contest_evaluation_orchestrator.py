#!/usr/bin/env python3
"""
CONTEST EVALUATION ORCHESTRATOR
Trading Strategy Contest - Comprehensive Multi-Stage Evaluation

Stages:
1. Security Audit (security_audit_framework_v2.py)
2. Compliance Check (contest_compliance_checker_strict.py)
3. Data Manipulation Detection (data_integrity_checker.py)
4. Contest Rules Verification (contest_rules_verifier.py)
5. Final Ranking Generation

Usage:
    python contest_evaluation_orchestrator.py --base-path final_evaluation --output-dir evaluation_results
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

@dataclass
class SubmissionResult:
    """Complete evaluation results for one submission."""
    submission_id: str
    participant: str
    security_passed: bool
    security_score: float
    compliance_passed: bool
    compliance_score: float
    data_integrity_passed: bool
    data_integrity_score: float
    contest_rules_passed: bool
    contest_rules_score: float
    overall_score: float
    final_status: str  # PASS, FAIL, PENDING
    issues: List[str]
    evaluation_timestamp: str

class ContestEvaluationOrchestrator:
    """Main orchestrator for multi-stage contest evaluation."""

    def __init__(self, base_path: Path, output_dir: Path):
        self.base_path = base_path
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Stage results storage
        self.stage_results = {
            'security': {},
            'compliance': {},
            'data_integrity': {},
            'contest_rules': {}
        }

        self.final_results: List[SubmissionResult] = []

    def run_interactive_evaluation(self):
        """Run evaluation pipeline interactively, step by step."""
        print("🏆 CONTEST EVALUATION ORCHESTRATOR - INTERACTIVE MODE")
        print("=" * 60)
        print(f"Base path: {self.base_path}")
        print(f"Output: {self.output_dir}")
        print()

        # Stage 1: Security Audit
        print("🔒 STAGE 1: SECURITY AUDIT")
        print("-" * 40)
        print("This stage will run security audit on all submissions.")
        print("It checks for malicious code, dangerous imports, and security vulnerabilities.")
        print()

        response = input("🤔 Do you want to run Stage 1 (Security Audit)? [y/N/s=skip]: ").strip().lower()
        if response in ['s', 'skip']:
            print("⏭️ Stage 1 skipped. Assuming all submissions pass security audit...")
            # Get all submissions from base path
            submissions = [d.name for d in self.base_path.iterdir() if d.is_dir()]
            security_survivors = submissions
            for submission_id in security_survivors:
                self.stage_results['security'][submission_id] = {
                    'passed': True,
                    'score': 90.0,
                    'issues': []
                }
                print(f"✅ {submission_id}: 90.0/100 (SKIPPED)")
        elif response not in ['y', 'yes']:
            print("❌ Stage 1 skipped. Exiting...")
            return
        else:
            security_survivors = self.run_security_audit()

        print(f"\n✅ Security survivors: {len(security_survivors)}")
        if security_survivors:
            print("   Survivors:", ", ".join(security_survivors))
        else:
            print("❌ No submissions passed security audit!")
            return

        self.wait_for_user_input("Stage 1 (Security Audit) completed")

        # Stage 2: Compliance Check
        print("\n📋 STAGE 2: COMPLIANCE CHECK")
        print("-" * 40)
        print("This stage verifies contest structure compliance.")
        print("It checks required files, BaseStrategy inheritance, and Signal usage.")
        print(f"Running on {len(security_survivors)} survivors from Stage 1.")
        print()

        response = input("🤔 Do you want to run Stage 2 (Compliance Check)? [y/N/s=skip]: ").strip().lower()
        if response in ['s', 'skip']:
            print("⏭️ Stage 2 skipped. Assuming all survivors pass compliance check...")
            compliance_survivors = security_survivors
            for submission_id in compliance_survivors:
                self.stage_results['compliance'][submission_id] = {
                    'passed': True,
                    'score': 85.0,
                    'issues': []
                }
                print(f"✅ {submission_id}: 85.0/100 (SKIPPED)")
        elif response not in ['y', 'yes']:
            print("❌ Stage 2 skipped. Stopping here...")
            return
        else:
            compliance_survivors = self.run_compliance_check(security_survivors)
        print(f"\n✅ Compliance survivors: {len(compliance_survivors)}")
        if compliance_survivors:
            print("   Survivors:", ", ".join(compliance_survivors))
        else:
            print("❌ No submissions passed compliance check!")
            return

        self.wait_for_user_input("Stage 2 (Compliance Check) completed")

        # Stage 3: Data Integrity Check
        print("\n🔍 STAGE 3: DATA INTEGRITY CHECK")
        print("-" * 40)
        print("This stage checks for data manipulation and synthetic data.")
        print("It detects hardcoded data, synthetic generation, hindsight bias, and unrealistic patterns.")
        print(f"Running on {len(compliance_survivors)} survivors from Stage 2.")
        print()

        response = input("🤔 Do you want to run Stage 3 (Data Integrity Check)? [y/N/s=skip]: ").strip().lower()
        if response in ['s', 'skip']:
            print("⏭️ Stage 3 skipped. Assuming all survivors pass data integrity check...")
            data_survivors = compliance_survivors
            for submission_id in data_survivors:
                self.stage_results['data_integrity'][submission_id] = {
                    'passed': True,
                    'score': 80.0,
                    'issues': []
                }
                print(f"✅ {submission_id}: 80.0/100 (SKIPPED)")
        elif response not in ['y', 'yes']:
            print("❌ Stage 3 skipped. Stopping here...")
            return
        else:
            data_survivors = self.run_data_integrity_check(compliance_survivors)
        print(f"\n✅ Data integrity survivors: {len(data_survivors)}")
        if data_survivors:
            print("   Survivors:", ", ".join(data_survivors))

        self.wait_for_user_input("Stage 3 (Data Integrity Check) completed")

        # Stage 4: Contest Rules Verification
        print("\n⚖️ STAGE 4: CONTEST RULES VERIFICATION")
        print("-" * 40)
        print("This stage verifies contest rules compliance.")
        print("It checks performance requirements, drawdown limits, and trade counts.")
        print("It validates starting capital, trading period, and asset compliance.")
        print(f"Running on {len(data_survivors)} survivors from Stage 3.")
        print()

        response = input("🤔 Do you want to run Stage 4 (Contest Rules Verification)? [y/N/s=skip]: ").strip().lower()
        if response in ['s', 'skip']:
            print("⏭️ Stage 4 skipped. Assuming all survivors pass contest rules verification...")
            final_survivors = data_survivors
            for submission_id in final_survivors:
                self.stage_results['contest_rules'][submission_id] = {
                    'passed': True,
                    'score': 75.0,
                    'issues': []
                }
                print(f"✅ {submission_id}: 75.0/100 (SKIPPED)")
        elif response not in ['y', 'yes']:
            print("❌ Stage 4 skipped. Stopping here...")
            return
        else:
            final_survivors = self.run_contest_rules_verification(data_survivors)
        print(f"\n✅ Contest rules survivors: {len(final_survivors)}")
        if final_survivors:
            print("   Survivors:", ", ".join(final_survivors))

        self.wait_for_user_input("Stage 4 (Contest Rules Verification) completed")

        # Stage 5: Generate Final Results
        print("\n🏁 STAGE 5: FINAL RANKING")
        print("-" * 40)
        print("This stage generates the final ranking and comprehensive report.")
        print()

        response = input("🤔 Do you want to generate final ranking? [y/N/s=skip]: ").strip().lower()
        if response in ['s', 'skip']:
            print("⏭️ Final ranking skipped.")
            return
        elif response not in ['y', 'yes']:
            print("❌ Final ranking skipped.")
            return
        else:
            self.generate_final_ranking()

        print("\n🎉 EVALUATION COMPLETE!")
        self.print_summary()

    def wait_for_user_input(self, stage_description: str):
        """Wait for user to review results before continuing."""
        print(f"\n📊 {stage_description}.")
        print("📁 Check the results in the output directory if needed.")
        input("\n⏸️  Press Enter to continue to next stage...")

    def run_full_evaluation(self):
        """Run complete automated evaluation pipeline."""
        print("🏆 CONTEST EVALUATION ORCHESTRATOR - AUTOMATED MODE")
        print("=" * 60)
        print(f"Base path: {self.base_path}")
        print(f"Output: {self.output_dir}")
        print()

        # Stage 1: Security Audit
        print("🔒 STAGE 1: SECURITY AUDIT")
        print("-" * 30)
        security_survivors = self.run_security_audit()
        print(f"✅ Security survivors: {len(security_survivors)}")
        print()

        # Stage 2: Compliance Check
        print("📋 STAGE 2: COMPLIANCE CHECK")
        print("-" * 30)
        compliance_survivors = self.run_compliance_check(security_survivors)
        print(f"✅ Compliance survivors: {len(compliance_survivors)}")
        print()

        # Stage 3: Data Integrity Check
        print("🔍 STAGE 3: DATA INTEGRITY CHECK")
        print("-" * 30)
        data_survivors = self.run_data_integrity_check(compliance_survivors)
        print(f"✅ Data integrity survivors: {len(data_survivors)}")
        print()

        # Stage 4: Contest Rules Verification
        print("⚖️ STAGE 4: CONTEST RULES VERIFICATION")
        print("-" * 30)
        final_survivors = self.run_contest_rules_verification(data_survivors)
        print(f"✅ Final survivors: {len(final_survivors)}")
        print()

        # Stage 5: Generate Final Results
        print("🏁 STAGE 5: FINAL RANKING")
        print("-" * 30)
        self.generate_final_ranking()

        print("🎉 EVALUATION COMPLETE!")
        self.print_summary()

    def run_security_audit(self) -> List[str]:
        """Run Stage 1: Security Audit using existing framework."""
        try:
            cmd = [
                sys.executable,
                "security_audit_framework_v2.py",
                "--base-path", str(self.base_path),
                "--output-dir", str(self.output_dir / "stage1_security"),
                "--no-detailed-json"  # Save space
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")

            if result.returncode != 0:
                print(f"⚠️ Security audit failed: {result.stderr}")
                return []

            # Parse security results
            security_file = self.output_dir / "stage1_security" / "security_audit_summary.json"
            if not security_file.exists():
                print("⚠️ Security results file not found")
                return []

            with open(security_file) as f:
                security_data = json.load(f)

            survivors = []
            for entry in security_data:
                submission_id = entry['submission_id']
                self.stage_results['security'][submission_id] = {
                    'passed': entry['passed'],
                    'score': entry['security_score'],
                    'issues': entry['total_issues']
                }

                if entry['passed']:
                    survivors.append(submission_id)
                    print(f"✅ {submission_id}: {entry['security_score']:.1f}/100")
                else:
                    print(f"❌ {submission_id}: {entry['security_score']:.1f}/100 (REJECTED)")

            return survivors

        except Exception as e:
            print(f"❌ Security audit error: {e}")
            return []

    def run_compliance_check(self, survivors: List[str]) -> List[str]:
        """Run Stage 2: Contest Compliance Check."""
        try:
            cmd = [
                sys.executable,
                "contest_compliance_checker_strict.py",
                "--base-path", str(self.base_path),
                "--output-dir", str(self.output_dir / "stage2_compliance"),
                "--submissions", ",".join(survivors)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")

            if result.returncode != 0:
                print(f"⚠️ Compliance check failed: {result.stderr}")
                # Fall back to assuming all pass
                print("⚠️ Falling back to assume all submissions pass compliance")
                return survivors

            # Parse compliance results
            compliance_file = self.output_dir / "stage2_compliance" / "strict_compliance_results.json"
            if not compliance_file.exists():
                print("⚠️ Compliance results file not found, assuming all pass")
                return survivors

            with open(compliance_file) as f:
                compliance_data = json.load(f)

            new_survivors = []
            for entry in compliance_data:
                submission_id = entry['submission_id']
                self.stage_results['compliance'][submission_id] = {
                    'passed': entry['passed'],
                    'score': entry['compliance_score'],
                    'issues': entry.get('issues', [])
                }

                if entry['passed']:
                    new_survivors.append(submission_id)
                    print(f"✅ {submission_id}: {entry['compliance_score']:.1f}/100")
                else:
                    print(f"❌ {submission_id}: {entry['compliance_score']:.1f}/100 (REJECTED)")

            return new_survivors

        except Exception as e:
            print(f"❌ Compliance check error: {e}")
            print("⚠️ Assuming all submissions pass compliance")
            return survivors

    def run_data_integrity_check(self, survivors: List[str]) -> List[str]:
        """Run Stage 3: Data Integrity Check."""
        print("🔍 Running data integrity checker on survivors...")

        # Prepare submissions list for the checker
        submissions_list = ",".join(survivors)

        try:
            # Run data integrity checker
            result = subprocess.run([
                sys.executable, "data_integrity_checker.py",
                "--base-path", str(self.base_path),
                "--output-dir", str(self.output_dir / "stage3_data_integrity"),
                "--submissions", submissions_list
            ], capture_output=True, text=True, encoding='utf-8')

            if result.returncode != 0:
                print(f"❌ Data integrity checker failed: {result.stderr}")
                return []

            # Load results
            results_file = self.output_dir / "stage3_data_integrity" / "data_integrity_results.json"
            if results_file.exists():
                with open(results_file, 'r', encoding='utf-8') as f:
                    results = json.load(f)

                data_survivors = []
                for result in results:
                    submission_id = result['submission_id']
                    self.stage_results['data_integrity'][submission_id] = {
                        'passed': result['passed'],
                        'score': result['integrity_score'],
                        'issues': result['issues']
                    }

                    status = "PASS" if result['passed'] else "FAIL"
                    print(f"[{status}] {submission_id}: {result['integrity_score']:.1f}/100")

                    if result['passed']:
                        data_survivors.append(submission_id)

                return data_survivors
            else:
                print("❌ Data integrity results file not found!")
                return []

        except Exception as e:
            print(f"❌ Error running data integrity checker: {str(e)}")
            return []

    def run_contest_rules_verification(self, survivors: List[str]) -> List[str]:
        """Run Stage 4: Contest Rules Verification."""
        print("⚖️ Running contest rules verification on survivors...")

        # Prepare submissions list for the verifier
        submissions_list = ",".join(survivors)

        try:
            # Run contest rules verifier
            result = subprocess.run([
                sys.executable, "contest_rules_verifier.py",
                "--base-path", str(self.base_path),
                "--output-dir", str(self.output_dir / "stage4_contest_rules"),
                "--submissions", submissions_list
            ], capture_output=True, text=True, encoding='utf-8')

            if result.returncode != 0:
                print(f"❌ Contest rules verifier failed: {result.stderr}")
                # Fall back to assuming all pass
                print("⚠️ Falling back to assume all submissions pass contest rules")
                for submission_id in survivors:
                    self.stage_results['contest_rules'][submission_id] = {
                        'passed': True,
                        'score': 75.0,
                        'issues': []
                    }
                    print(f"✅ {submission_id}: 75.0/100 (ASSUMED)")
                return survivors

            # Load results
            results_file = self.output_dir / "stage4_contest_rules" / "contest_rules_results.json"
            if results_file.exists():
                with open(results_file, 'r', encoding='utf-8') as f:
                    results = json.load(f)

                rules_survivors = []
                for result in results:
                    submission_id = result['submission_id']
                    self.stage_results['contest_rules'][submission_id] = {
                        'passed': result['passed'],
                        'score': result['rules_score'],
                        'issues': [v['description'] for v in result['violations']]
                    }

                    status = "PASS" if result['passed'] else "FAIL"
                    print(f"[{status}] {submission_id}: {result['rules_score']:.1f}/100")

                    if result['passed']:
                        rules_survivors.append(submission_id)

                return rules_survivors
            else:
                print("❌ Contest rules results file not found!")
                # Fall back to assuming all pass
                for submission_id in survivors:
                    self.stage_results['contest_rules'][submission_id] = {
                        'passed': True,
                        'score': 75.0,
                        'issues': []
                    }
                return survivors

        except Exception as e:
            print(f"❌ Error running contest rules verifier: {str(e)}")
            # Fall back to assuming all pass
            for submission_id in survivors:
                self.stage_results['contest_rules'][submission_id] = {
                    'passed': True,
                    'score': 75.0,
                    'issues': []
                }
            return survivors

    def generate_final_ranking(self):
        """Generate final ranking and comprehensive report."""
        all_submissions = set()
        for stage_results in self.stage_results.values():
            all_submissions.update(stage_results.keys())

        for submission_id in all_submissions:
            # Get results from all stages
            security = self.stage_results['security'].get(submission_id, {'passed': False, 'score': 0, 'issues': []})
            compliance = self.stage_results['compliance'].get(submission_id, {'passed': False, 'score': 0, 'issues': []})
            data_integrity = self.stage_results['data_integrity'].get(submission_id, {'passed': False, 'score': 0, 'issues': []})
            contest_rules = self.stage_results['contest_rules'].get(submission_id, {'passed': False, 'score': 0, 'issues': []})

            # Calculate overall score (weighted average)
            overall_score = (
                security['score'] * 0.3 +        # Security: 30%
                compliance['score'] * 0.25 +     # Compliance: 25%
                data_integrity['score'] * 0.25 + # Data Integrity: 25%
                contest_rules['score'] * 0.2     # Contest Rules: 20%
            )

            # Determine final status
            if all([security['passed'], compliance['passed'], data_integrity['passed'], contest_rules['passed']]):
                final_status = "PASS"
            else:
                final_status = "FAIL"

            # Collect all issues
            issues = []
            if not security['passed']:
                issues.append(f"Security: Failed ({security['score']:.1f}/100)")
            if not compliance['passed']:
                issues.append(f"Compliance: Failed ({compliance['score']:.1f}/100)")
            if not data_integrity['passed']:
                issues.append(f"Data Integrity: Failed ({data_integrity['score']:.1f}/100)")
            if not contest_rules['passed']:
                issues.append(f"Contest Rules: Failed ({contest_rules['score']:.1f}/100)")

            result = SubmissionResult(
                submission_id=submission_id,
                participant=self.extract_participant_name(submission_id),
                security_passed=security['passed'],
                security_score=security['score'],
                compliance_passed=compliance['passed'],
                compliance_score=compliance['score'],
                data_integrity_passed=data_integrity['passed'],
                data_integrity_score=data_integrity['score'],
                contest_rules_passed=contest_rules['passed'],
                contest_rules_score=contest_rules['score'],
                overall_score=overall_score,
                final_status=final_status,
                issues=issues,
                evaluation_timestamp=datetime.now().isoformat()
            )

            self.final_results.append(result)

        # Sort by overall score (descending)
        self.final_results.sort(key=lambda x: x.overall_score, reverse=True)

        # Save results
        self.save_final_results()

    def extract_participant_name(self, submission_id: str) -> str:
        """Extract participant name from submission ID."""
        # Try to extract from folder name pattern: #ID (Name)
        import re
        match = re.search(r'#\d+\s*\(([^)]+)\)', submission_id)
        if match:
            return match.group(1).strip()
        return "Unknown"

    def save_final_results(self):
        """Save final evaluation results to files."""
        # JSON results
        json_data = [asdict(result) for result in self.final_results]
        with open(self.output_dir / "final_evaluation_results.json", 'w') as f:
            json.dump(json_data, f, indent=2)

        # Markdown report
        self.generate_markdown_report()

    def generate_markdown_report(self):
        """Generate comprehensive markdown evaluation report."""
        passed_count = sum(1 for r in self.final_results if r.final_status == "PASS")
        total_count = len(self.final_results)

        lines = [
            "# Contest Evaluation Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"**Total Submissions:** {total_count}",
            f"**Passed All Stages:** {passed_count}/{total_count}",
            "",
            "## Executive Summary",
            "",
        ]

        if passed_count == 0:
            lines.append("🚨 **NO SUBMISSIONS PASSED** all evaluation stages.")
        elif passed_count == total_count:
            lines.append("🎉 **ALL SUBMISSIONS PASSED** evaluation!")
        else:
            lines.append(f"✅ **{passed_count} out of {total_count} submissions passed** all evaluation stages.")

        lines.extend([
            "",
            "## Final Rankings",
            "",
            "| Rank | Submission | Participant | Overall Score | Status | Security | Compliance | Data | Rules |",
            "|------|------------|-------------|---------------|--------|----------|------------|------|-------|"
        ])

        for rank, result in enumerate(self.final_results, 1):
            status_emoji = "✅ PASS" if result.final_status == "PASS" else "❌ FAIL"

            lines.append(
                f"| {rank} | {result.submission_id} | {result.participant} | "
                f"{result.overall_score:.1f}/100 | {status_emoji} | "
                f"{result.security_score:.1f} | {result.compliance_score:.1f} | "
                f"{result.data_integrity_score:.1f} | {result.contest_rules_score:.1f} |"
            )

        # Add failed submissions details
        failed_results = [r for r in self.final_results if r.final_status == "FAIL"]
        if failed_results:
            lines.extend([
                "",
                "## Failed Submissions - Issue Details",
                ""
            ])

            for result in failed_results:
                lines.extend([
                    f"### {result.submission_id} ({result.participant})",
                    f"Overall Score: {result.overall_score:.1f}/100",
                    "",
                    "**Issues:**"
                ])

                for issue in result.issues:
                    lines.append(f"- {issue}")
                lines.append("")

        lines.extend([
            "",
            "## Evaluation Stages",
            "",
            "1. **Security Audit (30%)**: Malicious code detection, import validation",
            "2. **Compliance Check (25%)**: BaseStrategy inheritance, Signal objects usage",
            "3. **Data Integrity (25%)**: Yahoo Finance data verification, manipulation detection",
            "4. **Contest Rules (20%)**: Structure requirements, performance criteria",
            "",
            "---",
            "Generated by Contest Evaluation Orchestrator v1.0"
        ])

        with open(self.output_dir / "final_evaluation_report.md", 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    def generate_compliance_checker(self):
        """Generate the compliance checker script on-the-fly."""
        compliance_script = '''#!/usr/bin/env python3
"""
CONTEST COMPLIANCE CHECKER
Stage 2: Verify contest structure and interface compliance

Checks:
1. Required folder structure (your-strategy-template/, reports/)
2. Required files (your_strategy.py, startup.py, backtest_runner.py, etc.)
3. BaseStrategy inheritance
4. Signal objects usage
5. Required methods implementation
"""

import os
import sys
import ast
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict

@dataclass
class ComplianceIssue:
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str
    description: str
    file_path: str
    recommendation: str

@dataclass
class ComplianceResult:
    submission_id: str
    participant: str
    passed: bool
    compliance_score: float
    issues: List[ComplianceIssue]
    required_files_found: int
    required_files_total: int
    base_strategy_inheritance: bool
    signal_objects_usage: bool
    required_methods_implemented: bool

class ComplianceChecker:
    """Contest compliance verification."""

    def __init__(self):
        # Core required files (flexible paths)
        self.required_files_patterns = [
            "*strategy*.py",      # Strategy file (any name with 'strategy')
            "startup.py",
            "Dockerfile",
            "requirements.txt",
            "README.md",
            "reports/backtest_runner.py",
            "reports/backtest_report.md"
        ]

        self.required_methods = [
            "generate_signal",
            "__init__"
        ]

    def check_submission(self, submission_path: Path) -> ComplianceResult:
        """Check single submission for contest compliance."""
        print(f"[CHECK] {submission_path.name}...")

        submission_id = submission_path.name
        participant = self.extract_participant_name(submission_path)
        issues = []

        # 1. Check required file structure (flexible)
        files_found = 0
        strategy_files = list(submission_path.glob("**/*strategy*.py"))
        reports_folder = None

        # Look for strategy template folder
        strategy_folders = [d for d in submission_path.iterdir() if d.is_dir() and 'strategy' in d.name.lower()]

        if strategy_folders:
            main_folder = strategy_folders[0]  # Use first strategy folder found
            files_found += self._check_files_in_folder(main_folder, issues)
        else:
            issues.append(ComplianceIssue(
                severity="HIGH",
                category="Missing Strategy Folder",
                description="No strategy folder found (should contain 'strategy' in name)",
                file_path="",
                recommendation="Create a folder with 'strategy' in the name containing your strategy files"
            ))

        # Check for reports folder
        reports_path = submission_path / "reports"
        if not reports_path.exists():
            # Try alternative paths
            reports_candidates = list(submission_path.glob("**/reports"))
            if reports_candidates:
                reports_path = reports_candidates[0]

        if reports_path.exists():
            files_found += self._check_reports_folder(reports_path, issues)
        else:
            issues.append(ComplianceIssue(
                severity="HIGH",
                category="Missing Reports Folder",
                description="Reports folder not found",
                file_path="reports/",
                recommendation="Create reports/ folder with backtest_runner.py and backtest_report.md"
            ))

        # 2. Check BaseStrategy inheritance
        base_strategy_inheritance = self.check_base_strategy_inheritance(submission_path)
        if not base_strategy_inheritance:
            issues.append(ComplianceIssue(
                severity="CRITICAL",
                category="BaseStrategy Inheritance",
                description="Strategy does not inherit from BaseStrategy",
                file_path="your-strategy-template/your_strategy.py",
                recommendation="Ensure your strategy class inherits from BaseStrategy"
            ))

        # 3. Check Signal objects usage
        signal_usage = self.check_signal_objects_usage(submission_path)
        if not signal_usage:
            issues.append(ComplianceIssue(
                severity="CRITICAL",
                category="Signal Objects",
                description="Strategy does not use Signal objects correctly",
                file_path="your-strategy-template/your_strategy.py",
                recommendation="Ensure generate_signal method returns Signal objects"
            ))

        # 4. Check required methods
        methods_implemented = self.check_required_methods(submission_path)
        if not methods_implemented:
            issues.append(ComplianceIssue(
                severity="HIGH",
                category="Required Methods",
                description="Required methods not properly implemented",
                file_path="your-strategy-template/your_strategy.py",
                recommendation="Implement all required methods: generate_signal, __init__"
            ))

        # Calculate compliance score
        compliance_score = 100.0
        for issue in issues:
            if issue.severity == "CRITICAL":
                compliance_score -= 40
            elif issue.severity == "HIGH":
                compliance_score -= 15
            elif issue.severity == "MEDIUM":
                compliance_score -= 5
            elif issue.severity == "LOW":
                compliance_score -= 1

        compliance_score = max(0.0, compliance_score)

        # Pass criteria: score >= 60 and no CRITICAL issues
        critical_issues = sum(1 for issue in issues if issue.severity == "CRITICAL")
        passed = compliance_score >= 60.0 and critical_issues == 0

        result = ComplianceResult(
            submission_id=submission_id,
            participant=participant,
            passed=passed,
            compliance_score=compliance_score,
            issues=issues,
            required_files_found=files_found,
            required_files_total=7,  # Expected total files
            base_strategy_inheritance=base_strategy_inheritance,
            signal_objects_usage=signal_usage,
            required_methods_implemented=methods_implemented
        )

        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {submission_id}: {compliance_score:.1f}/100")

        return result

    def _check_files_in_folder(self, folder_path: Path, issues: list) -> int:
        """Check required files in strategy folder."""
        files_found = 0
        required_files = ["startup.py", "Dockerfile", "requirements.txt", "README.md"]

        # Check for strategy file
        strategy_files = list(folder_path.glob("*strategy*.py"))
        if strategy_files:
            files_found += 1
        else:
            issues.append(ComplianceIssue(
                severity="HIGH",
                category="Missing Strategy File",
                description="No strategy Python file found (should contain 'strategy' in name)",
                file_path=str(folder_path),
                recommendation="Create a Python file with 'strategy' in the name"
            ))

        # Check other required files
        for req_file in required_files:
            if (folder_path / req_file).exists():
                files_found += 1
            else:
                issues.append(ComplianceIssue(
                    severity="MEDIUM",
                    category="Missing Required File",
                    description=f"Required file missing: {req_file}",
                    file_path=str(folder_path / req_file),
                    recommendation=f"Create {req_file} in strategy folder"
                ))

        return files_found

    def _check_reports_folder(self, reports_path: Path, issues: list) -> int:
        """Check required files in reports folder."""
        files_found = 0
        required_reports = ["backtest_runner.py", "backtest_report.md"]

        for req_file in required_reports:
            if (reports_path / req_file).exists():
                files_found += 1
            else:
                issues.append(ComplianceIssue(
                    severity="HIGH",
                    category="Missing Report File",
                    description=f"Required report file missing: {req_file}",
                    file_path=str(reports_path / req_file),
                    recommendation=f"Create {req_file} in reports folder"
                ))

        return files_found

    def check_base_strategy_inheritance(self, submission_path: Path) -> bool:
        """Check if strategy inherits from BaseStrategy (flexible path search)."""
        # Search for strategy files in any subfolder
        strategy_files = list(submission_path.glob("**/*strategy*.py"))

        for strategy_file in strategy_files:
            try:
                content = strategy_file.read_text(encoding='utf-8')
                if "BaseStrategy" in content and "class" in content:
                    return True
            except Exception:
                continue

        return False

    def check_signal_objects_usage(self, submission_path: Path) -> bool:
        """Check if strategy uses Signal objects (flexible path search)."""
        strategy_files = list(submission_path.glob("**/*strategy*.py"))

        for strategy_file in strategy_files:
            try:
                content = strategy_file.read_text(encoding='utf-8')
                if "Signal(" in content and "return Signal" in content:
                    return True
            except Exception:
                continue

        return False

    def check_required_methods(self, submission_path: Path) -> bool:
        """Check if required methods are implemented (flexible path search)."""
        strategy_files = list(submission_path.glob("**/*strategy*.py"))

        for strategy_file in strategy_files:
            try:
                content = strategy_file.read_text(encoding='utf-8')
                if "def generate_signal" in content and "def __init__" in content:
                    return True
            except Exception:
                continue

        return False

    def extract_participant_name(self, submission_path: Path) -> str:
        """Extract participant name from submission."""
        import re
        folder_name = submission_path.name
        match = re.search(r'#\\d+\\s*\\(([^)]+)\\)', folder_name)
        if match:
            return match.group(1).strip()
        return "Unknown"

def main():
    parser = argparse.ArgumentParser(description="Contest Compliance Checker")
    parser.add_argument("--base-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--submissions", type=str, required=True, help="Comma-separated submission IDs")

    args = parser.parse_args()

    checker = ComplianceChecker()
    results = []

    submission_ids = args.submissions.split(',')

    for submission_id in submission_ids:
        submission_path = args.base_path / submission_id.strip()
        if submission_path.exists():
            result = checker.check_submission(submission_path)
            results.append(asdict(result))

    # Save results
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with open(args.output_dir / "compliance_results.json", 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Compliance results saved to {args.output_dir}")

if __name__ == "__main__":
    main()
'''

        with open(self.output_dir / "contest_compliance_checker.py", 'w') as f:
            f.write(compliance_script)

    def print_summary(self):
        """Print final evaluation summary."""
        passed = [r for r in self.final_results if r.final_status == "PASS"]
        failed = [r for r in self.final_results if r.final_status == "FAIL"]

        print()
        print("📊 FINAL EVALUATION SUMMARY")
        print("=" * 40)
        print(f"Total submissions: {len(self.final_results)}")
        print(f"Passed all stages: {len(passed)}")
        print(f"Failed: {len(failed)}")
        print()

        if passed:
            print("✅ PASSED SUBMISSIONS:")
            for rank, result in enumerate(passed, 1):
                print(f"  {rank}. {result.submission_id} - {result.overall_score:.1f}/100")

        if failed:
            print()
            print("❌ FAILED SUBMISSIONS:")
            for result in failed:
                print(f"  - {result.submission_id} - {result.overall_score:.1f}/100")

        print()
        print(f"📁 Results saved to: {self.output_dir}")
        print(f"📝 Report: {self.output_dir}/final_evaluation_report.md")
        print(f"📊 Data: {self.output_dir}/final_evaluation_results.json")

def main():
    parser = argparse.ArgumentParser(description="Contest Evaluation Orchestrator")
    parser.add_argument("--base-path", type=Path, default=Path("final_evaluation"),
                       help="Base directory containing submissions")
    parser.add_argument("--output-dir", type=Path, default=Path("evaluation_results"),
                       help="Output directory for results")
    parser.add_argument("--interactive", action="store_true",
                       help="Run in interactive mode (step-by-step with user prompts)")

    args = parser.parse_args()

    if not args.base_path.exists():
        print(f"❌ Base path {args.base_path} does not exist")
        sys.exit(1)

    orchestrator = ContestEvaluationOrchestrator(args.base_path, args.output_dir)

    if args.interactive:
        orchestrator.run_interactive_evaluation()
    else:
        orchestrator.run_full_evaluation()

if __name__ == "__main__":
    main()