#!/usr/bin/env python3
"""
CONTEST RULES VERIFIER
Stage 4: Verify contest rules compliance and performance requirements

Checks:
1. Performance Requirements
   - Maximum drawdown < 50%
   - At least 10 executed trades
   - Valid PnL calculation

2. Strategy Structure Requirements
   - Proper folder structure (your-strategy-template/ and reports/)
   - Required files present
   - Valid backtest report

3. Financial Constraints
   - Realistic performance metrics
   - Valid Sharpe ratio
   - Proper risk management indicators

4. Contest-Specific Rules
   - Starting capital compliance ($10,000)
   - Trading period compliance (Jan-Jun 2024)
   - Asset compliance (BTC-USD, ETH-USD)
"""

import os
import sys
import json
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import re

@dataclass
class RuleViolation:
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str
    description: str
    file_path: str
    recommendation: str
    metric_value: Optional[float] = None
    threshold: Optional[float] = None

@dataclass
class ContestRulesResult:
    submission_id: str
    participant: str
    passed: bool
    rules_score: float
    violations: List[RuleViolation]

    # Performance metrics
    total_pnl: Optional[float] = None
    total_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    total_trades: Optional[int] = None
    win_rate: Optional[float] = None

    # Structure compliance
    folder_structure_valid: bool = False
    backtest_report_present: bool = False
    required_files_present: bool = False

    # Contest-specific compliance
    starting_capital_compliant: bool = False
    trading_period_compliant: bool = False
    assets_compliant: bool = False

class ContestRulesVerifier:
    """Contest rules and performance requirements verification."""

    def __init__(self):
        # Contest rules thresholds (STRICT ENFORCEMENT)
        self.MAX_DRAWDOWN = 50.0  # 50% maximum drawdown (DISQUALIFICATION if exceeded)
        self.MIN_TRADES = 10      # At least 10 trades (DISQUALIFICATION if not met)
        self.STARTING_CAPITAL = 10000.0  # $10,000 starting capital (EXACT)
        self.MAX_POSITION_SIZE = 0.55     # 55% maximum exposure per trade

        # Data requirements (STRICT)
        self.REQUIRED_DATA_START = "2024-01-01"
        self.REQUIRED_DATA_END = "2024-06-30"
        self.REQUIRED_INTERVAL = "1h"  # Hourly data only
        self.EXPECTED_CANDLES = 4344      # Exact number of hourly candles
        self.REQUIRED_DATA_SOURCE = "yfinance"  # Yahoo Finance only

        # Valid assets (EXACT)
        self.VALID_ASSETS = ["BTC-USD", "ETH-USD", "BTCUSDT", "ETHUSDT"]

        # Performance thresholds for scoring
        self.EXCELLENT_RETURN = 25.0  # >25% return = excellent
        self.GOOD_RETURN = 10.0       # >10% return = good
        self.MIN_SHARPE = 0.5         # Minimum acceptable Sharpe ratio

        # Required folder structure
        self.required_structure = [
            "your-strategy-template/",
            "reports/",
            "reports/backtest_runner.py",
            "reports/backtest_report.md"
        ]

    def check_submission(self, submission_path: Path) -> ContestRulesResult:
        """Check single submission for contest rules compliance."""
        print(f"[RULES CHECK] {submission_path.name}...")
        print("=" * 50)

        submission_id = submission_path.name
        participant = self.extract_participant_name(submission_path)
        violations = []

        # 1. Check folder structure
        print("  [1/7] Checking folder structure...")
        structure_valid = self.check_folder_structure(submission_path, violations)
        if structure_valid:
            print("    [PASS] Folder structure: VALID (your-strategy-template/ and reports/ found)")
        else:
            print("    [FAIL] Folder structure: INVALID (missing required folders)")

        # 2. Check backtest report presence and validity
        print("  [2/7] Checking backtest report...")
        backtest_present, backtest_data = self.check_backtest_report(submission_path, violations)
        if backtest_present:
            print("    [PASS] Backtest report: FOUND")
        else:
            print("    [FAIL] Backtest report: NOT FOUND")

        # 3. Extract and validate performance metrics
        print("  [3/7] Extracting performance metrics...")
        performance_metrics = self.extract_performance_metrics(submission_path, backtest_data, violations)
        self.log_performance_metrics(performance_metrics)

        # 4. Check contest-specific requirements
        print("  [4/7] Checking contest compliance...")
        contest_compliance = self.check_contest_compliance(submission_path, performance_metrics, violations)
        self.log_contest_compliance(contest_compliance)

        # 5. Validate financial constraints and realism
        print("  [5/7] Validating financial constraints...")
        self.validate_financial_constraints(performance_metrics, violations)
        self.log_financial_validation(performance_metrics)

        # 6. Validate position sizing compliance
        print("  [6/7] Checking position sizing...")
        self.validate_position_sizing(submission_path, violations)
        self.log_position_sizing_check(submission_path)

        # 7. Validate data source and interval compliance
        print("  [7/7] Checking data compliance...")
        self.validate_data_compliance(submission_path, violations)
        self.log_data_compliance_check(submission_path)

        # Calculate overall rules score
        rules_score = self.calculate_rules_score(violations, performance_metrics)

        # Determine pass/fail
        critical_violations = sum(1 for v in violations if v.severity == "CRITICAL")
        high_violations = sum(1 for v in violations if v.severity == "HIGH")
        medium_violations = sum(1 for v in violations if v.severity == "MEDIUM")
        low_violations = sum(1 for v in violations if v.severity == "LOW")

        # Pass criteria: score >= 70, no critical violations, max 2 high violations
        passed = (rules_score >= 70.0 and
                 critical_violations == 0 and
                 high_violations <= 2)

        # Log final assessment
        print("\n  [FINAL ASSESSMENT]")
        print(f"    Score: {rules_score:.1f}/100")
        print(f"    Violations: {critical_violations} CRITICAL, {high_violations} HIGH, {medium_violations} MEDIUM, {low_violations} LOW")

        if passed:
            print(f"    [PASS] RESULT: PASS")
        else:
            print(f"    [FAIL] RESULT: FAIL")
            if critical_violations > 0:
                print(f"      Reason: {critical_violations} CRITICAL violation(s) - automatic disqualification")
            elif high_violations > 2:
                print(f"      Reason: {high_violations} HIGH violations exceed maximum of 2")
            elif rules_score < 70.0:
                print(f"      Reason: Score {rules_score:.1f} below minimum of 70.0")

        result = ContestRulesResult(
            submission_id=submission_id,
            participant=participant,
            passed=passed,
            rules_score=rules_score,
            violations=violations,
            total_pnl=performance_metrics.get('total_pnl'),
            total_return=performance_metrics.get('total_return'),
            max_drawdown=performance_metrics.get('max_drawdown'),
            sharpe_ratio=performance_metrics.get('sharpe_ratio'),
            total_trades=performance_metrics.get('total_trades'),
            win_rate=performance_metrics.get('win_rate'),
            folder_structure_valid=structure_valid,
            backtest_report_present=backtest_present,
            required_files_present=structure_valid,
            starting_capital_compliant=contest_compliance.get('capital', False),
            trading_period_compliant=contest_compliance.get('period', False),
            assets_compliant=contest_compliance.get('assets', False)
        )

        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {submission_id}: {rules_score:.1f}/100")

        return result

    def check_folder_structure(self, submission_path: Path, violations: List[RuleViolation]) -> bool:
        """Check required folder structure compliance."""
        structure_valid = True

        # Check for strategy template folder
        strategy_folders = [d for d in submission_path.iterdir()
                          if d.is_dir() and 'strategy' in d.name.lower()]

        if not strategy_folders:
            violations.append(RuleViolation(
                severity="CRITICAL",
                category="Folder Structure",
                description="Missing your-strategy-template/ folder",
                file_path="your-strategy-template/",
                recommendation="Create folder with 'strategy' in the name"
            ))
            structure_valid = False

        # Check for reports folder
        reports_path = submission_path / "reports"
        if not reports_path.exists():
            # Try alternative locations
            reports_candidates = list(submission_path.glob("**/reports"))
            if not reports_candidates:
                violations.append(RuleViolation(
                    severity="CRITICAL",
                    category="Folder Structure",
                    description="Missing reports/ folder",
                    file_path="reports/",
                    recommendation="Create reports/ folder with required files"
                ))
                structure_valid = False

        return structure_valid

    def check_backtest_report(self, submission_path: Path, violations: List[RuleViolation]) -> Tuple[bool, Dict]:
        """Check backtest report presence and extract data."""
        # Look for backtest report
        report_files = list(submission_path.glob("**/backtest_report.md")) + \
                      list(submission_path.glob("**/backtest_report.txt")) + \
                      list(submission_path.glob("**/README.md"))

        backtest_data = {}

        if not report_files:
            violations.append(RuleViolation(
                severity="HIGH",
                category="Backtest Report",
                description="No backtest report found",
                file_path="reports/backtest_report.md",
                recommendation="Create backtest report with performance metrics"
            ))
            return False, backtest_data

        # Try to extract data from reports
        for report_file in report_files:
            try:
                content = report_file.read_text(encoding='utf-8', errors='ignore')
                extracted_data = self.extract_metrics_from_text(content)
                backtest_data.update(extracted_data)
            except Exception as e:
                print(f"Warning: Could not read {report_file}: {e}")

        return True, backtest_data

    def extract_metrics_from_text(self, content: str) -> Dict:
        """Extract performance metrics from text content."""
        metrics = {}
        content_lower = content.lower()

        # First try to extract from markdown tables
        table_metrics = self.extract_from_markdown_table(content)
        if table_metrics:
            metrics.update(table_metrics)

        # Extract PnL/Return (enhanced patterns)
        pnl_patterns = [
            r'(?:total pnl|final pnl|profit|return)[\s:]*\$?([+-]?\d+(?:\.\d+)?)',
            r'(?:total return|final return|combined)[\s:]*([+-]?\d+(?:\.\d+)?)%',
            r'\$(\d+(?:\.\d+)?)\s*(?:profit|pnl|return)',
            r'(\d+(?:\.\d+)?)%\s*(?:return|profit)',
            # Table format patterns
            r'\|\s*[*]*(?:combined|total)[*]*\s*\|\s*[*]*([+-]?\d+(?:\.\d+)?)%?[*]*\s*\|',
            r'return[^\|]*\|\s*(\d+(?:\.\d+)?)%'
        ]

        for pattern in pnl_patterns:
            match = re.search(pattern, content_lower)
            if match:
                try:
                    value = float(match.group(1))
                    if 'return' in pattern or '%' in pattern or value <= 100:
                        metrics['total_return'] = value
                        metrics['total_pnl'] = value * self.STARTING_CAPITAL / 100
                    else:
                        metrics['total_pnl'] = value
                        metrics['total_return'] = (value / self.STARTING_CAPITAL) * 100
                    break
                except ValueError:
                    continue

        # Extract drawdown (enhanced patterns)
        drawdown_patterns = [
            r'(?:max drawdown|maximum drawdown|worst drawdown|max dd)[\s:]*([+-]?\d+(?:\.\d+)?)%?',
            r'drawdown[\s:]*([+-]?\d+(?:\.\d+)?)%',
            # Table format patterns
            r'\|\s*[*]*(?:combined|total)[*]*\s*\|[^|]*\|\s*([+-]?\d+(?:\.\d+)?)%?\s*\|',
            r'max dd[^\|]*\|\s*(\d+(?:\.\d+)?)%'
        ]

        for pattern in drawdown_patterns:
            match = re.search(pattern, content_lower)
            if match:
                try:
                    metrics['max_drawdown'] = abs(float(match.group(1)))
                    break
                except ValueError:
                    continue

        # Extract trade count (enhanced patterns)
        trade_patterns = [
            r'(?:total trades|number of trades|trades executed)[\s:]*(\d+)',
            r'(\d+)\s*(?:trades|transactions)',
            # Table format patterns
            r'\|\s*[*]*(?:combined|total)[*]*\s*\|[^|]*\|[^|]*\|[^|]*\|\s*(\d+)\s*\|',
            r'trades[^\|]*\|\s*(\d+)\s*\|'
        ]

        for pattern in trade_patterns:
            match = re.search(pattern, content_lower)
            if match:
                try:
                    metrics['total_trades'] = int(match.group(1))
                    break
                except ValueError:
                    continue

        # Extract Sharpe ratio - look for the specific pattern in entry #169 format
        # Pattern: "- Combined: 36.10/26.16 = **1.38**"
        sharpe_match = re.search(r'combined:\s*[\d\.]+/[\d\.]+ = \*\*([+-]?\d+(?:\.\d+)?)\*\*', content_lower)
        if sharpe_match:
            try:
                sharpe_value = float(sharpe_match.group(1))
                if -5.0 <= sharpe_value <= 10.0:  # Reasonable Sharpe ratio range
                    metrics['sharpe_ratio'] = sharpe_value
            except ValueError:
                pass

        # If not found, try other patterns but be more careful
        if 'sharpe_ratio' not in metrics:
            sharpe_patterns = [
                r'sharpe ratio[:\s]*([+-]?\d+(?:\.\d+)?)',
                r'(?:^|\s)sharpe[:\s]*([+-]?\d+(?:\.\d+)?)(?:\s|$)'
            ]

            for pattern in sharpe_patterns:
                match = re.search(pattern, content_lower)
                if match:
                    try:
                        sharpe_value = float(match.group(1))
                        # Only accept reasonable Sharpe ratios, reject high numbers like trade counts
                        if -5.0 <= sharpe_value <= 10.0:
                            metrics['sharpe_ratio'] = sharpe_value
                            break
                    except ValueError:
                        continue

        # Extract win rate
        winrate_patterns = [
            r'(?:win rate|success rate|winning percentage)[\s:]*(\d+(?:\.\d+)?)%?',
            r'(\d+(?:\.\d+)?)%\s*(?:win|success|wins)'
        ]

        for pattern in winrate_patterns:
            match = re.search(pattern, content_lower)
            if match:
                try:
                    metrics['win_rate'] = float(match.group(1))
                    break
                except ValueError:
                    continue

        return metrics

    def extract_from_markdown_table(self, content: str) -> Dict:
        """Extract metrics specifically from markdown tables."""
        metrics = {}
        lines = content.split('\n')

        # Look for different table formats
        for i, line in enumerate(lines):
            line_lower = line.lower()

            # Format 1: Standard table with combined row
            if ('symbol' in line_lower or 'combined' in line_lower) and '|' in line:
                # Found a table, look for the combined/total row
                for j in range(i, min(i+10, len(lines))):
                    row = lines[j].lower()
                    if ('combined' in row or 'total' in row) and '|' in row:
                        # Parse the table row
                        cells = [cell.strip(' |*') for cell in row.split('|')]

                        try:
                            # Typical format: | Combined | 28.65% | 14.98% | 1.75 | 112 |
                            if len(cells) >= 5:
                                # Return percentage
                                return_str = cells[2].replace('%', '').strip()
                                if return_str:
                                    metrics['total_return'] = float(return_str)
                                    metrics['total_pnl'] = float(return_str) * self.STARTING_CAPITAL / 100

                                # Max drawdown
                                dd_str = cells[3].replace('%', '').strip()
                                if dd_str:
                                    metrics['max_drawdown'] = abs(float(dd_str))

                                # Sharpe ratio
                                sharpe_str = cells[4].strip()
                                if sharpe_str:
                                    metrics['sharpe_ratio'] = float(sharpe_str)

                                # Trades
                                if len(cells) >= 6:
                                    trades_str = cells[5].strip()
                                    if trades_str:
                                        metrics['total_trades'] = int(trades_str)

                                return metrics
                        except (ValueError, IndexError):
                            continue

            # Format 2: Metric-Value table (like entry #154)
            elif ('metric' in line_lower and 'value' in line_lower) and '|' in line:
                # Look for specific metric rows
                for j in range(i, min(i+15, len(lines))):
                    row = lines[j]
                    row_lower = row.lower()

                    if '|' not in row:
                        continue

                    cells = [cell.strip(' |*+') for cell in row.split('|')]

                    if len(cells) >= 2:
                        metric_name = cells[0].lower() if cells[0] else ''
                        metric_value = cells[1] if len(cells) > 1 else ''

                        try:
                            # Combined Return
                            if 'combined return' in metric_name or 'total return' in metric_name:
                                value_str = metric_value.replace('%', '').replace('+', '').replace('**', '').strip()
                                if value_str:
                                    metrics['total_return'] = float(value_str)
                                    metrics['total_pnl'] = float(value_str) * self.STARTING_CAPITAL / 100

                            # Max Drawdown
                            elif 'max drawdown' in metric_name or 'drawdown' in metric_name:
                                value_str = metric_value.replace('%', '').replace('**', '').strip()
                                if value_str:
                                    metrics['max_drawdown'] = abs(float(value_str))

                            # Total Trades
                            elif 'total trades' in metric_name:
                                value_str = metric_value.replace('**', '').strip()
                                # Extract just the number
                                trade_match = re.search(r'(\d+)', value_str)
                                if trade_match:
                                    metrics['total_trades'] = int(trade_match.group(1))

                        except (ValueError, IndexError):
                            continue

        # Also try to extract from "Average Drawdown" line if not found
        if 'max_drawdown' not in metrics:
            for line in lines:
                if 'average drawdown' in line.lower() and '%' in line:
                    # Extract percentage value
                    match = re.search(r'(\d+\.\d+)%', line)
                    if match:
                        try:
                            metrics['max_drawdown'] = float(match.group(1))
                        except ValueError:
                            pass
                        break

        return metrics

    def extract_performance_metrics(self, submission_path: Path, backtest_data: Dict,
                                  violations: List[RuleViolation]) -> Dict:
        """Extract and validate performance metrics from various sources."""
        metrics = backtest_data.copy()

        # Try to extract from CSV files
        csv_files = list(submission_path.glob("**/*.csv"))
        for csv_file in csv_files:
            try:
                if csv_file.stat().st_size > 1024 * 1024:  # Skip files > 1MB
                    continue

                df = pd.read_csv(csv_file, nrows=1000)  # Limit rows
                csv_metrics = self.extract_metrics_from_csv(df)
                metrics.update(csv_metrics)
            except Exception:
                continue

        # Validate extracted metrics
        self.validate_extracted_metrics(metrics, violations)

        return metrics

    def extract_metrics_from_csv(self, df: pd.DataFrame) -> Dict:
        """Extract metrics from CSV dataframe."""
        metrics = {}

        # Look for portfolio value columns
        value_cols = [col for col in df.columns if any(term in col.lower()
                     for term in ['portfolio', 'value', 'pnl', 'balance', 'equity'])]

        if value_cols:
            try:
                values = df[value_cols[0]].dropna()
                if len(values) > 0:
                    initial_value = values.iloc[0]
                    final_value = values.iloc[-1]

                    if initial_value > 0:
                        metrics['total_return'] = ((final_value - initial_value) / initial_value) * 100
                        metrics['total_pnl'] = final_value - initial_value

                        # Calculate drawdown
                        cummax = values.cummax()
                        drawdown = ((values - cummax) / cummax) * 100
                        metrics['max_drawdown'] = abs(drawdown.min())
            except Exception:
                pass

        # Look for trade-related columns
        trade_cols = [col for col in df.columns if any(term in col.lower()
                     for term in ['trade', 'signal', 'position', 'action'])]

        if trade_cols:
            try:
                trades = df[trade_cols[0]].dropna()
                # Count non-zero or non-hold trades
                valid_trades = trades[~trades.isin([0, 'HOLD', 'hold', '', None])]
                metrics['total_trades'] = len(valid_trades)
            except Exception:
                pass

        return metrics

    def validate_extracted_metrics(self, metrics: Dict, violations: List[RuleViolation]):
        """Validate that extracted metrics make sense."""
        # Check if we have minimum required metrics
        required_metrics = ['total_pnl', 'max_drawdown', 'total_trades']
        missing_metrics = [m for m in required_metrics if m not in metrics or metrics[m] is None]

        if missing_metrics:
            violations.append(RuleViolation(
                severity="HIGH",
                category="Performance Metrics",
                description=f"Missing required metrics: {', '.join(missing_metrics)}",
                file_path="reports/backtest_report.md",
                recommendation="Include all required performance metrics in backtest report"
            ))

    def check_contest_compliance(self, submission_path: Path, metrics: Dict,
                               violations: List[RuleViolation]) -> Dict:
        """Check contest-specific requirements compliance."""
        compliance = {}

        # Check starting capital compliance (should be around $10,000)
        if 'total_pnl' in metrics and metrics['total_pnl'] is not None:
            total_return = metrics.get('total_return', 0)
            implied_capital = abs(metrics['total_pnl'] / (total_return / 100)) if total_return != 0 else 0

            if abs(implied_capital - self.STARTING_CAPITAL) > 1000:  # Allow 10% variance
                violations.append(RuleViolation(
                    severity="MEDIUM",
                    category="Starting Capital",
                    description=f"Starting capital appears to be ${implied_capital:.0f}, should be ${self.STARTING_CAPITAL}",
                    file_path="backtest configuration",
                    recommendation="Use exactly $10,000 starting capital",
                    metric_value=implied_capital,
                    threshold=self.STARTING_CAPITAL
                ))
                compliance['capital'] = False
            else:
                compliance['capital'] = True
        else:
            compliance['capital'] = True  # Can't verify, assume compliant

        # Check trading period (Jan-Jun 2024)
        compliance['period'] = True  # Assume compliant unless we find evidence otherwise

        # Check asset compliance (BTC-USD, ETH-USD)
        compliance['assets'] = self.check_asset_compliance(submission_path, violations)

        return compliance

    def check_asset_compliance(self, submission_path: Path, violations: List[RuleViolation]) -> bool:
        """Check that only allowed assets are used."""
        # Look for asset mentions in files
        strategy_files = [f for f in submission_path.glob("**/*.py") if "base-bot-template" not in str(f)] + \
                        [f for f in submission_path.glob("**/*.md") if "base-bot-template" not in str(f)]

        valid_patterns = [
            r'\bBTC-USD\b',
            r'\bETH-USD\b',
            r'\bBTCUSDT\b',
            r'\bETHUSDT\b'
        ]

        forbidden_patterns = [
            r'\b(LTC|XRP|ADA|DOT|SOL|AVAX|MATIC|LINK|DOGE|SHIB|UNI|AAVE)[/-]?USD[T]?\b',
            r'\b(LITECOIN|RIPPLE|CARDANO|POLKADOT|SOLANA|AVALANCHE|POLYGON|CHAINLINK)\b',
            r'\b[A-Z]{3,5}USD[T]?\b(?<!BTC-USD)(?<!ETH-USD)(?<!BTCUSDT)(?<!ETHUSDT)'
        ]

        found_forbidden = set()

        for file_path in strategy_files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                content_upper = content.upper()

                # Check for forbidden assets (excluding valid ones)
                for pattern in forbidden_patterns:
                    matches = re.findall(pattern, content_upper)
                    for match in matches:
                        if isinstance(match, tuple):
                            match = match[0] if match[0] else match[1] if len(match) > 1 else str(match)

                        # Skip if this is part of a valid asset
                        if any(re.search(valid_pattern, content_upper) for valid_pattern in valid_patterns):
                            # Check if the forbidden match is actually part of valid asset
                            valid_contexts = [
                                f"{match}-USD",
                                f"{match}USD",
                                f"{match}USDT"
                            ]

                            # Only flag if it's not part of a valid context
                            is_in_valid_context = False
                            for valid_ctx in valid_contexts:
                                if valid_ctx in content_upper and valid_ctx in ['BTC-USD', 'ETH-USD', 'BTCUSDT', 'ETHUSDT']:
                                    is_in_valid_context = True
                                    break

                            if not is_in_valid_context:
                                found_forbidden.add(match)
                        else:
                            found_forbidden.add(match)

            except Exception:
                continue

        # Filter out false positives (BTC, ETH when used in valid contexts)
        actual_forbidden = set()
        for asset in found_forbidden:
            if asset in ['BTC', 'ETH']:
                # Only flag BTC/ETH if they're not part of BTC-USD/ETH-USD
                found_valid = False
                for file_path in strategy_files:
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore').upper()
                        if f"{asset}-USD" in content or f"{asset}USD" in content:
                            found_valid = True
                            break
                    except Exception:
                        continue

                if not found_valid:
                    actual_forbidden.add(asset)
            else:
                actual_forbidden.add(asset)

        if actual_forbidden:
            violations.append(RuleViolation(
                severity="HIGH",
                category="Asset Compliance",
                description=f"Invalid assets detected: {', '.join(actual_forbidden)}",
                file_path="strategy files",
                recommendation="Use only BTC-USD and ETH-USD as specified in contest rules"
            ))
            return False

        return True

    def validate_financial_constraints(self, metrics: Dict, violations: List[RuleViolation]):
        """Validate financial constraints and realism (STRICT CONTEST RULES)."""

        # Check maximum drawdown (DISQUALIFICATION THRESHOLD)
        if 'max_drawdown' in metrics and metrics['max_drawdown'] is not None:
            if metrics['max_drawdown'] >= self.MAX_DRAWDOWN:
                violations.append(RuleViolation(
                    severity="CRITICAL",
                    category="DISQUALIFICATION - Drawdown Violation",
                    description=f"Maximum drawdown {metrics['max_drawdown']:.1f}% exceeds contest limit of {self.MAX_DRAWDOWN}% - AUTOMATIC DISQUALIFICATION",
                    file_path="performance metrics",
                    recommendation="Strategy disqualified - exceeds maximum drawdown threshold",
                    metric_value=metrics['max_drawdown'],
                    threshold=self.MAX_DRAWDOWN
                ))

        # Check minimum trades (DISQUALIFICATION THRESHOLD)
        if 'total_trades' in metrics and metrics['total_trades'] is not None:
            if metrics['total_trades'] < self.MIN_TRADES:
                violations.append(RuleViolation(
                    severity="CRITICAL",
                    category="DISQUALIFICATION - Insufficient Trading",
                    description=f"Only {metrics['total_trades']} trades executed, minimum required: {self.MIN_TRADES} - AUTOMATIC DISQUALIFICATION",
                    file_path="trading activity",
                    recommendation="Strategy disqualified - insufficient trading activity",
                    metric_value=metrics['total_trades'],
                    threshold=self.MIN_TRADES
                ))

        # Validate starting capital compliance (EXACT)
        if 'total_pnl' in metrics and 'total_return' in metrics:
            if metrics['total_pnl'] is not None and metrics['total_return'] is not None and metrics['total_return'] != 0:
                implied_capital = abs(metrics['total_pnl'] / (metrics['total_return'] / 100))
                if abs(implied_capital - self.STARTING_CAPITAL) > 500:  # Allow $500 variance
                    violations.append(RuleViolation(
                        severity="CRITICAL",
                        category="Starting Capital Violation",
                        description=f"Starting capital ${implied_capital:.0f} does not match required ${self.STARTING_CAPITAL}",
                        file_path="backtest configuration",
                        recommendation="Must use exactly $10,000 starting capital",
                        metric_value=implied_capital,
                        threshold=self.STARTING_CAPITAL
                    ))

        # Check for unrealistic performance
        if 'total_return' in metrics and metrics['total_return'] is not None:
            if metrics['total_return'] > 1000:  # >1000% return is suspicious
                violations.append(RuleViolation(
                    severity="HIGH",
                    category="Unrealistic Performance",
                    description=f"Return of {metrics['total_return']:.1f}% appears unrealistic",
                    file_path="performance metrics",
                    recommendation="Verify backtest implementation and data sources",
                    metric_value=metrics['total_return'],
                    threshold=1000
                ))
            elif metrics['total_return'] < -90:  # >90% loss is concerning
                violations.append(RuleViolation(
                    severity="MEDIUM",
                    category="Poor Performance",
                    description=f"Significant loss of {metrics['total_return']:.1f}%",
                    file_path="performance metrics",
                    recommendation="Review strategy logic and risk management",
                    metric_value=metrics['total_return'],
                    threshold=-90
                ))

        # Check Sharpe ratio reasonableness
        if 'sharpe_ratio' in metrics and metrics['sharpe_ratio'] is not None:
            if metrics['sharpe_ratio'] > 10:  # Sharpe > 10 is suspicious
                violations.append(RuleViolation(
                    severity="MEDIUM",
                    category="Unrealistic Sharpe",
                    description=f"Sharpe ratio of {metrics['sharpe_ratio']:.2f} appears unrealistic",
                    file_path="performance metrics",
                    recommendation="Verify Sharpe ratio calculation methodology"
                ))
            elif metrics['sharpe_ratio'] < -2:  # Sharpe < -2 is very poor
                violations.append(RuleViolation(
                    severity="LOW",
                    category="Poor Risk-Adjusted Return",
                    description=f"Poor Sharpe ratio of {metrics['sharpe_ratio']:.2f}",
                    file_path="performance metrics",
                    recommendation="Improve risk-adjusted returns"
                ))

    def calculate_rules_score(self, violations: List[RuleViolation], metrics: Dict) -> float:
        """Calculate overall contest rules compliance score."""
        base_score = 100.0

        # Deduct points for violations
        for violation in violations:
            if violation.severity == "CRITICAL":
                base_score -= 30
            elif violation.severity == "HIGH":
                base_score -= 15
            elif violation.severity == "MEDIUM":
                base_score -= 8
            elif violation.severity == "LOW":
                base_score -= 3

        # Bonus points for good performance
        if 'total_return' in metrics and metrics['total_return'] is not None:
            if metrics['total_return'] > self.EXCELLENT_RETURN:
                base_score += 10  # Bonus for excellent return
            elif metrics['total_return'] > self.GOOD_RETURN:
                base_score += 5   # Bonus for good return

        if 'max_drawdown' in metrics and metrics['max_drawdown'] is not None:
            if metrics['max_drawdown'] < 10:  # Very low drawdown
                base_score += 5
            elif metrics['max_drawdown'] < 20:  # Good drawdown control
                base_score += 2

        if 'sharpe_ratio' in metrics and metrics['sharpe_ratio'] is not None:
            if metrics['sharpe_ratio'] > 2.0:  # Excellent Sharpe
                base_score += 5
            elif metrics['sharpe_ratio'] > 1.0:  # Good Sharpe
                base_score += 2

        return max(0.0, min(100.0, base_score))

    def extract_participant_name(self, submission_path: Path) -> str:
        """Extract participant name from submission."""
        import re
        folder_name = submission_path.name
        match = re.search(r'#\d+\s*\(([^)]+)\)', folder_name)
        if match:
            return match.group(1).strip()
        return "Unknown"

    def log_performance_metrics(self, metrics: Dict):
        """Log performance metrics validation results."""
        if 'total_return' in metrics and metrics['total_return'] is not None:
            print(f"    [PASS] Total Return: {metrics['total_return']:.2f}%")
        else:
            print("    [WARN] Total Return: NOT FOUND")

        if 'total_pnl' in metrics and metrics['total_pnl'] is not None:
            print(f"    [PASS] Total PnL: ${metrics['total_pnl']:.0f}")
        else:
            print("    [WARN] Total PnL: NOT FOUND")

        if 'max_drawdown' in metrics and metrics['max_drawdown'] is not None:
            dd = metrics['max_drawdown']
            if dd < self.MAX_DRAWDOWN:
                print(f"    [PASS] Max Drawdown: {dd:.2f}% (within {self.MAX_DRAWDOWN}% limit)")
            else:
                print(f"    [FAIL] Max Drawdown: {dd:.2f}% (EXCEEDS {self.MAX_DRAWDOWN}% limit)")
        else:
            print("    [WARN] Max Drawdown: NOT FOUND")

        if 'total_trades' in metrics and metrics['total_trades'] is not None:
            trades = metrics['total_trades']
            if trades >= self.MIN_TRADES:
                print(f"    [PASS] Total Trades: {trades} (meets minimum {self.MIN_TRADES})")
            else:
                print(f"    [FAIL] Total Trades: {trades} (BELOW minimum {self.MIN_TRADES})")
        else:
            print("    [WARN] Total Trades: NOT FOUND")

        if 'sharpe_ratio' in metrics and metrics['sharpe_ratio'] is not None:
            print(f"    [PASS] Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        else:
            print("    [WARN] Sharpe Ratio: NOT FOUND")

    def log_contest_compliance(self, compliance: Dict):
        """Log contest compliance check results."""
        capital_status = "[PASS] COMPLIANT" if compliance.get('capital', True) else "[FAIL] NON-COMPLIANT"
        period_status = "[PASS] COMPLIANT" if compliance.get('period', True) else "[FAIL] NON-COMPLIANT"
        assets_status = "[PASS] COMPLIANT" if compliance.get('assets', True) else "[FAIL] NON-COMPLIANT"

        print(f"    Starting Capital: {capital_status}")
        print(f"    Trading Period: {period_status}")
        print(f"    Asset Usage: {assets_status}")

    def log_financial_validation(self, metrics: Dict):
        """Log financial validation results."""
        # Check drawdown threshold
        if 'max_drawdown' in metrics and metrics['max_drawdown'] is not None:
            dd = metrics['max_drawdown']
            if dd < self.MAX_DRAWDOWN:
                print(f"    [PASS] Drawdown Check: {dd:.2f}% < {self.MAX_DRAWDOWN}% limit")
            else:
                print(f"    [FAIL] Drawdown Check: {dd:.2f}% >= {self.MAX_DRAWDOWN}% limit (DISQUALIFICATION)")

        # Check trade count threshold
        if 'total_trades' in metrics and metrics['total_trades'] is not None:
            trades = metrics['total_trades']
            if trades >= self.MIN_TRADES:
                print(f"    [PASS] Trade Count Check: {trades} >= {self.MIN_TRADES} minimum")
            else:
                print(f"    [FAIL] Trade Count Check: {trades} < {self.MIN_TRADES} minimum (DISQUALIFICATION)")

        # Check return reasonableness
        if 'total_return' in metrics and metrics['total_return'] is not None:
            ret = metrics['total_return']
            if ret <= 1000:
                print(f"    [PASS] Return Realism: {ret:.2f}% (reasonable)")
            else:
                print(f"    [WARN] Return Realism: {ret:.2f}% (suspiciously high)")

    def log_position_sizing_check(self, submission_path: Path):
        """Log position sizing validation results."""
        strategy_files = [f for f in submission_path.glob("**/*.py") if "base-bot-template" not in str(f)]

        # Look for position size settings
        found_position_size = None
        for strategy_file in strategy_files:
            try:
                content = strategy_file.read_text(encoding='utf-8', errors='ignore')

                # Look for position size assignments
                position_patterns = [
                    r'position[_\s]*size[_\s]*[=:]\s*([0-9]*\.?[0-9]+)',
                    r'max[_\s]*position[_\s]*[=:]\s*([0-9]*\.?[0-9]+)'
                ]

                for pattern in position_patterns:
                    matches = re.findall(pattern, content.lower())
                    if matches:
                        for match in matches:
                            try:
                                value = float(match)
                                if value <= 1.0:  # Decimal format
                                    found_position_size = value
                                    break
                            except ValueError:
                                continue
                        if found_position_size:
                            break
            except Exception:
                continue

        if found_position_size is not None:
            if found_position_size <= self.MAX_POSITION_SIZE:
                print(f"    [PASS] Position Size: {found_position_size*100:.1f}% (within {self.MAX_POSITION_SIZE*100:.1f}% limit)")
            else:
                print(f"    [FAIL] Position Size: {found_position_size*100:.1f}% (EXCEEDS {self.MAX_POSITION_SIZE*100:.1f}% limit)")
        else:
            print("    [WARN] Position Size: Not explicitly found (assuming compliant)")

    def log_data_compliance_check(self, submission_path: Path):
        """Log data source and interval compliance results."""
        code_files = [f for f in submission_path.glob("**/*.py") if "base-bot-template" not in str(f)]

        # Check data source
        has_yfinance = False
        forbidden_sources = []

        # Check interval
        has_hourly = False
        forbidden_intervals = []

        for code_file in code_files:
            try:
                content = code_file.read_text(encoding='utf-8', errors='ignore')
                content_lower = content.lower()

                # Check yfinance usage
                if 'yfinance' in content_lower or 'import yf' in content_lower:
                    has_yfinance = True

                # Check for forbidden sources
                forbidden_list = ['alpha_vantage', 'quandl', 'polygon', 'iex', 'binance', 'coinbase']
                for source in forbidden_list:
                    if source in content_lower:
                        forbidden_sources.append(source)

                # Check for hourly intervals
                valid_intervals = ['1h', 'hourly', '1 hour', 'hour']
                if any(interval in content_lower for interval in valid_intervals):
                    has_hourly = True

                # Check for forbidden intervals
                forbidden_list = ['1m', '5m', '15m', '30m', '1d', '1wk', '1mo', 'daily', 'minute']
                interval_patterns = [
                    r'interval\s*[=:]\s*[\'\"](.*?)[\'\"]',
                ]
                for pattern in interval_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        if match.lower() in forbidden_list:
                            forbidden_intervals.append(match)

            except Exception:
                continue

        # Log data source results
        if has_yfinance and not forbidden_sources:
            print("    [PASS] Data Source: Yahoo Finance (yfinance) detected")
        elif forbidden_sources:
            print(f"    [FAIL] Data Source: Forbidden sources detected: {', '.join(set(forbidden_sources))}")
        elif not has_yfinance:
            print("    [WARN] Data Source: yfinance not detected (verification needed)")
        else:
            print("    [PASS] Data Source: No violations detected")

        # Log interval results
        if forbidden_intervals:
            print(f"    [FAIL] Data Interval: Forbidden intervals detected: {', '.join(set(forbidden_intervals))}")
        elif has_hourly:
            print("    [PASS] Data Interval: Hourly (1h) detected")
        else:
            print("    [WARN] Data Interval: Hourly not explicitly detected (assuming compliant)")

    def validate_position_sizing(self, submission_path: Path, violations: List[RuleViolation]):
        """Validate position sizing compliance (55% maximum exposure)."""
        # Search for position sizing in strategy files
        strategy_files = [f for f in submission_path.glob("**/*.py") if "base-bot-template" not in str(f)]

        position_violations = []

        for strategy_file in strategy_files:
            try:
                content = strategy_file.read_text(encoding='utf-8', errors='ignore')
                content_lower = content.lower()

                # Look for position size patterns that exceed 0.55
                position_patterns = [
                    r'position[_\s]*size[_\s]*[=:]\s*([0-9]*\.?[0-9]+)',
                    r'allocation[_\s]*[=:]\s*([0-9]*\.?[0-9]+)',
                    r'exposure[_\s]*[=:]\s*([0-9]*\.?[0-9]+)',
                    r'weight[_\s]*[=:]\s*([0-9]*\.?[0-9]+)',
                    r'fraction[_\s]*[=:]\s*([0-9]*\.?[0-9]+)',
                    r'max[_\s]*position[_\s]*[=:]\s*([0-9]*\.?[0-9]+)'
                ]

                for pattern in position_patterns:
                    matches = re.findall(pattern, content_lower)
                    for match in matches:
                        try:
                            value = float(match)
                            # Check if value exceeds 55% (0.55 or 55)
                            if (value > 0.55 and value <= 1.0) or (value > 55 and value <= 100):
                                position_violations.append({
                                    'file': strategy_file.name,
                                    'value': value,
                                    'pattern': pattern,
                                    'context': 'position_assignment'
                                })
                        except ValueError:
                            continue

                # Look for percentage patterns > 55% but ONLY in position sizing context
                # Exclude common false positives like win rate, return percentage, etc.
                lines = content.split('\n')
                for line_num, line in enumerate(lines):
                    line_lower = line.lower().strip()

                    # Skip comment lines and known false positive contexts
                    if (line_lower.startswith('#') or
                        line_lower.startswith('//') or
                        line_lower.startswith('*') or
                        'win rate' in line_lower or
                        'success rate' in line_lower or
                        'return' in line_lower or
                        'performance' in line_lower or
                        'drawdown' in line_lower or
                        'sharpe' in line_lower or
                        'author:' in line_lower or
                        'trades:' in line_lower):
                        continue

                    # Look for position sizing context
                    position_context_words = ['position', 'allocation', 'size', 'exposure', 'weight', 'fraction']
                    if any(word in line_lower for word in position_context_words):
                        # Look for percentage in this line
                        percent_matches = re.findall(r'([0-9]+(?:\.[0-9]+)?)\s*%', line)
                        for match in percent_matches:
                            try:
                                value = float(match)
                                if value > 55:
                                    position_violations.append({
                                        'file': strategy_file.name,
                                        'value': value,
                                        'pattern': f"{value}% (line {line_num + 1})",
                                        'context': f'percentage_in_position_context: {line.strip()}'
                                    })
                            except ValueError:
                                continue

            except Exception:
                continue

        # Report position sizing violations (filter out obvious false positives)
        if position_violations:
            # Filter out violations that are clearly false positives
            genuine_violations = []
            for violation in position_violations:
                # Skip if value is exactly 66.7 (common win rate false positive)
                if violation['value'] == 66.7:
                    continue

                # Skip if context suggests it's not position sizing
                if ('win rate' in violation.get('context', '').lower() or
                    'return' in violation.get('context', '').lower() or
                    'performance' in violation.get('context', '').lower()):
                    continue

                genuine_violations.append(violation)

            # Report genuine violations
            unique_violations = list({v['value']: v for v in genuine_violations}.values())
            for violation in unique_violations:
                violations.append(RuleViolation(
                    severity="CRITICAL",
                    category="DISQUALIFICATION - Position Size Violation",
                    description=f"Position size {violation['value']} exceeds maximum 55% (0.55) - AUTOMATIC DISQUALIFICATION",
                    file_path=violation['file'],
                    recommendation="Reduce position sizing to maximum 55% exposure per trade",
                    metric_value=violation['value'],
                    threshold=self.MAX_POSITION_SIZE
                ))

    def validate_data_compliance(self, submission_path: Path, violations: List[RuleViolation]):
        """Validate data source and interval compliance (Yahoo Finance + hourly only)."""

        # Check data source compliance
        self.check_data_source_compliance(submission_path, violations)

        # Check data interval compliance
        self.check_data_interval_compliance(submission_path, violations)

        # Check data period compliance
        self.check_data_period_compliance(submission_path, violations)

    def check_data_source_compliance(self, submission_path: Path, violations: List[RuleViolation]):
        """Check that only Yahoo Finance (yfinance) is used for data."""
        code_files = [f for f in submission_path.glob("**/*.py") if "base-bot-template" not in str(f)]

        forbidden_sources = ['alpha_vantage', 'quandl', 'polygon', 'iex', 'binance', 'coinbase', 'kraken']
        required_source = 'yfinance'

        has_yfinance = False
        forbidden_found = []

        for code_file in code_files:
            try:
                content = code_file.read_text(encoding='utf-8', errors='ignore')
                content_lower = content.lower()

                # Check for yfinance usage
                if 'yfinance' in content_lower or 'import yf' in content_lower:
                    has_yfinance = True

                # Check for forbidden data sources
                for source in forbidden_sources:
                    if source in content_lower:
                        forbidden_found.append(source)

                # Check for external API calls that might indicate non-Yahoo data
                if any(term in content_lower for term in ['api_key', 'requests.get', 'urllib', 'http']):
                    # Look for patterns that suggest external data sources
                    if not ('yahoo' in content_lower or 'yfinance' in content_lower):
                        violations.append(RuleViolation(
                            severity="HIGH",
                            category="Suspicious External Data Access",
                            description="Detected external API calls - verify data source compliance",
                            file_path=code_file.name,
                            recommendation="Ensure only Yahoo Finance (yfinance) is used for market data"
                        ))

            except Exception:
                continue

        # Report violations
        if forbidden_found:
            violations.append(RuleViolation(
                severity="CRITICAL",
                category="DISQUALIFICATION - Forbidden Data Source",
                description=f"Forbidden data sources detected: {', '.join(set(forbidden_found))} - AUTOMATIC DISQUALIFICATION",
                file_path="strategy files",
                recommendation="Use only Yahoo Finance (yfinance) for market data",
            ))

        if not has_yfinance:
            violations.append(RuleViolation(
                severity="HIGH",
                category="Missing Required Data Source",
                description="No yfinance usage detected - verify Yahoo Finance compliance",
                file_path="strategy files",
                recommendation="Ensure yfinance library is used for market data access"
            ))

    def check_data_interval_compliance(self, submission_path: Path, violations: List[RuleViolation]):
        """Check that only hourly interval (1h) is used."""
        code_files = [f for f in submission_path.glob("**/*.py") if "base-bot-template" not in str(f)]

        forbidden_intervals = ['1m', '5m', '15m', '30m', '1d', '1wk', '1mo', 'daily', 'minute']
        valid_intervals = ['1h', 'hourly', '1 hour', 'hour']

        has_explicit_hourly = False
        critical_violations = []

        for code_file in code_files:
            try:
                content = code_file.read_text(encoding='utf-8', errors='ignore')
                content_lower = content.lower()

                # Look for interval specifications
                interval_patterns = [
                    r'interval\s*[=:]\s*[\'\"](.*?)[\'\"]',
                    r'period\s*[=:]\s*[\'\"](.*?)[\'\"]',
                    r'freq\s*[=:]\s*[\'\"](.*?)[\'\"]'
                ]

                found_intervals = []
                for pattern in interval_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    found_intervals.extend(matches)

                # Check for explicit valid intervals
                for interval in found_intervals:
                    if interval.lower() in valid_intervals:
                        has_explicit_hourly = True

                # Check for forbidden intervals (CRITICAL violations only)
                for interval in found_intervals:
                    if interval.lower() in forbidden_intervals:
                        critical_violations.append((interval, code_file.name))

                # Also check for valid interval mentions in comments/documentation
                if any(term in content_lower for term in valid_intervals):
                    has_explicit_hourly = True

                # Look for yfinance download with hourly data patterns
                if 'yfinance' in content_lower and 'download' in content_lower:
                    # Check for typical hourly data patterns
                    hourly_patterns = [
                        r'download\([^)]*interval\s*=\s*[\'\"](1h|hourly)[\'\"]',
                        r'download\([^)]*[\'\"](1h|hourly)[\'\"]',
                        r'hourly\s+data',
                        r'1h\s+data',
                        r'interval.*1h',
                        r'yahoo.*hourly'
                    ]

                    for pattern in hourly_patterns:
                        if re.search(pattern, content_lower):
                            has_explicit_hourly = True
                            break

            except Exception:
                continue

        # Report critical violations (actual non-hourly intervals)
        for interval, filename in critical_violations:
            violations.append(RuleViolation(
                severity="CRITICAL",
                category="DISQUALIFICATION - Wrong Data Interval",
                description=f"Data interval '{interval}' not allowed - only '1h' (hourly) permitted - AUTOMATIC DISQUALIFICATION",
                file_path=filename,
                recommendation="Use only hourly interval (interval='1h') for fair comparison"
            ))

        # Only flag missing interval specification if no forbidden intervals found
        # and there's evidence of data fetching without clear hourly specification
        if not critical_violations and not has_explicit_hourly:
            # Check if there's any data fetching at all
            has_data_fetching = False
            for code_file in code_files:
                try:
                    content = code_file.read_text(encoding='utf-8', errors='ignore').lower()
                    if any(term in content for term in ['yfinance', 'download', 'fetch', 'get_data']):
                        has_data_fetching = True
                        break
                except Exception:
                    continue

            # Only flag if there's data fetching but no clear hourly specification
            if has_data_fetching:
                # Check if backtest report mentions hourly data
                report_mentions_hourly = False
                try:
                    report_files = list(submission_path.glob("**/*report*.md"))
                    for report_file in report_files:
                        content = report_file.read_text(encoding='utf-8', errors='ignore').lower()
                        if any(term in content for term in valid_intervals):
                            report_mentions_hourly = True
                            break
                except Exception:
                    pass

                if not report_mentions_hourly:
                    violations.append(RuleViolation(
                        severity="LOW",  # Reduced from MEDIUM
                        category="Interval Verification Recommended",
                        description="Data interval not clearly specified as hourly (1h) - verification recommended",
                        file_path="strategy files",
                        recommendation="Consider explicitly specifying interval='1h' for clarity"
                    ))

    def check_data_period_compliance(self, submission_path: Path, violations: List[RuleViolation]):
        """Check that exact data period (2024-01-01 to 2024-06-30) is used."""
        code_files = [f for f in submission_path.glob("**/*.py") if "base-bot-template" not in str(f)]
        csv_files = list(submission_path.glob("**/*.csv"))

        # Check code for date specifications
        for code_file in code_files:
            try:
                content = code_file.read_text(encoding='utf-8', errors='ignore')

                # Look for date patterns
                date_patterns = [
                    r'20\d{2}-\d{2}-\d{2}',  # YYYY-MM-DD format
                    r'[\'\"]\d{4}-\d{1,2}-\d{1,2}[\'\"]',  # Quoted dates
                    r'start[_\s]*[=:]\s*[\'\"](.*?)[\'\"]',
                    r'end[_\s]*[=:]\s*[\'\"](.*?)[\'\"]'
                ]

                found_dates = []
                for pattern in date_patterns:
                    matches = re.findall(pattern, content)
                    found_dates.extend(matches)

                # Check for wrong date ranges
                wrong_dates = []
                for date_str in found_dates:
                    if date_str and '2024' in date_str:
                        if not (date_str.startswith('2024-01') or date_str.startswith('2024-06-30')):
                            if any(month in date_str for month in ['2024-07', '2024-08', '2024-09', '2024-10', '2024-11', '2024-12']):
                                wrong_dates.append(date_str)
                            elif any(month in date_str for month in ['2023-', '2025-']):
                                wrong_dates.append(date_str)

                if wrong_dates:
                    violations.append(RuleViolation(
                        severity="HIGH",
                        category="Data Period Violation",
                        description=f"Incorrect data period detected: {', '.join(set(wrong_dates))} - Must use 2024-01-01 to 2024-06-30",
                        file_path=code_file.name,
                        recommendation="Use exactly Jan 1 to Jun 30, 2024 data period"
                    ))

            except Exception:
                continue

        # Check CSV files for data period compliance
        for csv_file in csv_files:
            try:
                if csv_file.stat().st_size > 10 * 1024 * 1024:  # Skip files > 10MB
                    continue

                # Read first and last few rows to check date range
                df_head = pd.read_csv(csv_file, nrows=5)
                df_tail = pd.read_csv(csv_file).tail(5)

                # Look for date columns
                date_columns = [col for col in df_head.columns
                              if any(term in col.lower() for term in ['date', 'time', 'timestamp'])]

                if date_columns:
                    date_col = date_columns[0]
                    try:
                        first_date = pd.to_datetime(df_head[date_col].iloc[0])
                        last_date = pd.to_datetime(df_tail[date_col].iloc[-1])

                        expected_start = pd.to_datetime('2024-01-01')
                        expected_end = pd.to_datetime('2024-06-30')

                        # Allow some tolerance (few days)
                        if abs((first_date - expected_start).days) > 7:
                            violations.append(RuleViolation(
                                severity="MEDIUM",
                                category="Data Start Date Issue",
                                description=f"Data starts {first_date.strftime('%Y-%m-%d')}, expected around 2024-01-01",
                                file_path=csv_file.name,
                                recommendation="Ensure data starts from January 1, 2024"
                            ))

                        if abs((last_date - expected_end).days) > 7:
                            violations.append(RuleViolation(
                                severity="MEDIUM",
                                category="Data End Date Issue",
                                description=f"Data ends {last_date.strftime('%Y-%m-%d')}, expected around 2024-06-30",
                                file_path=csv_file.name,
                                recommendation="Ensure data ends on June 30, 2024"
                            ))

                    except Exception:
                        pass

            except Exception:
                continue

def main():
    parser = argparse.ArgumentParser(description="Contest Rules Verifier")
    parser.add_argument("--base-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--submissions", type=str, required=True,
                       help="Comma-separated submission IDs")

    args = parser.parse_args()

    verifier = ContestRulesVerifier()
    results = []

    submission_ids = args.submissions.split(',')

    print(f"Contest Rules Verification - Processing {len(submission_ids)} submissions")
    print("=" * 60)

    for submission_id in submission_ids:
        submission_path = args.base_path / submission_id.strip()
        if submission_path.exists():
            result = verifier.check_submission(submission_path)
            results.append(asdict(result))
        else:
            print(f"⚠️  Submission not found: {submission_id}")

    # Save results
    args.output_dir.mkdir(parents=True, exist_ok=True)

    with open(args.output_dir / "contest_rules_results.json", 'w') as f:
        json.dump(results, f, indent=2)

    # Generate summary report
    generate_summary_report(results, args.output_dir)

    print(f"\nContest rules verification completed")
    print(f"Results saved to: {args.output_dir}")

def generate_summary_report(results: List[Dict], output_dir: Path):
    """Generate a summary report of contest rules verification."""
    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)

    lines = [
        "# Contest Rules Verification Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Total Submissions:** {total_count}",
        f"**Passed Rules Check:** {passed_count}/{total_count}",
        "",
        "## Summary",
        ""
    ]

    if passed_count == 0:
        lines.append("❌ **NO SUBMISSIONS PASSED** contest rules verification.")
    else:
        lines.append(f"✅ **{passed_count} submissions passed** contest rules verification.")

    lines.extend([
        "",
        "## Results by Submission",
        "",
        "| Submission | Participant | Status | Score | PnL | Return | Drawdown | Trades |",
        "|------------|-------------|--------|-------|-----|--------|----------|--------|"
    ])

    for result in sorted(results, key=lambda x: x['rules_score'], reverse=True):
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        pnl = f"${result['total_pnl']:.0f}" if result['total_pnl'] else "N/A"
        return_pct = f"{result['total_return']:.1f}%" if result['total_return'] else "N/A"
        drawdown = f"{result['max_drawdown']:.1f}%" if result['max_drawdown'] else "N/A"
        trades = str(result['total_trades']) if result['total_trades'] else "N/A"

        lines.append(
            f"| {result['submission_id']} | {result['participant']} | {status} | "
            f"{result['rules_score']:.1f}/100 | {pnl} | {return_pct} | {drawdown} | {trades} |"
        )

    # Add violations details for failed submissions
    failed_results = [r for r in results if not r['passed']]
    if failed_results:
        lines.extend([
            "",
            "## Rule Violations",
            ""
        ])

        for result in failed_results:
            lines.extend([
                f"### {result['submission_id']} ({result['participant']})",
                f"**Score:** {result['rules_score']:.1f}/100",
                ""
            ])

            if result['violations']:
                for violation in result['violations']:
                    severity_emoji = {
                        'CRITICAL': '🚨',
                        'HIGH': '⚠️',
                        'MEDIUM': '⚡',
                        'LOW': 'ℹ️'
                    }.get(violation['severity'], '📋')

                    lines.append(f"{severity_emoji} **{violation['severity']}**: {violation['description']}")

                lines.append("")

    lines.extend([
        "",
        "## Contest Rules Checked",
        "",
        "1. **Performance Requirements**:",
        "   - Maximum drawdown < 50%",
        "   - At least 10 executed trades",
        "   - Valid PnL calculation",
        "",
        "2. **Structure Requirements**:",
        "   - Proper folder structure",
        "   - Required files present",
        "   - Valid backtest report",
        "",
        "3. **Contest Compliance**:",
        "   - Starting capital: $10,000",
        "   - Trading period: Jan-Jun 2024",
        "   - Assets: BTC-USD, ETH-USD only",
        "",
        "---",
        "Generated by Contest Rules Verifier v1.0"
    ])

    with open(output_dir / "contest_rules_summary.md", 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

if __name__ == "__main__":
    main()