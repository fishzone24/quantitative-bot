#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
交易报告工具 - 用于生成交易绩效报告和图表
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from datetime import datetime, timedelta
import argparse

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入交易记录器
from trading.trade_recorder import TradeRecorder

# 设置绘图样式
plt.style.use('seaborn-v0_8-darkgrid')
sns.set(font_scale=1.2)
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

class TradingReportGenerator:
    """交易报告生成器"""
    
    def __init__(self, output_dir=None):
        """
        初始化报告生成器
        
        Args:
            output_dir: 输出目录
        """
        self.trade_recorder = TradeRecorder()
        self.output_dir = output_dir or "data/reports"
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_performance_report(self, period=None):
        """
        生成绩效报告
        
        Args:
            period: 时间周期 (daily, weekly, monthly, all)
            
        Returns:
            str: 报告文件路径
        """
        # 获取绩效指标
        metrics = self.trade_recorder.get_performance_metrics(period)
        
        if not metrics:
            print("无法获取绩效指标")
            return None
        
        # 获取交易历史
        trades = self.trade_recorder.get_trade_history(limit=1000)
        if not trades:
            print("无交易历史记录")
            return None
            
        # 转换为DataFrame
        trades_df = pd.DataFrame(trades)
        
        # 筛选已关闭的交易
        closed_trades = trades_df[trades_df['status'] == 'CLOSED'].copy()
        
        if len(closed_trades) == 0:
            print("无已关闭的交易记录")
            return None
        
        # 准备数据
        closed_trades['entry_time'] = pd.to_datetime(closed_trades['entry_time'])
        closed_trades['exit_time'] = pd.to_datetime(closed_trades['exit_time'])
        closed_trades['duration'] = (closed_trades['exit_time'] - closed_trades['entry_time']).dt.total_seconds() / 3600  # 小时
        
        # 按时间排序
        closed_trades = closed_trades.sort_values('exit_time')
        
        # 计算累计收益
        closed_trades['cumulative_profit'] = closed_trades['profit_loss'].cumsum()
        
        # 生成报告
        report_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(self.output_dir, f"performance_report_{report_time}.html")
        
        # 创建HTML报告
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>交易绩效报告</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        line-height: 1.6;
                    }}
                    h1, h2, h3 {{
                        color: #2c3e50;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        margin: 20px 0;
                    }}
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 8px;
                        text-align: left;
                    }}
                    th {{
                        background-color: #f2f2f2;
                    }}
                    tr:nth-child(even) {{
                        background-color: #f9f9f9;
                    }}
                    .summary-container {{
                        display: flex;
                        flex-wrap: wrap;
                    }}
                    .summary-box {{
                        background-color: #f8f9fa;
                        border-radius: 5px;
                        padding: 15px;
                        margin: 10px;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                        flex: 1;
                        min-width: 200px;
                    }}
                    .positive {{
                        color: green;
                    }}
                    .negative {{
                        color: red;
                    }}
                </style>
            </head>
            <body>
                <h1>交易绩效报告</h1>
                <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <h2>绩效摘要</h2>
                <div class="summary-container">
                    <div class="summary-box">
                        <h3>交易统计</h3>
                        <p>总交易次数: <strong>{metrics['total_trades']}</strong></p>
                        <p>盈利交易: <strong class="positive">{metrics['winning_trades']}</strong></p>
                        <p>亏损交易: <strong class="negative">{metrics['losing_trades']}</strong></p>
                        <p>胜率: <strong>{metrics['win_rate']*100:.2f}%</strong></p>
                    </div>
                    
                    <div class="summary-box">
                        <h3>盈亏分析</h3>
                        <p>总盈亏: <strong class="{'positive' if metrics['total_profit_loss'] >= 0 else 'negative'}">{metrics['total_profit_loss']:.2f}</strong></p>
                        <p>平均盈利: <strong class="positive">{metrics['average_profit']:.2f}</strong></p>
                        <p>平均亏损: <strong class="negative">{metrics['average_loss']:.2f}</strong></p>
                        <p>盈亏比: <strong>{metrics['profit_factor']:.2f}</strong></p>
                    </div>
                    
                    <div class="summary-box">
                        <h3>风险指标</h3>
                        <p>夏普比率: <strong>{metrics['sharpe_ratio']:.2f}</strong></p>
                        <p>最大回撤: <strong class="negative">{metrics['max_drawdown']:.2f}</strong></p>
                        <p>平均交易: <strong class="{'positive' if metrics['average_trade'] >= 0 else 'negative'}">{metrics['average_trade']:.2f}</strong></p>
                    </div>
                </div>
                
                <h2>交易记录摘要</h2>
                <table>
                    <tr>
                        <th>交易对</th>
                        <th>方向</th>
                        <th>入场时间</th>
                        <th>入场价格</th>
                        <th>出场时间</th>
                        <th>出场价格</th>
                        <th>盈亏</th>
                        <th>盈亏百分比</th>
                    </tr>
            """)
            
            # 添加最近10条交易记录
            for _, row in closed_trades.tail(10).iterrows():
                profit_class = "positive" if row['profit_loss'] >= 0 else "negative"
                f.write(f"""
                    <tr>
                        <td>{row['symbol']}</td>
                        <td>{row['side'].upper()}</td>
                        <td>{row['entry_time']}</td>
                        <td>{float(row['entry_price']):.4f}</td>
                        <td>{row['exit_time']}</td>
                        <td>{float(row['exit_price']):.4f}</td>
                        <td class="{profit_class}">{float(row['profit_loss']):.2f}</td>
                        <td class="{profit_class}">{float(row['profit_loss_pct']):.2f}%</td>
                    </tr>
                """)
            
            f.write("""
                </table>
            """)
            
            # 生成图表
            self._generate_charts(closed_trades)
            
            # 添加图表到报告
            f.write(f"""
                <h2>绩效图表</h2>
                <div>
                    <h3>累计收益</h3>
                    <img src="cumulative_returns.png" alt="累计收益" style="width:100%;max-width:800px;">
                </div>
                
                <div>
                    <h3>盈亏分布</h3>
                    <img src="profit_loss_distribution.png" alt="盈亏分布" style="width:100%;max-width:800px;">
                </div>
                
                <div>
                    <h3>交易对绩效</h3>
                    <img src="symbol_performance.png" alt="交易对绩效" style="width:100%;max-width:800px;">
                </div>
                
            </body>
            </html>
            """)
        
        print(f"交易绩效报告已生成: {report_file}")
        return report_file
    
    def _generate_charts(self, trades_df):
        """
        生成图表
        
        Args:
            trades_df: 交易记录DataFrame
        """
        # 1. 累计收益图
        plt.figure(figsize=(12, 6))
        plt.plot(trades_df['exit_time'], trades_df['cumulative_profit'], 'b-', linewidth=2)
        plt.fill_between(trades_df['exit_time'], trades_df['cumulative_profit'], 0, 
                         where=(trades_df['cumulative_profit'] >= 0), color='green', alpha=0.3)
        plt.fill_between(trades_df['exit_time'], trades_df['cumulative_profit'], 0, 
                         where=(trades_df['cumulative_profit'] < 0), color='red', alpha=0.3)
        plt.xlabel('时间')
        plt.ylabel('累计收益')
        plt.title('累计收益曲线')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'cumulative_returns.png'))
        plt.close()
        
        # 2. 盈亏分布图
        plt.figure(figsize=(12, 6))
        sns.histplot(trades_df['profit_loss_pct'], bins=20, kde=True)
        plt.axvline(x=0, color='r', linestyle='--')
        plt.xlabel('盈亏百分比 (%)')
        plt.ylabel('频率')
        plt.title('盈亏分布')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'profit_loss_distribution.png'))
        plt.close()
        
        # 3. 交易对绩效图
        symbol_performance = trades_df.groupby('symbol')['profit_loss'].sum().sort_values()
        plt.figure(figsize=(12, 6))
        bars = plt.bar(symbol_performance.index, symbol_performance.values)
        
        # 为柱状图着色
        for i, bar in enumerate(bars):
            if symbol_performance.values[i] >= 0:
                bar.set_color('green')
            else:
                bar.set_color('red')
        
        plt.xlabel('交易对')
        plt.ylabel('总盈亏')
        plt.title('各交易对绩效')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'symbol_performance.png'))
        plt.close()
    
    def generate_trade_list_report(self, limit=100):
        """
        生成交易列表报告
        
        Args:
            limit: 显示的交易记录数量限制
            
        Returns:
            str: 报告文件路径
        """
        # 获取交易历史
        trades = self.trade_recorder.get_trade_history(limit=limit)
        if not trades:
            print("无交易历史记录")
            return None
            
        # 转换为DataFrame
        trades_df = pd.DataFrame(trades)
        
        # 生成报告
        report_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(self.output_dir, f"trades_list_{report_time}.html")
        
        # 创建HTML报告
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>交易历史记录</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        line-height: 1.6;
                    }}
                    h1, h2 {{
                        color: #2c3e50;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        margin: 20px 0;
                    }}
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 8px;
                        text-align: left;
                    }}
                    th {{
                        background-color: #f2f2f2;
                    }}
                    tr:nth-child(even) {{
                        background-color: #f9f9f9;
                    }}
                    .positive {{
                        color: green;
                    }}
                    .negative {{
                        color: red;
                    }}
                    .status-open {{
                        background-color: #e6f7ff;
                    }}
                    .status-closed {{
                        background-color: #f6f6f6;
                    }}
                </style>
            </head>
            <body>
                <h1>交易历史记录</h1>
                <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>显示最近 {len(trades_df)} 条交易记录</p>
                
                <table>
                    <tr>
                        <th>ID</th>
                        <th>状态</th>
                        <th>交易对</th>
                        <th>方向</th>
                        <th>数量</th>
                        <th>入场时间</th>
                        <th>入场价格</th>
                        <th>出场时间</th>
                        <th>出场价格</th>
                        <th>盈亏</th>
                        <th>盈亏百分比</th>
                        <th>策略</th>
                    </tr>
            """)
            
            # 添加交易记录
            for _, row in trades_df.iterrows():
                status_class = "status-open" if row['status'] == 'OPEN' else "status-closed"
                profit_class = ""
                profit_str = ""
                profit_pct_str = ""
                
                if row['status'] == 'CLOSED':
                    profit_class = "positive" if float(row['profit_loss']) >= 0 else "negative"
                    profit_str = f"{float(row['profit_loss']):.2f}"
                    profit_pct_str = f"{float(row['profit_loss_pct']):.2f}%"
                
                f.write(f"""
                    <tr class="{status_class}">
                        <td>{row['trade_id'][:8]}...</td>
                        <td>{row['status']}</td>
                        <td>{row['symbol']}</td>
                        <td>{row['side'].upper()}</td>
                        <td>{float(row['quantity']):.4f}</td>
                        <td>{row['entry_time']}</td>
                        <td>{float(row['entry_price']):.4f}</td>
                        <td>{row['exit_time'] if row['exit_time'] else '-'}</td>
                        <td>{float(row['exit_price']) if row['exit_price'] else '-'}</td>
                        <td class="{profit_class}">{profit_str}</td>
                        <td class="{profit_class}">{profit_pct_str}</td>
                        <td>{row['strategy']}</td>
                    </tr>
                """)
            
            f.write("""
                </table>
            </body>
            </html>
            """)
        
        print(f"交易历史报告已生成: {report_file}")
        return report_file


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='交易报告工具')
    parser.add_argument('--performance', action='store_true', help='生成绩效报告')
    parser.add_argument('--trades', action='store_true', help='生成交易列表报告')
    parser.add_argument('--period', choices=['daily', 'weekly', 'monthly', 'all'], default='all', help='绩效报告时间周期')
    parser.add_argument('--limit', type=int, default=100, help='交易列表记录数量限制')
    parser.add_argument('--output', type=str, default='data/reports', help='输出目录')
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    report_generator = TradingReportGenerator(output_dir=args.output)
    
    if args.performance:
        report_generator.generate_performance_report(period=args.period)
    
    if args.trades:
        report_generator.generate_trade_list_report(limit=args.limit)
    
    # 如果没有指定任何报告，生成两种报告
    if not (args.performance or args.trades):
        report_generator.generate_performance_report()
        report_generator.generate_trade_list_report()


if __name__ == "__main__":
    main() 