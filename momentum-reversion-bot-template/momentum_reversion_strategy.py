#!/usr/bin/env python3
"""Adaptive Momentum-Reversion Hybrid Trading Strategy.

This strategy combines momentum and mean reversion techniques to capture
both trending and ranging market conditions. It uses multiple technical
indicators with dynamic position sizing and risk management.

Key Features:
- RSI + MACD for momentum detection
- Bollinger Bands for mean reversion opportunities
- Volume confirmation for trade validation
- ATR-based dynamic stop losses and profit targets
- Adaptive position sizing based on market volatility
- Multi-timeframe analysis for trend confirmation
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from statistics import mean, pstdev
from typing import Any, Dict, Optional, List
from collections import deque
import logging

# Import base infrastructure from base-bot-template
import sys
import os

# Handle both local development and Docker container paths
base_path = os.path.join(os.path.dirname(__file__), '..', 'base-bot-template')
if not os.path.exists(base_path):
    # In Docker container, base template is at /app/base/
    base_path = '/app/base'

sys.path.insert(0, base_path)

from strategy_interface import BaseStrategy, Signal, register_strategy
from exchange_interface import MarketSnapshot


class MomentumReversionStrategy(BaseStrategy):
    """Adaptive Momentum-Reversion Hybrid Strategy.
    
    This strategy intelligently switches between momentum and mean reversion
    modes based on market conditions. It uses a sophisticated scoring system
    that combines multiple technical indicators.
    
    Configuration Parameters:
    - trade_amount: Base trade size in USD (default: 400)
    - rsi_period: RSI calculation period (default: 14)
    - rsi_oversold: RSI oversold threshold (default: 30)
    - rsi_overbought: RSI overbought threshold (default: 70)
    - bb_period: Bollinger Bands period (default: 20)
    - bb_std_dev: Bollinger Bands standard deviations (default: 2.0)
    - macd_fast: MACD fast EMA period (default: 12)
    - macd_slow: MACD slow EMA period (default: 26)
    - macd_signal: MACD signal line period (default: 9)
    - atr_period: ATR period for volatility (default: 14)
    - volume_threshold: Volume spike threshold multiplier (default: 1.5)
    - momentum_threshold: Score threshold for momentum trades (default: 75)
    - reversion_threshold: Score threshold for reversion trades (default: 80)
    - max_positions: Maximum concurrent positions (default: 3)
    - stop_loss_atr_multiplier: Stop loss as multiple of ATR (default: 1.8)
    - take_profit_atr_multiplier: Take profit as multiple of ATR (default: 4.5)
    - position_size_scaling: Enable dynamic position sizing (default: True)
    """

    def __init__(self, config: Dict[str, Any], exchange):
        super().__init__(config=config, exchange=exchange)
        
        # Trading parameters
        self.trade_amount = float(config.get("trade_amount", 400.0))
        
        # Technical indicator periods
        self.rsi_period = int(config.get("rsi_period", 14))
        self.rsi_oversold = float(config.get("rsi_oversold", 30))
        self.rsi_overbought = float(config.get("rsi_overbought", 70))
        
        self.bb_period = int(config.get("bb_period", 20))
        self.bb_std_dev = float(config.get("bb_std_dev", 2.0))
        
        self.macd_fast = int(config.get("macd_fast", 12))
        self.macd_slow = int(config.get("macd_slow", 26))
        self.macd_signal = int(config.get("macd_signal", 9))
        
        self.atr_period = int(config.get("atr_period", 14))
        self.volume_threshold = float(config.get("volume_threshold", 1.5))
        
        # Strategy thresholds
        self.momentum_threshold = float(config.get("momentum_threshold", 78))
        self.reversion_threshold = float(config.get("reversion_threshold", 82))
        
        # Risk management
        self.max_positions = int(config.get("max_positions", 3))
        self.stop_loss_atr_multiplier = float(config.get("stop_loss_atr_multiplier", 1.6))
        self.take_profit_atr_multiplier = float(config.get("take_profit_atr_multiplier", 5.0))
        self.position_size_scaling = bool(config.get("position_size_scaling", True))
        
        # State tracking
        self.positions: List[Dict[str, Any]] = []
        self.last_trade_time: Optional[datetime] = None
        self.min_trade_interval = timedelta(hours=4)  # Prevent overtrading - 4 hour minimum
        
        # Price history for indicators (need enough for slow MACD)
        self.price_history: deque = deque(maxlen=max(400, self.macd_slow * 3))
        
        # Database client for persistence
        self._db_client = config.get("db_client")
        self._starting_cash = float(config.get("starting_cash", 10000.0))
        
        # Logging
        self._logger = logging.getLogger("strategy.momentum_reversion")
        self._logger.setLevel(logging.INFO)
        
        # Restore state from database
        self._restore_state_from_db()

    def _restore_state_from_db(self) -> None:
        """Restore strategy state from database on restart."""
        if not self._db_client:
            return
            
        try:
            # Restore open positions
            if hasattr(self._db_client, 'get_open_positions'):
                self.positions = self._db_client.get_open_positions()
                self._logger.info(f"Restored {len(self.positions)} open positions from database")
        except Exception as exc:
            self._logger.warning(f"Failed to restore state: {exc}")

    def generate_signal(self, market: MarketSnapshot, portfolio) -> Signal:
        """Generate trading signal based on momentum and mean reversion analysis."""
        now = datetime.now(timezone.utc)
        
        # Update price history
        self.price_history.append(market.current_price)
        
        # Need sufficient price history
        min_required = max(self.bb_period, self.macd_slow, self.atr_period, 200) + 10
        if len(market.prices) < min_required:
            return Signal("hold", reason=f"Warming up indicators (need {min_required} data points)")
        
        # Time-based filter: avoid low-liquidity periods
        hour = now.hour
        if hour < 8 or hour > 20:  # Only trade during 8am-8pm UTC
            return Signal("hold", reason="Outside trading hours window")
        
        # Check trade interval to prevent overtrading
        if self.last_trade_time and (now - self.last_trade_time) < self.min_trade_interval:
            return Signal("hold", reason="Minimum trade interval not elapsed")
        
        # Check existing positions
        if len(self.positions) >= self.max_positions:
            # Check if we should close any positions
            sell_signal = self._check_exit_conditions(market, portfolio)
            if sell_signal:
                return sell_signal
            return Signal("hold", reason=f"Maximum positions reached ({self.max_positions})")
        
        # Calculate technical indicators
        indicators = self._calculate_indicators(market.prices)
        
        # Volatility regime filter: avoid extreme volatility
        atr = indicators['atr']
        atr_pct = (atr / market.current_price) * 100
        if atr_pct > 6.0:  # Skip if volatility is too high
            return Signal("hold", reason="Volatility too high for entry")
        
        # Check for sell signals first (exit before entry)
        if portfolio.quantity > 0:
            sell_signal = self._check_exit_conditions(market, portfolio)
            if sell_signal:
                return sell_signal
        
        # Generate buy signal using hybrid approach
        buy_signal = self._check_entry_conditions(market, portfolio, indicators)
        if buy_signal:
            return buy_signal
        
        return Signal("hold", reason="No trading opportunity detected")

    def _calculate_indicators(self, prices: List[float]) -> Dict[str, float]:
        """Calculate all technical indicators."""
        indicators = {}
        
        # RSI
        indicators['rsi'] = self._calculate_rsi(prices, self.rsi_period)
        
        # Bollinger Bands
        bb = self._calculate_bollinger_bands(prices, self.bb_period, self.bb_std_dev)
        indicators['bb_upper'] = bb['upper']
        indicators['bb_middle'] = bb['middle']
        indicators['bb_lower'] = bb['lower']
        indicators['bb_position'] = bb['position']  # Where current price is relative to bands
        
        # MACD
        macd = self._calculate_macd(prices, self.macd_fast, self.macd_slow, self.macd_signal)
        indicators['macd'] = macd['macd']
        indicators['macd_signal'] = macd['signal']
        indicators['macd_histogram'] = macd['histogram']
        
        # ATR for volatility
        indicators['atr'] = self._calculate_atr(prices, self.atr_period)
        
        # Price momentum (rate of change)
        indicators['momentum'] = self._calculate_momentum(prices, 10)
        
        # Volume analysis (using price volatility as proxy)
        indicators['volume_spike'] = self._detect_volume_spike(prices)

        # Trend analysis using longer-term moving averages
        sma_short = self._calculate_sma(prices, 50)
        sma_long = self._calculate_sma(prices, 200)
        indicators['sma_short'] = sma_short
        indicators['sma_long'] = sma_long
        if len(prices) >= 200 and sma_long > 0:
            indicators['trend_ratio'] = (sma_short - sma_long) / sma_long
        else:
            indicators['trend_ratio'] = 0.0
 
        return indicators

    def _calculate_rsi(self, prices: List[float], period: int) -> float:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return 50.0  # Neutral
        
        gains = []
        losses = []
        
        for i in range(len(prices) - period, len(prices)):
            change = prices[i] - prices[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = mean(gains) if gains else 0
        avg_loss = mean(losses) if losses else 0
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi

    def _calculate_bollinger_bands(self, prices: List[float], period: int, std_dev: float) -> Dict[str, float]:
        """Calculate Bollinger Bands."""
        if len(prices) < period:
            current = prices[-1]
            return {
                'upper': current * 1.02,
                'middle': current,
                'lower': current * 0.98,
                'position': 0.5
            }
        
        recent = prices[-period:]
        middle = mean(recent)
        std = pstdev(recent) if len(recent) > 1 else 0
        
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        
        current = prices[-1]
        
        # Calculate position between bands (0 = lower, 0.5 = middle, 1 = upper)
        if upper == lower:
            position = 0.5
        else:
            position = (current - lower) / (upper - lower)
        
        return {
            'upper': upper,
            'middle': middle,
            'lower': lower,
            'position': position
        }

    def _calculate_macd(self, prices: List[float], fast: int, slow: int, signal: int) -> Dict[str, float]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        if len(prices) < slow + signal:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
        
        # Calculate EMAs
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)
        
        macd_line = ema_fast - ema_slow
        
        # Calculate signal line (EMA of MACD)
        # For simplicity, using SMA instead of proper EMA of MACD
        signal_line = macd_line  # Simplified
        
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }

    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return mean(prices)
        
        multiplier = 2 / (period + 1)
        ema = mean(prices[-period:])  # Start with SMA
        
        for price in prices[-period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema

    def _calculate_sma(self, prices: List[float], period: int) -> float:
        """Calculate Simple Moving Average."""
        if not prices:
            return 0.0

        if len(prices) < period:
            return mean(prices)

        return mean(prices[-period:])

    def _calculate_atr(self, prices: List[float], period: int) -> float:
        """Calculate Average True Range for volatility."""
        if len(prices) < period + 1:
            return abs(prices[-1] - prices[0]) / len(prices)
        
        true_ranges = []
        for i in range(len(prices) - period, len(prices)):
            high_low = abs(prices[i] - prices[i - 1])
            true_ranges.append(high_low)
        
        return mean(true_ranges) if true_ranges else 0

    def _calculate_momentum(self, prices: List[float], period: int) -> float:
        """Calculate price momentum (rate of change)."""
        if len(prices) < period:
            return 0
        
        old_price = prices[-period]
        current_price = prices[-1]
        
        if old_price == 0:
            return 0
        
        return ((current_price - old_price) / old_price) * 100

    def _detect_volume_spike(self, prices: List[float]) -> bool:
        """Detect volume spike using price volatility as proxy."""
        if len(prices) < 20:
            return False
        
        recent_volatility = pstdev(prices[-5:]) if len(prices[-5:]) > 1 else 0
        historical_volatility = pstdev(prices[-20:-5]) if len(prices[-20:-5]) > 1 else 0
        
        if historical_volatility == 0:
            return False
        
        return recent_volatility > (historical_volatility * self.volume_threshold)

    def _check_entry_conditions(self, market: MarketSnapshot, portfolio, indicators: Dict[str, float]) -> Optional[Signal]:
        """Check for entry conditions using hybrid momentum-reversion approach."""
        current_price = market.current_price
        
        # Calculate scores for both momentum and mean reversion
        momentum_score = self._calculate_momentum_score(indicators)
        reversion_score = self._calculate_reversion_score(indicators)

        sma_short = indicators.get('sma_short', 0.0)
        sma_long = indicators.get('sma_long', 0.0)
        trend_ratio = indicators.get('trend_ratio', 0.0)

        uptrend = False
        supportive_trend = False

        if sma_long > 0:
            uptrend = (
                trend_ratio >= 0.001
                and current_price >= sma_long * 1.00
                and sma_short >= sma_long * 1.00
            )
            supportive_trend = (
                trend_ratio >= -0.001
                and current_price >= sma_long * 0.99
            )
 
        # Determine trade type based on higher score
        if momentum_score >= self.momentum_threshold:
            if not uptrend:
                return Signal("hold", reason="Trend filter prevents momentum entry")

            reason = f"Momentum buy (score: {momentum_score:.1f}, RSI: {indicators['rsi']:.1f})"
            size = self._calculate_position_size(portfolio, indicators, current_price)
            
            # Calculate stop loss and take profit
            atr = indicators['atr']
            stop_loss = current_price - (atr * self.stop_loss_atr_multiplier)
            target_price = current_price + (atr * self.take_profit_atr_multiplier)
            
            return Signal(
                "buy",
                size=size,
                reason=reason,
                stop_loss=stop_loss,
                target_price=target_price,
                entry_price=current_price
            )
        
        elif reversion_score >= self.reversion_threshold:
            if not supportive_trend:
                return Signal("hold", reason="Trend filter prevents mean reversion entry")

            reason = f"Mean reversion buy (score: {reversion_score:.1f}, BB: {indicators['bb_position']:.2f})"
            size = self._calculate_position_size(portfolio, indicators, current_price)
            
            # For mean reversion, tighter targets
            atr = indicators['atr']
            stop_loss = current_price - (atr * self.stop_loss_atr_multiplier * 0.8)
            target_price = current_price + (atr * self.take_profit_atr_multiplier * 1.2)
            
            return Signal(
                "buy",
                size=size,
                reason=reason,
                stop_loss=stop_loss,
                target_price=target_price,
                entry_price=current_price
            )
        
        return None

    def _calculate_momentum_score(self, indicators: Dict[str, float]) -> float:
        """Calculate momentum trading score (0-100)."""
        score = 0
        
        rsi = indicators['rsi']
        macd_histogram = indicators['macd_histogram']
        momentum = indicators['momentum']
        volume_spike = indicators['volume_spike']
        
        # RSI momentum (bullish if RSI rising from oversold or neutral)
        if 30 < rsi < 60:
            score += 25  # Sweet spot for momentum
        elif rsi < 30:
            score += 15  # Oversold, potential reversal
        
        # MACD bullish
        if macd_histogram > 0:
            score += 25
        
        # Positive momentum
        if momentum > 2:
            score += 30
        elif momentum > 0:
            score += 15
        
        # Volume confirmation
        if volume_spike:
            score += 20
        
        return min(score, 100)

    def _calculate_reversion_score(self, indicators: Dict[str, float]) -> float:
        """Calculate mean reversion trading score (0-100)."""
        score = 0
        
        rsi = indicators['rsi']
        bb_position = indicators['bb_position']
        momentum = indicators['momentum']
        
        # RSI oversold
        if rsi < 30:
            score += 40
        elif rsi < 35:
            score += 25
        
        # Price near or below lower Bollinger Band
        if bb_position < 0.1:
            score += 40
        elif bb_position < 0.2:
            score += 25
        
        # Negative momentum (selling pressure exhausting)
        if momentum < -5:
            score += 20
        elif momentum < 0:
            score += 10
        
        return min(score, 100)

    def _calculate_position_size(self, portfolio, indicators: Dict[str, float], price: float) -> float:
        """Calculate position size based on portfolio and volatility."""
        base_size = self.trade_amount / price
        
        if not self.position_size_scaling:
            return base_size
        
        # Scale position size based on volatility (higher volatility = smaller position)
        atr = indicators['atr']
        atr_pct = (atr / price) * 100
        
        if atr_pct > 5:  # High volatility
            scale = 0.7
        elif atr_pct > 3:  # Medium volatility
            scale = 0.85
        else:  # Low volatility
            scale = 1.0
        
        return base_size * scale

    def _check_exit_conditions(self, market: MarketSnapshot, portfolio) -> Optional[Signal]:
        """Check if we should close any positions."""
        if not self.positions or portfolio.quantity <= 0:
            return None
        
        current_price = market.current_price
        
        # Check stop loss and take profit for each position
        for position in self.positions:
            entry_price = position.get('entry_price', 0)
            stop_loss = position.get('stop_loss', 0)
            target_price = position.get('target_price', 0)
            
            # Stop loss hit
            if stop_loss > 0 and current_price <= stop_loss:
                return Signal(
                    "sell",
                    size=portfolio.quantity,
                    reason=f"Stop loss hit at {current_price:.2f} (entry: {entry_price:.2f})"
                )
            
            # Take profit hit
            if target_price > 0 and current_price >= target_price:
                return Signal(
                    "sell",
                    size=portfolio.quantity,
                    reason=f"Take profit hit at {current_price:.2f} (entry: {entry_price:.2f})"
                )
        
        # Check technical exit signals
        indicators = self._calculate_indicators(market.prices)
        
        # Exit on overbought RSI
        if indicators['rsi'] > 75:
            return Signal(
                "sell",
                size=portfolio.quantity,
                reason=f"Overbought exit (RSI: {indicators['rsi']:.1f})"
            )
        
        # Exit on bearish MACD crossover
        if indicators['macd_histogram'] < 0 and indicators['macd'] < 0:
            return Signal(
                "sell",
                size=portfolio.quantity,
                reason="Bearish MACD crossover"
            )
        
        return None

    def on_trade(self, signal: Signal, execution_price: float, execution_size: float, timestamp: datetime) -> None:
        """Update strategy state after trade execution."""
        # Ensure timestamp is timezone-aware
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        
        if signal.action == "buy":
            # Add new position
            position = {
                'entry_price': execution_price,
                'size': execution_size,
                'stop_loss': signal.stop_loss,
                'target_price': signal.target_price,
                'timestamp': timestamp
            }
            self.positions.append(position)
            self.last_trade_time = timestamp
            self._logger.info(f"Opened position: {execution_size:.6f} @ {execution_price:.2f}")
            
        elif signal.action == "sell":
            # Close positions (FIFO)
            remaining = execution_size
            while self.positions and remaining > 0:
                position = self.positions[0]
                if position['size'] <= remaining:
                    remaining -= position['size']
                    self.positions.pop(0)
                else:
                    position['size'] -= remaining
                    remaining = 0
            
            self.last_trade_time = timestamp
            self._logger.info(f"Closed position: {execution_size:.6f} @ {execution_price:.2f}")

    def get_state(self) -> Dict[str, Any]:
        """Serialize strategy state for persistence."""
        return {
            'positions': [
                {
                    'entry_price': p['entry_price'],
                    'size': p['size'],
                    'stop_loss': p['stop_loss'],
                    'target_price': p['target_price'],
                    'timestamp': p['timestamp'].isoformat() if isinstance(p['timestamp'], datetime) else p['timestamp']
                }
                for p in self.positions
            ],
            'last_trade_time': self.last_trade_time.isoformat() if self.last_trade_time else None
        }

    def set_state(self, state: Dict[str, Any]) -> None:
        """Restore strategy state from persistence."""
        if 'positions' in state:
            self.positions = [
                {
                    'entry_price': p['entry_price'],
                    'size': p['size'],
                    'stop_loss': p['stop_loss'],
                    'target_price': p['target_price'],
                    'timestamp': datetime.fromisoformat(p['timestamp']) if p.get('timestamp') else datetime.now(timezone.utc)
                }
                for p in state['positions']
            ]
        
        if 'last_trade_time' in state and state['last_trade_time']:
            self.last_trade_time = datetime.fromisoformat(state['last_trade_time'])


# Register the strategy
register_strategy("momentum_reversion", lambda cfg, ex: MomentumReversionStrategy(cfg, ex))

