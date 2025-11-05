#!/usr/bin/env python3
"""Momentum-Reversion Bot Template - Adaptive Hybrid Trading Bot."""

from __future__ import annotations

import sys
import os

# Import base infrastructure from base-bot-template
# Handle both local development and Docker container paths
base_path = os.path.join(os.path.dirname(__file__), '..', 'base-bot-template')
if not os.path.exists(base_path):
    # In Docker container, base template is at /app/base/
    base_path = '/app/base'

sys.path.insert(0, base_path)

# Import momentum-reversion strategy (this registers the strategy)
import momentum_reversion_strategy  # noqa: F401

# Import base bot infrastructure
from universal_bot import UniversalBot


def main() -> None:
    """Main entry point for Momentum-Reversion Bot."""
    config_path = sys.argv[1] if len(sys.argv) > 1 else None

    bot = UniversalBot(config_path)

    # Print startup info with unique identifiers
    print("=" * 80)
    print("🚀 MOMENTUM-REVERSION TRADING BOT")
    print("=" * 80)
    print(f"🆔 Bot ID: {bot.config.bot_instance_id}")
    print(f"👤 User ID: {bot.config.user_id}")
    print(f"📈 Strategy: {bot.config.strategy}")
    print(f"💰 Symbol: {bot.config.symbol}")
    print(f"🏦 Exchange: {bot.config.exchange}")
    print(f"💵 Starting Capital: ${bot.config.starting_cash:,.2f}")
    print()
    print("🎯 STRATEGY: Adaptive Momentum-Reversion Hybrid")
    print("   - Momentum Detection: RSI + MACD")
    print("   - Mean Reversion: Bollinger Bands")
    print("   - Risk Management: ATR-based stops")
    print("   - Position Sizing: Dynamic volatility adjustment")
    print("=" * 80)
    print()

    bot.run()


if __name__ == "__main__":
    main()

