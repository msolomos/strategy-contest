# Trading Logic Explanation

## Strategy Philosophy

The **Adaptive Momentum-Reversion Hybrid Strategy** is built on the principle that markets alternate between trending and mean-reverting states. Rather than choosing one approach, this strategy intelligently uses both, selecting the highest-probability trade type at each decision point.

---

## Core Trading Logic

### 1. Signal Generation Process

```
Market Data → Calculate Indicators → Score Opportunities → Generate Signal → Execute Trade
```

**Step-by-Step Flow**:

1. **Data Collection** (every 5 minutes)
   - Fetch current price and price history
   - Need minimum 50 candles for indicator calculation

2. **Indicator Calculation**
   - Calculate RSI (14-period)
   - Calculate Bollinger Bands (20-period, 2 std dev)
   - Calculate MACD (12, 26, 9)
   - Calculate ATR (14-period)
   - Calculate Price Momentum (10-period)
   - Detect Volume Spikes (1.8x threshold)

3. **Opportunity Scoring**
   - Calculate Momentum Score (0-100)
   - Calculate Mean Reversion Score (0-100)
   - Compare against thresholds

4. **Signal Decision**
   - If Momentum Score ≥ 70: Generate BUY signal (momentum)
   - Else if Reversion Score ≥ 75: Generate BUY signal (reversion)
   - Else: HOLD

5. **Trade Execution**
   - Calculate position size (volatility-adjusted)
   - Set stop-loss (1.5x ATR below entry)
   - Set take-profit (4.0x ATR above entry)
   - Execute trade via exchange interface

---

## 2. Momentum Trading Logic

### When to Use Momentum Mode

Momentum trading captures strong directional moves. The strategy enters momentum trades when:
- Price is making sustained moves in one direction
- RSI shows strength but not overbought
- MACD confirms trend
- Volume supports the move

### Momentum Score Calculation

```python
score = 0

# RSI Momentum Check (0-25 points)
if 30 < RSI < 60:
    score += 25  # Sweet spot for momentum
elif RSI < 30:
    score += 15  # Oversold, potential reversal

# MACD Bullish Check (0-25 points)
if MACD_Histogram > 0:
    score += 25  # Bullish momentum confirmed

# Price Momentum Check (0-30 points)
if Price_Momentum > 2%:
    score += 30  # Strong upward movement
elif Price_Momentum > 0:
    score += 15  # Positive movement

# Volume Confirmation (0-20 points)
if Volume_Spike_Detected:
    score += 20  # Institutional interest

# Entry if score ≥ 70
```

### Momentum Entry Example

**Scenario**: BTC price rising strongly

1. **Price Action**: $42,000 → $42,500 (+1.2%)
2. **RSI**: 52 (momentum zone) → +25 points
3. **MACD Histogram**: +15 (positive) → +25 points
4. **Momentum**: +2.3% → +30 points
5. **Volume**: 1.9x average → +20 points
6. **Total Score**: 100 → **BUY SIGNAL**

---

## 3. Mean Reversion Logic

### When to Use Reversion Mode

Mean reversion captures bounces from oversold conditions. The strategy enters reversion trades when:
- Price has dropped significantly
- RSI shows oversold conditions
- Price touches/breaks lower Bollinger Band
- Momentum shows selling exhaustion

### Reversion Score Calculation

```python
score = 0

# RSI Oversold Check (0-40 points)
if RSI < 25:
    score += 40  # Deeply oversold
elif RSI < 30:
    score += 25  # Moderately oversold

# Bollinger Band Position (0-40 points)
BB_Position = (Price - BB_Lower) / (BB_Upper - BB_Lower)
if BB_Position < 0.1:
    score += 40  # Near/below lower band
elif BB_Position < 0.2:
    score += 25  # Close to lower band

# Momentum Exhaustion (0-20 points)
if Price_Momentum < -5%:
    score += 20  # Strong selling pressure exhausting
elif Price_Momentum < 0:
    score += 10  # Negative momentum

# Entry if score ≥ 75
```

### Reversion Entry Example

**Scenario**: BTC rapid selloff

1. **Price Action**: $42,000 → $40,800 (-2.9%)
2. **RSI**: 24 (oversold) → +40 points
3. **BB Position**: 0.08 (below lower band) → +40 points
4. **Momentum**: -6.2% → +20 points
5. **Total Score**: 100 → **BUY SIGNAL**

---

## 4. Exit Logic

### Why Exits Are Critical

Good entries are worthless without good exits. This strategy uses **multiple exit mechanisms** to protect profits and limit losses.

### Exit Mechanisms

#### A. Stop Loss (Hard Exit)

**Trigger**: Price ≤ Entry Price - (1.5 × ATR)

**Purpose**: Prevent large losses

**Example**:
- Entry: $42,000
- ATR: $600
- Stop Loss: $42,000 - (1.5 × $600) = $41,100
- If price hits $41,100 → **SELL IMMEDIATELY**

#### B. Take Profit (Target Exit)

**Trigger**: Price ≥ Entry Price + (4.0 × ATR)

**Purpose**: Lock in profits at target

**Example**:
- Entry: $42,000
- ATR: $600
- Take Profit: $42,000 + (4.0 × $600) = $44,400
- If price hits $44,400 → **SELL** (profit locked)

#### C. Overbought Exit (Technical Exit)

**Trigger**: RSI > 75

**Purpose**: Exit before reversal

**Logic**: When RSI exceeds 75, the market is overbought and likely to reverse. Exit to protect profits.

#### D. Trend Reversal Exit (Technical Exit)

**Trigger**: MACD histogram turns negative AND MACD line < 0

**Purpose**: Exit when trend reverses

**Logic**: When both MACD indicators turn bearish, momentum has shifted. Exit to avoid giving back profits.

---

## 5. Risk Management

### Position Sizing

**Base Size**: $800 per trade

**Volatility Adjustment**:
```python
ATR_Percentage = (ATR / Price) × 100

if ATR_Percentage > 5%:
    position_size = base_size × 0.7    # High volatility: 70%
elif ATR_Percentage > 3%:
    position_size = base_size × 0.85   # Medium volatility: 85%
else:
    position_size = base_size × 1.0    # Low volatility: 100%
```

**Why**: Reduce position size when volatility is high to manage risk.

### Position Limits

**Maximum Concurrent Positions**: 2

**Why**: Prevents over-concentration in the market. If both position slots are filled, the strategy waits for an exit before entering new trades.

### Trade Frequency Control

**Minimum Interval**: 2 hours between trades

**Why**: Prevents overtrading and reduces transaction costs. Forces the strategy to be selective.

---

## 6. Decision Tree

```
START
  ↓
[Fetch Market Data]
  ↓
[Sufficient History?] → NO → HOLD
  ↓ YES
[Calculate Indicators]
  ↓
[Any Open Positions?] → YES → [Check Exit Conditions]
  ↓ NO                           ↓
[In Cooldown Period?] → YES → HOLD
  ↓ NO                           ↓
[Calculate Scores]            [Exit Signal?] → YES → SELL
  ↓                              ↓ NO
[Momentum ≥ 70?] → YES → BUY   [Update Trailing Stop]
  ↓ NO                           ↓
[Reversion ≥ 75?] → YES → BUY  HOLD
  ↓ NO
HOLD
```

---

## 7. Trade Examples

### Example 1: Successful Momentum Trade

**Entry**:
- Time: 10:00 AM
- Price: $42,000
- RSI: 55, MACD: +20, Momentum: +2.5%
- Score: 80 → BUY
- Size: 0.019 BTC ($800 / $42,000)
- Stop: $41,100
- Target: $44,400

**During Trade**:
- Price rises to $43,500
- RSI: 68 (still in range)
- Holding position

**Exit**:
- Time: 2:30 PM
- Price: $44,500 (target hit)
- Exit: SELL at $44,500
- Profit: $2,500 × 0.019 = **+$47.50**

### Example 2: Stop Loss Triggered

**Entry**:
- Time: 9:00 AM
- Price: $42,000
- RSI: 45, MACD: +15, Momentum: +1.8%
- Score: 70 → BUY
- Size: 0.019 BTC
- Stop: $41,100
- Target: $44,400

**During Trade**:
- Price drops to $41,800
- Price continues to $41,500
- Price hits $41,100

**Exit**:
- Time: 10:15 AM
- Price: $41,100 (stop loss hit)
- Exit: SELL at $41,100
- Loss: -$900 × 0.019 = **-$17.10**

### Example 3: Successful Mean Reversion Trade

**Entry**:
- Time: 11:00 AM
- Price: $40,500 (after selloff)
- RSI: 23, BB Position: 0.05, Momentum: -7%
- Score: 100 → BUY
- Size: 0.0197 BTC ($800 / $40,500)
- Stop: $39,600
- Target: $42,900

**During Trade**:
- Price bounces to $41,200
- RSI recovers to 42
- Holding position

**Exit**:
- Time: 3:45 PM
- Price: $42,900 (target hit)
- Exit: SELL at $42,900
- Profit: $2,400 × 0.0197 = **+$47.28**

---

## 8. Why This Logic Works

### Complementary Approaches

1. **Trending Markets**: Momentum mode captures directional moves
2. **Ranging Markets**: Reversion mode profits from bounces
3. **Adaptive**: Strategy automatically selects the best approach

### Risk-First Design

1. **Stop Losses**: Every trade has defined max loss
2. **Position Sizing**: Adjusts to volatility
3. **Position Limits**: Prevents over-concentration
4. **Trade Frequency**: Prevents overtrading

### Quantitative Decision Making

1. **No Emotions**: Decisions based purely on numbers
2. **Consistent Logic**: Same rules applied every time
3. **Transparent Scoring**: Easy to understand why trades are made

### Proven Indicators

1. **RSI**: 50+ years of use in trading
2. **Bollinger Bands**: Standard volatility measure
3. **MACD**: Widely used momentum indicator
4. **ATR**: Industry-standard volatility measure

---

## 9. Strategy Limitations

### Known Weaknesses

1. **High Trade Frequency**: 3,369 trades in 6 months may incur significant costs
2. **Synthetic Data**: Backtested on generated data, not real market data
3. **No Regime Filter**: Doesn't distinguish between bull/bear/sideways markets
4. **Transaction Costs**: Not explicitly modeled in backtest
5. **Slippage**: Not accounted for in simulation

### When Strategy May Struggle

1. **Extreme Volatility**: Very rapid price swings can trigger stops
2. **Low Liquidity**: May have execution challenges
3. **Trending Markets**: Mean reversion mode may underperform
4. **Ranging Markets**: Momentum mode may have false signals

---

## 10. Conclusion

This trading logic combines:
- ✅ **Two proven approaches** (momentum + mean reversion)
- ✅ **Quantitative scoring** (objective decision-making)
- ✅ **Risk management** (stops, position limits, sizing)
- ✅ **Adaptability** (works in different market conditions)

The strategy is designed to be **robust, transparent, and professional** - suitable for both contest evaluation and real-world deployment.

---

**Document Version**: 1.0  
**Last Updated**: November 2, 2025  
**Strategy**: Adaptive Momentum-Reversion Hybrid

