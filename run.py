#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CryptoQuantTrader 启动脚本
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
from exchanges.exchange_client import ExchangeClient
from analysis.market_analysis import MarketAnalyzer
from analysis.social_analysis import SocialMediaAnalyzer
from trading.trading_engine import TradingEngine
from trading.risk_manager import RiskManager
from utils.logger import setup_logger
from utils.config import load_config
from utils.menu import Menu

# 加载环境变量
load_dotenv()

# 设置日志
logger = setup_logger()

def main():
    """主程序入口"""
    try:
        # 加载配置
        config = load_config()
        
        # 初始化交易所客户端
        exchange = os.getenv("EXCHANGE", "binance")
        exchange_client = ExchangeClient(exchange=exchange)
        
        # 初始化市场分析器
        market_analyzer = MarketAnalyzer(config.get("market_analysis", {}))
        
        # 初始化社交媒体分析器
        social_analyzer = SocialMediaAnalyzer(config.get("social_analysis", {}))
        
        # 初始化风险管理器
        risk_manager = RiskManager(config.get("risk_management", {}))
        
        # 初始化交易引擎
        trading_engine = TradingEngine(
            exchange_client=exchange_client,
            market_analyzer=market_analyzer,
            social_analyzer=social_analyzer,
            risk_manager=risk_manager,
            config=config.get("trading", {})
        )
        
        # 启动菜单
        menu = Menu(trading_engine)
        menu.run()
        
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 