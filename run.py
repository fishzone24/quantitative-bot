#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CryptoQuantTrader 启动脚本
"""

import os
import sys
import logging
import time
from datetime import datetime
from dotenv import load_dotenv
from menu import Menu
from analysis.market_analysis import MarketAnalyzer
from analysis.social_analysis import SocialMediaAnalyzer
from analysis.ai_analysis import AIAnalyzer
from trading.trading_engine import TradingEngine
from exchanges.exchange_client import ExchangeClient

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('main')

def init_settings():
    """初始化设置"""
    try:
        # 加载环境变量
        load_dotenv()
        
        # 初始化交易所客户端
        exchange_name = os.getenv("EXCHANGE", "binance")
        exchange = ExchangeClient(exchange_name)
        
        # 初始化市场分析器
        market_analyzer = MarketAnalyzer()
        
        # 初始化社交媒体分析器
        social_analyzer = SocialMediaAnalyzer()
        
        # 初始化AI分析器
        ai_analyzer = AIAnalyzer()
        
        # 初始化交易引擎
        trading_engine = TradingEngine()
        
        logger.info("初始化设置完成")
        return True
        
    except Exception as e:
        logger.error(f"初始化设置失败: {str(e)}")
        return False

def run_command_line():
    """命令行模式运行"""
    try:
        # 市场分析
        print("\n🔍 正在运行市场分析...")
        market_analyzer = MarketAnalyzer()
        market_summary = market_analyzer.get_market_summary()
        
        print("\n📊 市场分析结果:")
        for symbol, timeframes in market_summary["symbols"].items():
            print(f"\n{symbol}:")
            for timeframe, analysis in timeframes.items():
                print(f"\n{timeframe}周期:")
                print(f"当前价格: {analysis['current_price']}")
                print("技术指标:")
                for indicator, value in analysis['indicators'].items():
                    print(f"- {indicator}: {value}")
                print("交易信号:")
                signals = analysis['signals']
                if signals['buy']:
                    print(f"- 买入信号 (强度: {signals['strength']})")
                    print(f"- 原因: {', '.join(signals['reason'])}")
                if signals['sell']:
                    print(f"- 卖出信号 (强度: {abs(signals['strength'])})")
                    print(f"- 原因: {', '.join(signals['reason'])}")
        
        # AI分析
        print("\n🤖 正在运行AI分析...")
        ai_analyzer = AIAnalyzer()
        ai_summary = ai_analyzer.get_ai_summary()
        
        print("\n📈 AI分析结果:")
        for symbol, analysis in ai_summary["symbols"].items():
            print(f"\n{symbol}:")
            print(f"趋势预测: {analysis['trend']}")
            print(f"置信度: {analysis['confidence']}")
            print(f"建议操作: {analysis['action']}")
            print(f"理由: {analysis['reason']}")
        
        # 社交媒体分析
        print("\n💬 正在分析社交媒体...")
        social_analyzer = SocialMediaAnalyzer()
        social_summary = social_analyzer.get_social_summary()
        
        print("\n📱 社交媒体分析结果:")
        for symbol, analysis in social_summary["symbols"].items():
            print(f"\n{symbol}:")
            print(f"情感得分: {analysis['sentiment_score']}")
            print(f"市场情绪: {analysis['market_sentiment']}")
            print(f"热门话题: {', '.join(analysis['hot_topics'])}")
            print(f"重要新闻: {', '.join(analysis['important_news'])}")
        
        print("\n✅ 分析完成")
        
    except Exception as e:
        logger.error(f"命令行模式运行失败: {str(e)}")
        print(f"运行失败: {str(e)}")
        print("请确保已安装所有依赖包，命令: pip install -r requirements.txt")

def main():
    """主函数"""
    try:
        # 初始化设置
        if not init_settings():
            print("初始化设置失败，请检查配置")
            return
        
        # 尝试启动菜单
        try:
            menu = Menu()
            menu.run()
        except Exception as e:
            print(f"启动菜单失败: {str(e)}")
            print("尝试以命令行模式运行...")
            run_command_line()
            
    except Exception as e:
        logger.error(f"程序运行失败: {str(e)}")
        print(f"启动失败: {str(e)}")
        print("请确保已安装所有依赖包，命令: pip install -r requirements.txt")

if __name__ == "__main__":
    main() 