# Momentum-Reversion Bot Template - Dockerfile
FROM python:3.11-slim

LABEL description="Momentum-Reversion Trading Bot - Adaptive Hybrid Strategy"
LABEL strategy="momentum_reversion"
LABEL tier="contest"
LABEL contest="trading-strategy-2024"

# Set working directory
WORKDIR /app

# Copy base bot infrastructure
COPY base-bot-template/ /app/base/

# Copy Momentum-Reversion specific files
COPY momentum-reversion-bot-template/ /app/

# Install dependencies
RUN pip install --no-cache-dir -r /app/base/requirements.txt

# Make startup script executable
RUN chmod +x /app/startup.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Expose ports
EXPOSE 8080 3010

# Default environment variables
ENV BOT_EXCHANGE=paper
ENV BOT_STRATEGY=momentum_reversion
ENV BOT_SYMBOL=BTC-USD
ENV BOT_STARTING_CASH=10000.0
ENV BOT_SLEEP=300

# Strategy-specific defaults
ENV TRADE_AMOUNT=500.0
ENV RSI_PERIOD=14
ENV RSI_OVERSOLD=30
ENV RSI_OVERBOUGHT=70
ENV BB_PERIOD=20
ENV BB_STD_DEV=2.0
ENV MACD_FAST=12
ENV MACD_SLOW=26
ENV MACD_SIGNAL=9
ENV ATR_PERIOD=14
ENV VOLUME_THRESHOLD=1.5
ENV MOMENTUM_THRESHOLD=60
ENV REVERSION_THRESHOLD=70
ENV MAX_POSITIONS=3
ENV STOP_LOSS_ATR_MULTIPLIER=2.0
ENV TAKE_PROFIT_ATR_MULTIPLIER=3.0
ENV POSITION_SIZE_SCALING=true

# Start the Momentum-Reversion bot
CMD ["python", "/app/startup.py"]

