# Momentum-Reversion Hybrid Trading Strategy

## Overview

This is an **Adaptive Momentum-Reversion Hybrid Strategy** designed for cryptocurrency trading. The strategy intelligently combines momentum and mean reversion techniques to identify high-probability trading opportunities in both trending and ranging markets.

## Strategy Logic

### Core Concept

The strategy operates in two complementary modes:

1. **Momentum Mode**: Captures strong price trends using RSI and MACD indicators
2. **Mean Reversion Mode**: Exploits oversold conditions using Bollinger Bands and RSI

### Technical Indicators

- **RSI (Relative Strength Index)** - Period: 14
  - Identifies momentum and overbought/oversold conditions
  - Oversold threshold: 25, Overbought threshold: 75

- **Bollinger Bands** - Period: 20, Std Dev: 2.0
  - Detects mean reversion opportunities
  - Signals extreme price deviations from moving average

- **MACD (Moving Average Convergence Divergence)** - Fast: 12, Slow: 26, Signal: 9
  - Confirms trend direction and momentum
  - Histogram used for entry timing

- **ATR (Average True Range)** - Period: 14
  - Measures market volatility
  - Used for dynamic stop-loss and take-profit placement

- **Price Momentum** - Period: 10
  - Calculates rate of change
  - Confirms trend strength

- **Volume Analysis**
  - Detects volume spikes (1.8x threshold)
  - Confirms trade validity

### Entry Logic

#### Momentum Entry (Threshold: 70 points)

The strategy calculates a momentum score (0-100) based on:
- RSI in momentum zone (30-60): **+25 points**
- Positive MACD histogram: **+25 points**
- Strong positive momentum (>2%): **+30 points**
- Volume spike detected: **+20 points**

**Entry Trigger**: Score ≥ 70

#### Mean Reversion Entry (Threshold: 75 points)

The strategy calculates a reversion score (0-100) based on:
- RSI oversold (<25): **+40 points**
- Price near lower Bollinger Band (<10%): **+40 points**
- Negative momentum (<-5%): **+20 points**

**Entry Trigger**: Score ≥ 75

### Exit Logic

Multiple exit mechanisms protect profits and limit losses:

1. **Stop Loss**: Entry price - (1.5 × ATR)
   - Hard stop to prevent large losses
   - Dynamically adjusted based on volatility

2. **Take Profit**: Entry price + (4.0 × ATR)
   - Target profit level
   - Risk-reward ratio of ~2.67:1

3. **Technical Exits**:
   - RSI overbought (>75): Exit to lock profits
   - Bearish MACD crossover: Exit on trend reversal

### Risk Management

- **Maximum Positions**: 2 concurrent positions
- **Position Sizing**: $800 base size, volatility-adjusted
- **Trade Interval**: Minimum 2 hours between trades
- **Volatility Scaling**:
  - High volatility (ATR >5%): 70% position size
  - Medium volatility (ATR 3-5%): 85% position size
  - Low volatility (ATR <3%): 100% position size

## Configuration Parameters

### Trading Parameters

```json
{
  "trade_amount": 800.0,           // Base trade size in USD
  "max_positions": 2,              // Maximum concurrent positions
  "position_size_scaling": true    // Enable volatility-based sizing
}
```

### Technical Indicator Settings

```json
{
  "rsi_period": 14,
  "rsi_oversold": 25,              // More selective than default 30
  "rsi_overbought": 75,            // More selective than default 70
  "bb_period": 20,
  "bb_std_dev": 2.0,
  "macd_fast": 12,
  "macd_slow": 26,
  "macd_signal": 9,
  "atr_period": 14
}
```

### Strategy Thresholds

```json
{
  "momentum_threshold": 70,        // Minimum score for momentum trades
  "reversion_threshold": 75,       // Minimum score for reversion trades
  "volume_threshold": 1.8          // Volume spike multiplier
}
```

### Risk Management Settings

```json
{
  "stop_loss_atr_multiplier": 1.5,     // Stop loss distance
  "take_profit_atr_multiplier": 4.0    // Take profit distance
}
```

## How to Use

### Local Development

```bash
# Run with default settings
python startup.py

# Run with custom symbol
BOT_SYMBOL=ETH-USD python startup.py

# Run with custom configuration
BOT_STARTING_CASH=10000 \
TRADE_AMOUNT=800 \
python startup.py
```

### Docker Deployment

```bash
# Build the container (from repository root)
docker build -f momentum-reversion-bot-template/Dockerfile \
  -t momentum-reversion-bot .

# Run the container
docker run -p 8080:8080 -p 3010:3010 \
  -e BOT_STRATEGY=momentum_reversion \
  -e BOT_SYMBOL=BTC-USD \
  -e BOT_STARTING_CASH=10000 \
  -e TRADE_AMOUNT=800 \
  momentum-reversion-bot
```

### Environment Variables

```bash
# Core Configuration
BOT_EXCHANGE=paper                # Exchange (paper for testing)
BOT_STRATEGY=momentum_reversion   # Strategy name
BOT_SYMBOL=BTC-USD               # Trading pair
BOT_STARTING_CASH=10000          # Starting capital
BOT_SLEEP=300                    # Sleep between cycles (seconds)

# Strategy Parameters
TRADE_AMOUNT=800                 # Base trade size
RSI_PERIOD=14
RSI_OVERSOLD=25
RSI_OVERBOUGHT=75
MOMENTUM_THRESHOLD=70
REVERSION_THRESHOLD=75
MAX_POSITIONS=2
STOP_LOSS_ATR_MULTIPLIER=1.5
TAKE_PROFIT_ATR_MULTIPLIER=4.0

# Optional: Dashboard Integration
BOT_INSTANCE_ID=your-bot-id
USER_ID=your-user-id
BOT_SECRET=your-secret
BASE_URL=https://your-dashboard.com
POSTGRES_URL=postgresql://...
```

## Strategy Strengths

1. **Market Adaptability**: Works in both trending and ranging markets
2. **Risk Control**: Multiple stop-loss mechanisms protect capital
3. **High Signal Quality**: Strict thresholds reduce false signals
4. **Volatility Awareness**: Position sizing adapts to market conditions
5. **Proven Indicators**: Uses time-tested technical analysis tools
6. **No Overfitting**: Robust parameters, not curve-fitted to specific data

## Expected Performance

### Ideal Market Conditions
- **Medium Volatility**: Best performance in moderately volatile markets
- **Clear Trends**: Momentum mode captures strong directional moves
- **Oversold Bounces**: Mean reversion mode profits from recoveries

### Performance Characteristics
- **Win Rate Target**: 55-65%
- **Risk-Reward Ratio**: ~2.67:1 (based on ATR multipliers)
- **Trade Frequency**: 15-30 trades per month
- **Maximum Drawdown Target**: <25%

## Dependencies

- Python 3.11+
- requests>=2.31
- psycopg2-binary>=2.9 (for database integration)

All technical indicators implemented using Python's built-in `statistics` module - no external dependencies required.

## API Endpoints

### Health Check (Port 8080)
- `GET /health` - Bot status and strategy info

### Control API (Port 3010)
- `GET /performance` - Real-time performance metrics
- `GET /settings` - Current configuration
- `POST /settings` - Update configuration (hot reload)
- `POST /commands` - Bot control (start/stop/pause/resume)
- `GET /logs` - Recent trading logs

## Files

- `momentum_reversion_strategy.py` - Main strategy implementation
- `startup.py` - Bot entry point
- `Dockerfile` - Container configuration
- `requirements.txt` - Python dependencies
- `README.md` - This documentation

## Support

For questions or issues:
1. Check the strategy code comments in `momentum_reversion_strategy.py`
2. Review the configuration parameters above
3. Verify environment variables are set correctly
4. Check logs via `/logs` endpoint or container logs

## License

This strategy is part of the Trading Strategy Contest submission.

