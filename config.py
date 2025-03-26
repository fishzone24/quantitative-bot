import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# API配置
EXCHANGE = os.getenv("EXCHANGE", "binance")
TRADE_MODE = os.getenv("TRADE_MODE", "test")
MAX_TRADE_SIZE = int(os.getenv("MAX_TRADE_SIZE", 10))

# 风险管理配置
STOP_LOSS = float(os.getenv("STOP_LOSS", 3.0))
TAKE_PROFIT = float(os.getenv("TAKE_PROFIT", 2.0))
USE_DYNAMIC_SL = os.getenv("USE_DYNAMIC_SL", "true").lower() == "true"

# 系统配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DATA_REFRESH_INTERVAL = int(os.getenv("DATA_REFRESH_INTERVAL", 300))  # 数据更新间隔(秒)
SOCIAL_REFRESH_INTERVAL = int(os.getenv("SOCIAL_REFRESH_INTERVAL", 900))  # 社交媒体更新间隔(秒)
TIMEFRAME = os.getenv("TIMEFRAME", "1h")  # 默认时间周期为1小时K线

# 交易对配置
TRADING_PAIRS = [
    "BTC/USDT",
    "ETH/USDT",
    "BNB/USDT",
    "XRP/USDT",
    "SOL/USDT",
]

# 技术分析参数
TA_CONFIG = {
    "RSI": {
        "period": 14,
        "overbought": 70,
        "oversold": 30
    },
    "MACD": {
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9
    },
    "BOLLINGER": {
        "period": 20,
        "std_dev": 2
    },
    "SUPPORT_RESISTANCE": {
        "lookback_periods": [6, 12, 24],  # 小时
        "price_threshold": 1.0  # 价格偏差阈值百分比
    }
}

# 社交媒体分析配置
SOCIAL_CONFIG = {
    # Twitter账号列表
    "twitter_accounts": [
        "binance",
        "cz_binance",
        "BinanceResearch",
        "Bitcoin",
        "crypto"
    ],
    # 重要关键词列表
    "important_keywords": [
        "listing",
        "launch",
        "announcement",
        "partnership",
        "release",
        "upgrade",
        "update",
        "burn",
        "halving"
    ],
    # 情感分析阈值
    "sentiment_threshold": {
        "positive": 0.4,
        "negative": -0.3
    },
    # 模拟模式 - 无法访问Twitter API时自动启用
    "simulation_mode": False
}

# AI决策系统参数
AI_CONFIG = {
    "model": "deepseek-chat",
    "confidence_threshold": 0.7,  # 最小置信度要求
    "context_window": 24,  # 分析的历史数据窗口(小时)
    "enable_predictions": True,
}

# 交易记录配置
TRADE_RECORDS_DIR = "data/trade_records"
TRADE_RECORDS_FILE = f"{TRADE_RECORDS_DIR}/trades.csv"
TRADE_SUMMARY_FILE = f"{TRADE_RECORDS_DIR}/summary.csv"

# 确保数据目录存在
os.makedirs(TRADE_RECORDS_DIR, exist_ok=True) 