#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
import argparse
import schedule
import importlib
from datetime import datetime

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入配置
import config

# 导入交易所模块
from exchanges.exchange_client import ExchangeClientFactory

# 导入分析模块
from analysis.technical_analysis import TechnicalAnalysis
from analysis.social_analysis import SocialMediaAnalyzer
from analysis.ai_analysis import AIAnalyzer

# 导入交易模块
from trading.trade_recorder import TradeRecorder
from trading.auto_trader import AutoTrader

# 设置日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data/logs/trading.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('main')

# 确保日志目录存在
os.makedirs("data/logs", exist_ok=True)

class CryptoQuantTrader:
    """加密货币量化交易系统主类"""
    
    def __init__(self, args=None):
        """
        初始化加密货币量化交易系统
        
        Args:
            args: 命令行参数
        """
        self.args = args
        
        # 创建交易所客户端
        self.exchange_client = ExchangeClientFactory.create_client(config.EXCHANGE)
        
        # 初始化技术分析模块
        self.technical_analyzer = TechnicalAnalysis(config.TA_CONFIG)
        
        # 初始化社交媒体分析模块
        self.social_analyzer = SocialMediaAnalyzer(config.SOCIAL_CONFIG)
        
        # 初始化AI分析模块
        self.ai_analyzer = AIAnalyzer(config.AI_CONFIG)
        
        # 初始化交易记录器
        self.trade_recorder = TradeRecorder()
        
        # 初始化自动交易器
        self.auto_trader = AutoTrader(
            exchange_client=self.exchange_client,
            trade_recorder=self.trade_recorder,
            config=config.__dict__
        )
        
        # 交易对缓存
        self.pair_data_cache = {}
        self.social_data_cache = None
        self.last_social_update = None
        
        # 运行模式设置
        self.analysis_only = args.analysis_only if args else False
        
        # 获取时间周期设置
        self.timeframe = config.TIMEFRAME
        
        logger.info(f"初始化加密货币量化交易系统完成，运行模式: {'分析' if self.analysis_only else '交易'}, 时间周期: {self.timeframe}")
    
    def start(self):
        """启动交易系统"""
        try:
            logger.info("启动加密货币量化交易系统")
            
            # 先运行一次完整分析
            self.run_analysis()
            
            # 检查是否只运行分析
            if not self.analysis_only:
                # 检查未平仓头寸
                self.auto_trader.check_open_positions()
            
            # 设置定时任务
            # 每5分钟运行一次分析
            schedule.every(config.DATA_REFRESH_INTERVAL).seconds.do(self.run_analysis)
            
            # 如果不是只分析模式，每分钟检查一次开仓情况
            if not self.analysis_only:
                schedule.every(60).seconds.do(self.auto_trader.check_open_positions)
            
            # 每天0点更新统计数据
            schedule.every().day.at("00:00").do(self.trade_recorder.update_summary)
            
            # 主循环
            while True:
                schedule.run_pending()
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("用户中断，正常退出")
        except Exception as e:
            logger.error(f"系统运行出错: {str(e)}", exc_info=True)
        finally:
            logger.info("关闭加密货币量化交易系统")
    
    def run_analysis(self):
        """运行完整分析流程"""
        try:
            logger.info("开始市场分析...")
            
            # 获取社交媒体数据(每15分钟更新一次)
            current_time = datetime.now()
            if (self.social_data_cache is None or 
                self.last_social_update is None or 
                (current_time - self.last_social_update).total_seconds() >= config.SOCIAL_REFRESH_INTERVAL):
                
                logger.info("更新社交媒体分析...")
                self.social_data_cache = self.social_analyzer.analyze_binance_tweets()
                self.last_social_update = current_time
            
            # 分析每个交易对
            for trading_pair in config.TRADING_PAIRS:
                self.analyze_trading_pair(trading_pair)
            
            logger.info("市场分析完成")
            
        except Exception as e:
            logger.error(f"分析过程出错: {str(e)}", exc_info=True)
    
    def analyze_trading_pair(self, trading_pair):
        """
        分析单个交易对
        
        Args:
            trading_pair: 交易对
        """
        try:
            logger.info(f"分析交易对: {trading_pair}")
            
            # 获取历史K线数据，使用配置的时间周期
            ohlcv = self.exchange_client.get_historical_data(
                symbol=trading_pair,
                timeframe=self.timeframe,
                limit=200  # 获取足够多的数据进行分析
            )
            
            if not ohlcv or len(ohlcv) < 50:
                logger.warning(f"获取 {trading_pair} 的历史数据不足，跳过分析")
                return
            
            # 准备数据并添加技术指标
            df = self.technical_analyzer.prepare_data(ohlcv, add_all_ta=True)
            
            # 获取技术分析信号
            technical_analysis = self.technical_analyzer.get_signal(df)
            
            # 获取当前价格
            ticker = self.exchange_client.get_ticker(trading_pair)
            current_price = ticker['last'] if ticker else technical_analysis.get('current_price')
            
            # AI决策分析
            ai_analysis = self.ai_analyzer.analyze_market_data(
                technical_data=technical_analysis,
                social_data=self.social_data_cache,
                trading_pair=trading_pair
            )
            
            # 记录分析结果
            self.pair_data_cache[trading_pair] = {
                'technical': technical_analysis,
                'ai': ai_analysis,
                'price': current_price,
                'timestamp': datetime.now()
            }
            
            # 输出分析摘要
            self._print_analysis_summary(trading_pair, technical_analysis, ai_analysis)
            
            # 如果不是只分析模式，执行交易
            if not self.analysis_only:
                # 使用AI建议进行交易
                signal = ai_analysis.get('recommendation')
                confidence = ai_analysis.get('confidence')
                
                if signal and confidence:
                    # 只有当置信度超过阈值时才执行交易
                    trade_result = self.auto_trader.execute_trade(
                        symbol=trading_pair,
                        signal=signal,
                        price=current_price,
                        confidence=confidence,
                        ai_analysis=ai_analysis
                    )
                    
                    if trade_result['status'] == 'success':
                        logger.info(f"交易执行成功: {trading_pair} {signal.upper()} @ {current_price}")
                    elif trade_result['status'] != 'ignored':
                        logger.warning(f"交易执行失败: {trade_result['reason']}")
            
        except Exception as e:
            logger.error(f"分析交易对 {trading_pair} 出错: {str(e)}", exc_info=True)
    
    def _print_analysis_summary(self, trading_pair, technical_analysis, ai_analysis):
        """
        打印分析摘要
        
        Args:
            trading_pair: 交易对
            technical_analysis: 技术分析结果
            ai_analysis: AI分析结果
        """
        # 构建摘要信息
        price = technical_analysis.get('current_price', 'N/A')
        tech_signal = technical_analysis.get('signal', 'neutral')
        
        ai_recommendation = ai_analysis.get('recommendation', 'neutral')
        ai_confidence = ai_analysis.get('confidence', 0)
        
        # 获取趋势信息
        trend_info = technical_analysis.get('trend', {})
        short_trend = trend_info.get('short_trend', 'unknown')
        long_trend = trend_info.get('long_trend', 'unknown')
        
        # 输出摘要
        logger.info(f"分析摘要 - {trading_pair} @ {price} (K线周期: {self.timeframe})")
        logger.info(f"技术信号: {tech_signal.upper()}, 短期趋势: {short_trend}, 长期趋势: {long_trend}")
        logger.info(f"AI建议: {ai_recommendation.upper()} (置信度: {ai_confidence}%)")
        logger.info(f"AI观点: {ai_analysis.get('market_overview', 'N/A')[:100]}...")
    
    def get_analysis_report(self, trading_pair=None):
        """
        获取分析报告
        
        Args:
            trading_pair: 交易对，如果为None则返回所有交易对的报告
            
        Returns:
            dict: 分析报告
        """
        if trading_pair:
            return self.pair_data_cache.get(trading_pair)
        else:
            return self.pair_data_cache


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='加密货币量化交易系统')
    parser.add_argument('--analysis-only', action='store_true', help='仅运行分析，不执行交易')
    parser.add_argument('--report', action='store_true', help='生成交易报告')
    parser.add_argument('--list-trades', action='store_true', help='列出交易历史')
    parser.add_argument('--close-all', action='store_true', help='关闭所有头寸')
    parser.add_argument('--menu', action='store_true', help='启动交互式菜单')
    
    return parser.parse_args()


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 检查是否启动菜单
    if args.menu:
        try:
            from menu import run_menu
            run_menu()
            return
        except Exception as e:
            print(f"启动菜单失败: {str(e)}")
            print("将继续以命令行模式运行...")
    
    # 处理特殊命令
    if args.report:
        generate_report()
        return
    
    if args.list_trades:
        list_trades()
        return
    
    if args.close_all:
        close_all_positions()
        return
    
    # 创建并启动交易系统
    trader = CryptoQuantTrader(args)
    trader.start()


def generate_report():
    """生成交易报告"""
    try:
        trade_recorder = TradeRecorder()
        metrics = trade_recorder.get_performance_metrics()
        
        print("\n========== 交易绩效报告 ==========")
        print(f"总交易次数: {metrics['total_trades']}")
        print(f"盈利交易: {metrics['winning_trades']}")
        print(f"亏损交易: {metrics['losing_trades']}")
        print(f"胜率: {metrics['win_rate']*100:.2f}%")
        print(f"总盈亏: {metrics['total_profit_loss']:.2f}")
        print(f"平均盈利: {metrics['average_profit']:.2f}")
        print(f"平均亏损: {metrics['average_loss']:.2f}")
        print(f"盈亏比: {metrics['profit_factor']:.2f}")
        print(f"夏普比率: {metrics['sharpe_ratio']:.2f}")
        print(f"最大回撤: {metrics['max_drawdown']:.2f}")
        print("===================================\n")
        
    except Exception as e:
        print(f"生成报告出错: {str(e)}")


def list_trades():
    """列出交易历史"""
    try:
        trade_recorder = TradeRecorder()
        trades = trade_recorder.get_trade_history(limit=20)
        
        print("\n========== 最近交易记录 ==========")
        for trade in trades:
            status = trade['status']
            symbol = trade['symbol']
            side = trade['side']
            entry_price = trade['entry_price']
            exit_price = trade['exit_price'] if trade['exit_price'] else 'N/A'
            profit_loss = trade['profit_loss'] if status == 'CLOSED' else 'N/A'
            profit_loss_pct = trade['profit_loss_pct'] if status == 'CLOSED' else 'N/A'
            
            print(f"{symbol} {side.upper()} {status}")
            print(f"  入场: {entry_price} | 出场: {exit_price}")
            if status == 'CLOSED':
                print(f"  盈亏: {profit_loss:.2f} ({profit_loss_pct:.2f}%)")
            print("---------------------------------")
        
        print("===================================\n")
        
    except Exception as e:
        print(f"列出交易历史出错: {str(e)}")


def close_all_positions():
    """关闭所有头寸"""
    try:
        # 创建所需的对象
        exchange_client = ExchangeClientFactory.create_client(config.EXCHANGE)
        trade_recorder = TradeRecorder()
        auto_trader = AutoTrader(
            exchange_client=exchange_client,
            trade_recorder=trade_recorder,
            config=config.__dict__
        )
        
        # 关闭所有头寸
        closed_trades = auto_trader.close_all_positions("手动平仓")
        
        print(f"\n成功关闭 {len(closed_trades)} 个头寸")
        for trade in closed_trades:
            print(f"  {trade['symbol']} @ {trade['price']}")
        
    except Exception as e:
        print(f"关闭头寸出错: {str(e)}")


if __name__ == "__main__":
    main() 