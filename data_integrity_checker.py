#!/usr/bin/env python3
"""
DATA INTEGRITY CHECKER
Stage 3: Detect data manipulation and synthetic data injection

Checks for:
1. Hardcoded price data or market values
2. Synthetic/fake data generation
3. Hindsight bias (future data leakage)
4. Backdated or manipulated timestamps
5. Non-market hours trading data
6. Suspicious data patterns indicating manipulation
7. Unrealistic market data (prices, volumes, spreads)
"""

import os
import sys
import ast
import json
import re
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, time
from dataclasses import dataclass, asdict
import pandas as pd

@dataclass
class DataIntegrityIssue:
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str
    description: str
    file_path: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    recommendation: str = ""

@dataclass
class DataIntegrityResult:
    submission_id: str
    participant: str
    passed: bool
    integrity_score: float
    issues: List[DataIntegrityIssue]

    # Specific integrity checks
    hardcoded_data_detected: bool
    synthetic_data_detected: bool
    hindsight_bias_detected: bool
    suspicious_timestamps: bool
    unrealistic_data_patterns: bool
    non_market_hours_trading: bool

    scan_timestamp: str

class DataIntegrityChecker:
    """Detect data manipulation and synthetic data in trading strategies."""

    def __init__(self):
        # SURGICAL hardcoded market data patterns - ONLY target actual market data fraud
        self.hardcoded_patterns = [
            # Direct market price assignment (high-value prices only)
            r'(?:market_|current_|last_)?price\s*=\s*[\d.]{4,}',        # price = 1567.8 (4+ digits = likely stock price)
            r'(?:market_)?close\s*=\s*[\d.]{4,}',                       # close = 1234.5 (4+ digits)
            r'(?:market_)?open\s*=\s*[\d.]{4,}',                        # open = 987.65 (4+ digits)
            r'(?:market_)?high\s*=\s*[\d.]{4,}',                        # high = 1567.8 (4+ digits)
            r'(?:market_)?low\s*=\s*[\d.]{4,}',                         # low = 876.54 (4+ digits)
            r'(?:bid_|ask_)price\s*=\s*[\d.]{4,}',                     # bid_price = 1567.8

            # Volume (large numbers only)
            r'(?:market_)?volume\s*=\s*[\d.]{6,}',                     # volume = 100000+ (6+ digits)

            # DataFrame market data manipulation (explicit column names)
            r'df\[[\'"](Close|Open|High|Low|Volume)[\'"]\]\s*=\s*[\d.]{4,}',  # df['Close'] = 1234.5
            r'data\[[\'"](Close|Open|High|Low|Volume)[\'"]\]\s*=\s*[\d.]{4,}', # data['Close'] = 1234.5

            # Bulk market data arrays (long arrays of price-like numbers)
            r'np\.array\(\[[\d.,\s]{20,}\]\)',                         # np.array with 20+ chars of numbers
            r'pd\.DataFrame\(\{[^}]*[\'"](Close|Open|High|Low|Volume)[^}]*:.*[\d.]{4,}.*\}\)',

            # Hardcoded market conditions with specific prices
            r'if\s+.*price.*[>=<]+\s*[\d.]{4,}',                       # if price > 1567.8 (4+ digits)
            r'while\s+.*price.*[>=<]+\s*[\d.]{4,}',                    # while price < 1234.5
        ]

        # COMPREHENSIVE synthetic data patterns
        self.synthetic_patterns = [
            # Random/algorithmic data generation
            r'np\.random\.(randn|normal|uniform|randint|choice)',  # NumPy random
            r'random\.(gauss|uniform|normalvariate|randint|choice|sample)', # Python random
            r'np\.linspace\(',                        # Linear data sequences
            r'np\.arange\(',                          # Arithmetic sequences
            r'range\(\d{2,}\)',                       # Large ranges as data (10+ elements)
            r'np\.(ones|zeros|full)\(\d+',           # Constant arrays with size

            # Explicit fake data
            r'fake.*data',                            # fake_data, fake_prices
            r'mock.*data',                            # mock_data, mock_prices
            r'test.*data',                            # test_data (when not in test files)
            r'dummy.*data',                           # dummy_data, dummy_prices
            r'simulate.*data',                        # simulated_data
            r'synthetic.*data',                       # synthetic_data
            r'artificial.*data',                      # artificial_data
            r'generated.*prices',                     # generated_prices

            # Mathematical price generation
            r'math\.sin\(.*\)\s*\*.*price',          # sin wave price generation
            r'math\.cos\(.*\)\s*\*.*price',          # cos wave price generation
            r'np\.sin\(.*\)\s*\*.*[\d.]+',           # NumPy trig functions for prices
            r'fibonacci.*price',                      # Fibonacci-based prices
            r'for.*in.*range.*price.*=',             # Loop-generated prices
        ]

        # Hindsight bias patterns
        self.hindsight_patterns = [
            r'shift\(-\d+\)',                         # Negative shift (future data)
            r'\.loc\[.*:.*\+.*\]',                    # Future indexing
            r'future.*data',                          # Explicit future data
            r'lookahead',                             # Look-ahead bias
            r'tomorrow',                              # Future reference
            r'next.*day',                             # Next day data
            r'forecast.*actual',                      # Using forecast as actual
        ]

        # Suspicious timestamp patterns
        self.timestamp_patterns = [
            r'datetime\(202[0-4].*23:59',             # Suspicious end-of-day times
            r'datetime\(.*00:00:00\)',                # Exact midnight (suspicious)
            r'pd\.Timestamp\(.*weekend',              # Weekend trading
            r'holiday.*trading',                      # Holiday trading
            r'3[2-9]:\d{2}:\d{2}',                    # Invalid hours (>23)
            r'[6-9][0-9]:\d{2}:\d{2}',               # Invalid minutes/seconds (>59)
        ]

        # Market hours (NYSE: 9:30 AM - 4:00 PM EST)
        self.market_open = time(9, 30)
        self.market_close = time(16, 0)

        # Unrealistic data thresholds
        self.unrealistic_thresholds = {
            'price_change_percent': 50.0,            # >50% price change in one period
            'volume_spike_ratio': 100.0,             # >100x normal volume
            'spread_percent': 10.0,                  # >10% bid-ask spread
            'zero_volume_consecutive': 10,           # >10 consecutive zero volume periods
        }

    def check_submission(self, submission_path: Path) -> DataIntegrityResult:
        """Perform data integrity check on submission."""
        print(f"[DATA INTEGRITY] {submission_path.name}...")

        submission_id = submission_path.name
        participant = self._extract_participant_name(submission_path)
        issues = []

        # 1. Check strategy files for hardcoded data
        hardcoded_detected = self._check_hardcoded_data(submission_path, issues)

        # 2. Check for synthetic data generation
        synthetic_detected = self._check_synthetic_data(submission_path, issues)

        # 3. Check for hindsight bias
        hindsight_detected = self._check_hindsight_bias(submission_path, issues)

        # 4. Check timestamp manipulation
        timestamp_issues = self._check_timestamp_manipulation(submission_path, issues)

        # 5. Check backtest data for unrealistic patterns
        unrealistic_patterns = self._check_unrealistic_data_patterns(submission_path, issues)

        # 6. Check for non-market hours trading
        non_market_trading = self._check_non_market_hours_trading(submission_path, issues)

        # 7. Check yfinance authenticity
        yfinance_bypass = self._check_yfinance_authenticity(submission_path, issues)

        # 8. Check for suspicious performance claims (disabled for contest - too many false positives)
        # suspicious_performance = self._check_suspicious_performance_patterns(submission_path, issues)
        suspicious_performance = False

        # Calculate integrity score
        integrity_score = self._calculate_integrity_score(issues)

        # Pass criteria: No CRITICAL issues AND score >= 70
        critical_failed = any(issue.severity == "CRITICAL" for issue in issues)
        passed = not critical_failed and integrity_score >= 70.0

        result = DataIntegrityResult(
            submission_id=submission_id,
            participant=participant,
            passed=passed,
            integrity_score=integrity_score,
            issues=issues,
            hardcoded_data_detected=hardcoded_detected,
            synthetic_data_detected=synthetic_detected,
            hindsight_bias_detected=hindsight_detected,
            suspicious_timestamps=timestamp_issues,
            unrealistic_data_patterns=unrealistic_patterns,
            non_market_hours_trading=non_market_trading,
            scan_timestamp=datetime.now().isoformat()
        )

        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {submission_id}: {integrity_score:.1f}/100")
        if not passed:
            critical_count = sum(1 for issue in issues if issue.severity == "CRITICAL")
            if critical_count > 0:
                print(f"        CRITICAL DATA ISSUES: {critical_count}")

        return result

    def _check_hardcoded_data(self, submission_path: Path, issues: List[DataIntegrityIssue]) -> bool:
        """Check for hardcoded price/market data."""
        detected = False

        # Only check critical strategy and backtest files
        critical_files = [
            submission_path / "your-strategy-template" / "your_strategy.py",
            submission_path / "reports" / "backtest_runner.py"
        ]

        strategy_files = [f for f in critical_files if f.exists()]

        for file_path in strategy_files:
            if "test" in file_path.name.lower() or "example" in file_path.name.lower():
                continue

            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')

                for i, line in enumerate(lines, 1):
                    # Skip variable initialization and common patterns
                    line_stripped = line.strip()

                    # Skip legitimate patterns and comments
                    if line_stripped.startswith('#') or \
                       (line_stripped.startswith('self.') and ('= 0.0' in line_stripped or '= 0' in line_stripped or '= None' in line_stripped)) or \
                       'config.get' in line_stripped or \
                       '_period' in line_stripped or \
                       '_threshold' in line_stripped or \
                       'param' in line_stripped.lower() or \
                       'optimization' in line_stripped.lower() or \
                       'range' in line_stripped.lower() or \
                       ('=' in line_stripped and '[' in line_stripped and any(param_word in line_stripped.lower() for param_word in ['period', 'threshold', 'param', 'factor', 'ratio', 'weight', 'alpha', 'beta', 'gamma'])):
                        continue

                    for pattern in self.hardcoded_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            detected = True
                            issues.append(DataIntegrityIssue(
                                severity="CRITICAL",
                                category="Hardcoded Data",
                                description=f"Hardcoded market data detected: {line.strip()}",
                                file_path=str(file_path.relative_to(submission_path)),
                                line_number=i,
                                code_snippet=line.strip(),
                                recommendation="Use authentic market data from yfinance or other legitimate sources"
                            ))

            except Exception as e:
                continue

        return detected

    def _check_synthetic_data(self, submission_path: Path, issues: List[DataIntegrityIssue]) -> bool:
        """Check for synthetic/fake data generation."""
        detected = False

        # Only check critical strategy files
        critical_files = [
            submission_path / "your-strategy-template" / "your_strategy.py",
            submission_path / "reports" / "backtest_runner.py"
        ]

        strategy_files = [f for f in critical_files if f.exists()]

        for file_path in strategy_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')

                for i, line in enumerate(lines, 1):
                    line_stripped = line.strip()

                    # Skip comments, tests, and parameter optimization
                    if line_stripped.startswith('#') or \
                       any(word in line.lower() for word in ['test', 'demo', 'example', 'mock', 'param', 'optimization', 'grid', 'search']):
                        continue

                    for pattern in self.synthetic_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            # Additional context check - only flag if used for market data variables
                            if any(market_term in line.lower() for market_term in ['price', 'close', 'open', 'high', 'low', 'volume', 'data', 'ohlc']):
                                detected = True
                                issues.append(DataIntegrityIssue(
                                    severity="HIGH",
                                    category="Synthetic Data",
                                    description=f"Synthetic data generation detected: {line.strip()}",
                                    file_path=str(file_path.relative_to(submission_path)),
                                    line_number=i,
                                    code_snippet=line.strip(),
                                    recommendation="Remove synthetic data generation; use only real market data"
                                ))

            except Exception:
                continue

        return detected

    def _check_hindsight_bias(self, submission_path: Path, issues: List[DataIntegrityIssue]) -> bool:
        """Check for hindsight bias (using future data)."""
        detected = False

        # Only check critical strategy files
        critical_files = [
            submission_path / "your-strategy-template" / "your_strategy.py"
        ]

        strategy_files = [f for f in critical_files if f.exists()]

        for file_path in strategy_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')

                for i, line in enumerate(lines, 1):
                    line_stripped = line.strip()

                    # Skip comments - very important to avoid false positives!
                    if line_stripped.startswith('#'):
                        continue

                    for pattern in self.hindsight_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            detected = True
                            issues.append(DataIntegrityIssue(
                                severity="CRITICAL",
                                category="Hindsight Bias",
                                description=f"Potential future data leakage: {line.strip()}",
                                file_path=str(file_path.relative_to(submission_path)),
                                line_number=i,
                                code_snippet=line.strip(),
                                recommendation="Ensure strategy only uses historical data available at decision time"
                            ))

            except Exception:
                continue

        return detected

    def _check_timestamp_manipulation(self, submission_path: Path, issues: List[DataIntegrityIssue]) -> bool:
        """Check for suspicious timestamp manipulation."""
        detected = False

        strategy_files = list(submission_path.rglob("*.py"))

        for file_path in strategy_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')

                for i, line in enumerate(lines, 1):
                    for pattern in self.timestamp_patterns:
                        if re.search(pattern, line):
                            detected = True
                            issues.append(DataIntegrityIssue(
                                severity="HIGH",
                                category="Timestamp Manipulation",
                                description=f"Suspicious timestamp pattern: {line.strip()}",
                                file_path=str(file_path.relative_to(submission_path)),
                                line_number=i,
                                code_snippet=line.strip(),
                                recommendation="Use authentic timestamps from market data"
                            ))

            except Exception:
                continue

        return detected

    def _check_unrealistic_data_patterns(self, submission_path: Path, issues: List[DataIntegrityIssue]) -> bool:
        """Check for unrealistic data patterns in backtest results."""
        detected = False

        # Look for CSV files with trading data
        csv_files = list(submission_path.rglob("*.csv"))

        for file_path in csv_files:
            try:
                df = pd.read_csv(file_path)

                # Check for unrealistic price changes
                if 'close' in df.columns or 'Close' in df.columns:
                    price_col = 'Close' if 'Close' in df.columns else 'close'
                    if len(df) > 1:
                        price_changes = df[price_col].pct_change().abs() * 100
                        extreme_changes = price_changes > self.unrealistic_thresholds['price_change_percent']

                        if extreme_changes.any():
                            detected = True
                            max_change = price_changes.max()
                            issues.append(DataIntegrityIssue(
                                severity="MEDIUM",
                                category="Unrealistic Data",
                                description=f"Extreme price change detected: {max_change:.1f}%",
                                file_path=str(file_path.relative_to(submission_path)),
                                recommendation="Verify data authenticity; extreme price changes may indicate manipulation"
                            ))

                # Check for unrealistic volume patterns
                if 'volume' in df.columns or 'Volume' in df.columns:
                    volume_col = 'Volume' if 'Volume' in df.columns else 'volume'
                    if len(df) > 10:
                        median_volume = df[volume_col].median()
                        volume_spikes = df[volume_col] > median_volume * self.unrealistic_thresholds['volume_spike_ratio']

                        if volume_spikes.any():
                            detected = True
                            max_spike = (df[volume_col] / median_volume).max()
                            issues.append(DataIntegrityIssue(
                                severity="MEDIUM",
                                category="Unrealistic Data",
                                description=f"Extreme volume spike detected: {max_spike:.0f}x median",
                                file_path=str(file_path.relative_to(submission_path)),
                                recommendation="Verify volume data authenticity"
                            ))

            except Exception:
                continue

        return detected

    def _check_non_market_hours_trading(self, submission_path: Path, issues: List[DataIntegrityIssue]) -> bool:
        """Check for trading outside market hours."""
        detected = False

        # Look for trading logs or timestamp data
        log_files = list(submission_path.rglob("*.log")) + list(submission_path.rglob("*.csv"))

        for file_path in log_files:
            try:
                content = file_path.read_text(encoding='utf-8')

                # Look for timestamp patterns outside market hours
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    # Match timestamps like 2024-01-01 22:30:00 or similar
                    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}\s+(\d{2}):(\d{2}):(\d{2}))', line)
                    if timestamp_match:
                        hour = int(timestamp_match.group(2))
                        minute = int(timestamp_match.group(3))
                        trade_time = time(hour, minute)

                        # Check if outside market hours
                        if trade_time < self.market_open or trade_time > self.market_close:
                            detected = True
                            issues.append(DataIntegrityIssue(
                                severity="MEDIUM",
                                category="Non-Market Hours Trading",
                                description=f"Trading activity outside market hours: {timestamp_match.group(1)}",
                                file_path=str(file_path.relative_to(submission_path)),
                                line_number=i,
                                code_snippet=line.strip()[:100],
                                recommendation="Ensure trading only occurs during market hours (9:30 AM - 4:00 PM EST)"
                            ))
                            break  # Don't spam with multiple instances from same file

            except Exception:
                continue

        return detected

    def _check_yfinance_authenticity(self, submission_path: Path, issues: List[DataIntegrityIssue]) -> bool:
        """Check if yfinance is used properly - only in data loading files."""
        detected = False

        # Only check specific data loading files, not strategy files (framework handles data)
        data_files = [
            submission_path / "reports" / "backtest_runner.py",
            submission_path / "reports" / "data_loader.py"
        ]

        for file_path in data_files:
            if not file_path.exists():
                continue

            try:
                content = file_path.read_text(encoding='utf-8')

                # Only flag if this file claims to load data but has no legitimate source
                if ('download' in content.lower() or 'fetch' in content.lower()) and \
                   'yfinance' not in content and 'yf' not in content:
                    detected = True
                    issues.append(DataIntegrityIssue(
                        severity="LOW",  # Reduced severity - informational only
                        category="Data Source Info",
                        description="Custom data loading without clear yfinance reference",
                        file_path=str(file_path.relative_to(submission_path)),
                        recommendation="Consider using yfinance for market data authenticity"
                    ))

            except Exception:
                continue

        return detected

    def _check_suspicious_performance_patterns(self, submission_path: Path, issues: List[DataIntegrityIssue]) -> bool:
        """Check for patterns indicating artificially good performance."""
        detected = False

        # Look in reports for suspicious patterns
        report_files = list(submission_path.rglob("*.md")) + list(submission_path.rglob("*.txt"))

        for file_path in report_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')

                for i, line in enumerate(lines, 1):
                    line_lower = line.lower()

                    # Only extremely unrealistic performance claims (truly impossible numbers)
                    suspicious_patterns = [
                        r'100%.*win.*rate',                    # 100% win rate
                        r'0%.*loss.*rate',                     # 0% loss rate
                        r'[5-9]\d\d%.*return',                # 500%+ returns
                        r'100%.*accuracy',                     # 100% accuracy
                        r'drawdown.*0%',                       # Zero drawdown
                        r'sharpe.*[1-9]\d\d',                 # Sharpe ratio >100
                        r'profit.*factor.*[1-9]\d\d',         # Profit factor >100
                        r'never.*lose',                        # Never lose claims
                        r'perfect.*strategy',                  # Perfect strategy claims
                        r'infinite.*profit',                   # Infinite profit
                        r'zero.*risk',                         # Zero risk claims
                    ]

                    for pattern in suspicious_patterns:
                        if re.search(pattern, line_lower):
                            detected = True
                            issues.append(DataIntegrityIssue(
                                severity="MEDIUM",
                                category="Suspicious Performance",
                                description=f"Unrealistic performance claim: {line.strip()}",
                                file_path=str(file_path.relative_to(submission_path)),
                                line_number=i,
                                code_snippet=line.strip(),
                                recommendation="Verify performance claims with authentic market data"
                            ))

            except Exception:
                continue

        return detected

    def _calculate_integrity_score(self, issues: List[DataIntegrityIssue]) -> float:
        """Calculate integrity score based on issues found."""
        score = 100.0

        for issue in issues:
            if issue.severity == "CRITICAL":
                score -= 30  # Heavy penalty for critical data issues
            elif issue.severity == "HIGH":
                score -= 15
            elif issue.severity == "MEDIUM":
                score -= 8
            elif issue.severity == "LOW":
                score -= 3

        return max(0.0, score)

    def _extract_participant_name(self, submission_path: Path) -> str:
        """Extract participant name from submission path."""
        import re
        folder_name = submission_path.name
        match = re.search(r'#\d+\s*\(([^)]+)\)', folder_name)
        if match:
            return match.group(1).strip()
        return "Unknown"

def main():
    parser = argparse.ArgumentParser(description="Contest Data Integrity Checker")
    parser.add_argument("--base-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--submissions", type=str, required=True, help="Comma-separated submission IDs")

    args = parser.parse_args()

    checker = DataIntegrityChecker()
    results = []

    submission_ids = [s.strip() for s in args.submissions.split(',')]

    print(f"DATA INTEGRITY CHECK: {len(submission_ids)} submissions")
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
    with open(args.output_dir / "data_integrity_results.json", 'w') as f:
        json.dump(results, f, indent=2)

    # Summary
    passed_count = sum(1 for r in results if r['passed'])
    print()
    print("=" * 60)
    print(f"DATA INTEGRITY SUMMARY: {passed_count}/{len(results)} PASSED")
    print("=" * 60)

    if passed_count < len(results):
        print("\nFAILED SUBMISSIONS:")
        for r in results:
            if not r['passed']:
                critical_issues = sum(1 for issue in r['issues'] if issue['severity'] == 'CRITICAL')
                print(f"  - {r['submission_id']}: {critical_issues} CRITICAL data issues")

if __name__ == "__main__":
    main()