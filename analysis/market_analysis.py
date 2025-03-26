import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import os
from typing import Dict, List, Optional, Tuple
from exchanges.exchange_client import ExchangeClient

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('market_analysis')

class MarketAnalyzer:
    """市场分析类"""
    
    def __init__(self, config=None):
        """
        初始化市场分析模块
        
        Args:
            config: 市场分析配置参数
        """
        self.config = config or {}
        self.symbols = self.config.get("symbols", ["BTC/USDT"])
        self.timeframes = self.config.get("timeframes", ["1h"])
        self.indicators = self.config.get("indicators", ["RSI", "MACD", "BB"])
        
        # 初始化交易所客户端
        self.exchange_name = os.getenv("EXCHANGE", "binance")
        self.exchange = ExchangeClient(self.exchange_name)
        
        logger.info("初始化市场分析模块")
    
    def analyze_market(self, symbol: str, timeframe: str = "1h") -> Dict:
        """
        分析市场
        
        Args:
            symbol: 交易对名称
            timeframe: 时间周期
            
        Returns:
            Dict: 分析结果
        """
        try:
            # 获取K线数据
            klines = self.exchange.get_klines(symbol, timeframe)
            if klines.empty:
                logger.error(f"获取{symbol} K线数据失败")
                return {}
            
            # 计算技术指标
            indicators = self._calculate_indicators(klines)
            
            # 生成交易信号
            signals = self._generate_signals(indicators)
            
            # 获取当前价格
            current_price = self.exchange.get_symbol_price(symbol)
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "current_price": current_price,
                "indicators": indicators,
                "signals": signals,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"分析{symbol}市场失败: {str(e)}")
            return {}
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """
        计算技术指标
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            Dict: 技术指标数据
        """
        indicators = {}
        
        # 计算RSI
        if "RSI" in self.indicators:
            indicators["RSI"] = self._calculate_rsi(df)
        
        # 计算MACD
        if "MACD" in self.indicators:
            indicators["MACD"] = self._calculate_macd(df)
        
        # 计算布林带
        if "BB" in self.indicators:
            indicators["BB"] = self._calculate_bollinger_bands(df)
        
        return indicators
    
    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> Dict:
        """计算RSI指标"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return {
            "rsi": rsi.iloc[-1],
            "is_overbought": rsi.iloc[-1] > 70,
            "is_oversold": rsi.iloc[-1] < 30
        }
    
    def _calculate_macd(self, df: pd.DataFrame) -> Dict:
        """计算MACD指标"""
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        hist = macd - signal
        
        return {
            "macd": macd.iloc[-1],
            "signal": signal.iloc[-1],
            "hist": hist.iloc[-1],
            "is_bullish": hist.iloc[-1] > 0,
            "is_bearish": hist.iloc[-1] < 0
        }
    
    def _calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 20) -> Dict:
        """计算布林带指标"""
        sma = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        upper_band = sma + (std * 2)
        lower_band = sma - (std * 2)
        
        return {
            "upper": upper_band.iloc[-1],
            "middle": sma.iloc[-1],
            "lower": lower_band.iloc[-1],
            "is_overbought": df['close'].iloc[-1] > upper_band.iloc[-1],
            "is_oversold": df['close'].iloc[-1] < lower_band.iloc[-1]
        }
    
    def _generate_signals(self, indicators: Dict) -> Dict:
        """
        生成交易信号
        
        Args:
            indicators: 技术指标数据
            
        Returns:
            Dict: 交易信号
        """
        signals = {
            "buy": False,
            "sell": False,
            "strength": 0,
            "reason": []
        }
        
        # RSI信号
        if "RSI" in indicators:
            rsi = indicators["RSI"]
            if rsi["is_oversold"]:
                signals["buy"] = True
                signals["strength"] += 1
                signals["reason"].append("RSI超卖")
            elif rsi["is_overbought"]:
                signals["sell"] = True
                signals["strength"] -= 1
                signals["reason"].append("RSI超买")
        
        # MACD信号
        if "MACD" in indicators:
            macd = indicators["MACD"]
            if macd["is_bullish"]:
                signals["buy"] = True
                signals["strength"] += 1
                signals["reason"].append("MACD金叉")
            elif macd["is_bearish"]:
                signals["sell"] = True
                signals["strength"] -= 1
                signals["reason"].append("MACD死叉")
        
        # 布林带信号
        if "BB" in indicators:
            bb = indicators["BB"]
            if bb["is_oversold"]:
                signals["buy"] = True
                signals["strength"] += 1
                signals["reason"].append("价格触及布林带下轨")
            elif bb["is_overbought"]:
                signals["sell"] = True
                signals["strength"] -= 1
                signals["reason"].append("价格触及布林带上轨")
        
        return signals
    
    def get_market_summary(self) -> Dict:
        """
        获取市场总结
        
        Returns:
            Dict: 市场总结数据
        """
        summary = {
            "timestamp": datetime.now().isoformat(),
            "symbols": {}
        }
        
        for symbol in self.symbols:
            symbol_summary = {}
            for timeframe in self.timeframes:
                analysis = self.analyze_market(symbol, timeframe)
                if analysis:
                    symbol_summary[timeframe] = analysis
            
            if symbol_summary:
                summary["symbols"][symbol] = symbol_summary
        
        return summary 