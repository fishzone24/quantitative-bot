import os
import csv
import json
import logging
import pandas as pd
from datetime import datetime
import uuid

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('trade_recorder')

class TradeRecorder:
    """交易记录类"""
    
    def __init__(self, trades_file=None, summary_file=None):
        """
        初始化交易记录器
        
        Args:
            trades_file: 交易记录文件路径
            summary_file: 交易汇总文件路径
        """
        self.trades_file = trades_file or os.getenv("TRADE_RECORDS_FILE", "data/trade_records/trades.csv")
        self.summary_file = summary_file or os.getenv("TRADE_SUMMARY_FILE", "data/trade_records/summary.csv")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.trades_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.summary_file), exist_ok=True)
        
        # 初始化交易记录文件
        self._init_trade_records_file()
        self._init_summary_file()
        
        logger.info("初始化交易记录器")
    
    def _init_trade_records_file(self):
        """初始化交易记录文件"""
        if not os.path.exists(self.trades_file):
            # 创建文件并写入表头
            with open(self.trades_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'trade_id', 'symbol', 'side', 'entry_time', 'entry_price', 
                    'quantity', 'exit_time', 'exit_price', 'profit_loss', 
                    'profit_loss_pct', 'status', 'strategy', 'tags', 'notes'
                ])
            logger.info(f"创建新的交易记录文件: {self.trades_file}")
    
    def _init_summary_file(self):
        """初始化交易汇总文件"""
        if not os.path.exists(self.summary_file):
            # 创建文件并写入表头
            with open(self.summary_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'date', 'total_trades', 'winning_trades', 'losing_trades',
                    'win_rate', 'profit_loss', 'average_profit', 'average_loss',
                    'largest_profit', 'largest_loss', 'profit_factor', 'sharpe_ratio'
                ])
            logger.info(f"创建新的交易汇总文件: {self.summary_file}")
    
    def record_trade_entry(self, symbol, side, entry_price, quantity, 
                          strategy=None, stop_loss=None, take_profit=None, 
                          tags=None, notes=None):
        """
        记录交易入场
        
        Args:
            symbol: 交易对
            side: 买入/卖出
            entry_price: 入场价格
            quantity: 交易数量
            strategy: 交易策略
            stop_loss: 止损价格
            take_profit: 止盈价格
            tags: 标签列表
            notes: 备注
            
        Returns:
            str: 交易ID
        """
        try:
            # 生成交易ID
            trade_id = str(uuid.uuid4())
            
            # 当前时间
            entry_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 格式化标签
            tags_str = json.dumps(tags) if tags else ''
            
            # 构建交易记录
            trade_data = [
                trade_id, symbol, side, entry_time, entry_price, 
                quantity, '', '', 0, 0, 'OPEN', strategy or '', tags_str, notes or ''
            ]
            
            # 写入CSV文件
            with open(self.trades_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(trade_data)
            
            # 记录止损止盈信息
            self._record_risk_management(trade_id, stop_loss, take_profit)
            
            logger.info(f"记录交易入场: {trade_id} {side} {symbol} @ {entry_price}")
            
            return trade_id
            
        except Exception as e:
            logger.error(f"记录交易入场失败: {str(e)}")
            return None
    
    def record_trade_exit(self, trade_id, exit_price, exit_time=None, notes=None):
        """
        记录交易出场
        
        Args:
            trade_id: 交易ID
            exit_price: 出场价格
            exit_time: 出场时间，默认为当前时间
            notes: 备注
            
        Returns:
            bool: 是否成功
        """
        try:
            # 加载现有的交易记录
            trades_df = pd.read_csv(self.trades_file)
            
            # 查找匹配的交易ID
            trade_row = trades_df[trades_df['trade_id'] == trade_id]
            
            if len(trade_row) == 0:
                logger.error(f"找不到交易ID: {trade_id}")
                return False
            
            # 如果交易已关闭，忽略
            if trade_row.iloc[0]['status'] != 'OPEN':
                logger.warning(f"交易 {trade_id} 已关闭，忽略本次出场记录")
                return False
            
            # 记录出场时间
            if exit_time is None:
                exit_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 计算盈亏
            entry_price = float(trade_row.iloc[0]['entry_price'])
            quantity = float(trade_row.iloc[0]['quantity'])
            side = trade_row.iloc[0]['side']
            
            if side.upper() == 'BUY':
                profit_loss = (float(exit_price) - entry_price) * quantity
                profit_loss_pct = (float(exit_price) - entry_price) / entry_price * 100
            else:  # SELL
                profit_loss = (entry_price - float(exit_price)) * quantity
                profit_loss_pct = (entry_price - float(exit_price)) / entry_price * 100
            
            # 更新交易记录
            index = trade_row.index[0]
            trades_df.at[index, 'exit_time'] = exit_time
            trades_df.at[index, 'exit_price'] = exit_price
            trades_df.at[index, 'profit_loss'] = profit_loss
            trades_df.at[index, 'profit_loss_pct'] = profit_loss_pct
            trades_df.at[index, 'status'] = 'CLOSED'
            
            if notes:
                trades_df.at[index, 'notes'] = notes
            
            # 保存更新后的交易记录
            trades_df.to_csv(self.trades_file, index=False)
            
            # 更新交易汇总
            self.update_summary()
            
            logger.info(f"记录交易出场: {trade_id} @ {exit_price} 盈亏: {profit_loss:.2f} ({profit_loss_pct:.2f}%)")
            
            return True
            
        except Exception as e:
            logger.error(f"记录交易出场失败: {str(e)}")
            return False
    
    def _record_risk_management(self, trade_id, stop_loss, take_profit):
        """
        记录风险管理信息
        
        Args:
            trade_id: 交易ID
            stop_loss: 止损价格
            take_profit: 止盈价格
        """
        if not stop_loss and not take_profit:
            return
        
        try:
            # 创建风险管理记录文件夹
            risk_dir = os.path.join(os.path.dirname(self.trades_file), 'risk_management')
            os.makedirs(risk_dir, exist_ok=True)
            
            # 风险管理记录文件
            risk_file = os.path.join(risk_dir, f"{trade_id}.json")
            
            # 保存风险管理信息
            risk_data = {
                'trade_id': trade_id,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with open(risk_file, 'w') as f:
                json.dump(risk_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"记录风险管理信息失败: {str(e)}")
    
    def update_summary(self):
        """更新交易汇总"""
        try:
            # 加载交易记录
            trades_df = pd.read_csv(self.trades_file)
            
            # 只分析已关闭的交易
            closed_trades = trades_df[trades_df['status'] == 'CLOSED']
            
            if len(closed_trades) == 0:
                logger.info("没有已关闭的交易，跳过汇总更新")
                return
            
            # 转换日期列
            closed_trades['entry_time'] = pd.to_datetime(closed_trades['entry_time'])
            closed_trades['exit_time'] = pd.to_datetime(closed_trades['exit_time'])
            
            # 按日期分组
            closed_trades['date'] = closed_trades['exit_time'].dt.date
            daily_groups = closed_trades.groupby('date')
            
            # 准备汇总数据
            summary_data = []
            
            for date, group in daily_groups:
                # 统计盈亏情况
                winning_trades = group[group['profit_loss'] > 0]
                losing_trades = group[group['profit_loss'] < 0]
                
                total_trades = len(group)
                wins = len(winning_trades)
                losses = len(losing_trades)
                win_rate = wins / total_trades if total_trades > 0 else 0
                
                # 计算盈亏数据
                total_profit_loss = group['profit_loss'].sum()
                avg_profit = winning_trades['profit_loss'].mean() if wins > 0 else 0
                avg_loss = losing_trades['profit_loss'].mean() if losses > 0 else 0
                largest_profit = winning_trades['profit_loss'].max() if wins > 0 else 0
                largest_loss = losing_trades['profit_loss'].min() if losses > 0 else 0
                
                # 计算盈亏因子
                profit_factor = abs(winning_trades['profit_loss'].sum() / losing_trades['profit_loss'].sum()) if losses > 0 and losing_trades['profit_loss'].sum() != 0 else float('inf')
                
                # 计算夏普比率 (简化版，使用0作为无风险收益率)
                if total_trades > 1:
                    returns = group['profit_loss_pct'] / 100  # 转换为小数
                    sharpe_ratio = returns.mean() / returns.std() if returns.std() > 0 else 0
                else:
                    sharpe_ratio = 0
                
                # 构建汇总记录
                summary_row = [
                    date.strftime('%Y-%m-%d'), total_trades, wins, losses,
                    win_rate, total_profit_loss, avg_profit, avg_loss,
                    largest_profit, largest_loss, profit_factor, sharpe_ratio
                ]
                
                summary_data.append(summary_row)
            
            # 保存汇总数据
            with open(self.summary_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'date', 'total_trades', 'winning_trades', 'losing_trades',
                    'win_rate', 'profit_loss', 'average_profit', 'average_loss',
                    'largest_profit', 'largest_loss', 'profit_factor', 'sharpe_ratio'
                ])
                writer.writerows(summary_data)
            
            logger.info("更新交易汇总完成")
            
        except Exception as e:
            logger.error(f"更新交易汇总失败: {str(e)}")
    
    def get_open_trades(self):
        """
        获取未平仓的交易
        
        Returns:
            list: 未平仓的交易列表
        """
        try:
            # 加载交易记录
            trades_df = pd.read_csv(self.trades_file)
            
            # 筛选未平仓的交易
            open_trades = trades_df[trades_df['status'] == 'OPEN']
            
            return open_trades.to_dict('records')
            
        except Exception as e:
            logger.error(f"获取未平仓交易失败: {str(e)}")
            return []
    
    def get_trade_by_id(self, trade_id):
        """
        根据ID获取交易记录
        
        Args:
            trade_id: 交易ID
            
        Returns:
            dict: 交易记录
        """
        try:
            # 加载交易记录
            trades_df = pd.read_csv(self.trades_file)
            
            # 查找交易ID
            trade = trades_df[trades_df['trade_id'] == trade_id]
            
            if len(trade) == 0:
                logger.warning(f"找不到交易ID: {trade_id}")
                return None
            
            return trade.iloc[0].to_dict()
            
        except Exception as e:
            logger.error(f"获取交易记录失败: {str(e)}")
            return None
    
    def get_trades_by_symbol(self, symbol):
        """
        获取指定交易对的交易记录
        
        Args:
            symbol: 交易对
            
        Returns:
            list: 交易记录列表
        """
        try:
            # 加载交易记录
            trades_df = pd.read_csv(self.trades_file)
            
            # 筛选交易对
            symbol_trades = trades_df[trades_df['symbol'] == symbol]
            
            return symbol_trades.to_dict('records')
            
        except Exception as e:
            logger.error(f"获取交易对记录失败: {str(e)}")
            return []
    
    def get_performance_metrics(self, period=None):
        """
        获取交易绩效指标
        
        Args:
            period: 时间周期（'daily', 'weekly', 'monthly', 'all'）
            
        Returns:
            dict: 绩效指标
        """
        try:
            # 加载交易记录
            trades_df = pd.read_csv(self.trades_file)
            
            # 只分析已关闭的交易
            closed_trades = trades_df[trades_df['status'] == 'CLOSED']
            
            if len(closed_trades) == 0:
                logger.info("没有已关闭的交易，无法计算绩效指标")
                return {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'win_rate': 0,
                    'total_profit_loss': 0,
                    'profit_factor': 0,
                    'sharpe_ratio': 0,
                    'average_profit': 0,
                    'average_loss': 0,
                    'average_trade': 0,
                    'max_drawdown': 0
                }
            
            # 转换日期列
            closed_trades['exit_time'] = pd.to_datetime(closed_trades['exit_time'])
            
            # 根据时间周期筛选
            if period:
                now = datetime.now()
                if period == 'daily':
                    start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    closed_trades = closed_trades[closed_trades['exit_time'] >= start_date]
                elif period == 'weekly':
                    start_date = now - pd.Timedelta(days=now.weekday())
                    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    closed_trades = closed_trades[closed_trades['exit_time'] >= start_date]
                elif period == 'monthly':
                    start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    closed_trades = closed_trades[closed_trades['exit_time'] >= start_date]
            
            # 统计盈亏情况
            winning_trades = closed_trades[closed_trades['profit_loss'] > 0]
            losing_trades = closed_trades[closed_trades['profit_loss'] < 0]
            
            total_trades = len(closed_trades)
            wins = len(winning_trades)
            losses = len(losing_trades)
            win_rate = wins / total_trades if total_trades > 0 else 0
            
            # 计算盈亏数据
            total_profit_loss = closed_trades['profit_loss'].sum()
            avg_profit = winning_trades['profit_loss'].mean() if wins > 0 else 0
            avg_loss = losing_trades['profit_loss'].mean() if losses > 0 else 0
            avg_trade = closed_trades['profit_loss'].mean()
            
            # 计算盈亏因子
            profit_factor = abs(winning_trades['profit_loss'].sum() / losing_trades['profit_loss'].sum()) if losses > 0 and losing_trades['profit_loss'].sum() != 0 else float('inf')
            
            # 计算夏普比率
            if total_trades > 1:
                returns = closed_trades['profit_loss_pct'] / 100  # 转换为小数
                sharpe_ratio = returns.mean() / returns.std() if returns.std() > 0 else 0
            else:
                sharpe_ratio = 0
            
            # 计算最大回撤
            closed_trades = closed_trades.sort_values('exit_time')
            closed_trades['cumulative_profit'] = closed_trades['profit_loss'].cumsum()
            closed_trades['cumulative_max'] = closed_trades['cumulative_profit'].cummax()
            closed_trades['drawdown'] = closed_trades['cumulative_max'] - closed_trades['cumulative_profit']
            max_drawdown = closed_trades['drawdown'].max()
            
            # 整理绩效指标
            metrics = {
                'total_trades': total_trades,
                'winning_trades': wins,
                'losing_trades': losses,
                'win_rate': win_rate,
                'total_profit_loss': total_profit_loss,
                'profit_factor': profit_factor,
                'sharpe_ratio': sharpe_ratio,
                'average_profit': avg_profit,
                'average_loss': avg_loss,
                'average_trade': avg_trade,
                'max_drawdown': max_drawdown
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"计算绩效指标失败: {str(e)}")
            return None
    
    def get_trade_history(self, limit=100, offset=0, status=None, symbol=None):
        """
        获取交易历史
        
        Args:
            limit: 返回记录数量限制
            offset: 起始偏移
            status: 交易状态过滤
            symbol: 交易对过滤
            
        Returns:
            list: 交易记录列表
        """
        try:
            # 加载交易记录
            trades_df = pd.read_csv(self.trades_file)
            
            # 应用过滤器
            if status:
                trades_df = trades_df[trades_df['status'] == status]
            
            if symbol:
                trades_df = trades_df[trades_df['symbol'] == symbol]
            
            # 按入场时间排序
            trades_df = trades_df.sort_values('entry_time', ascending=False)
            
            # 应用分页
            if offset < len(trades_df):
                end = min(offset + limit, len(trades_df))
                trades_df = trades_df.iloc[offset:end]
            else:
                trades_df = pd.DataFrame()
            
            return trades_df.to_dict('records')
            
        except Exception as e:
            logger.error(f"获取交易历史失败: {str(e)}")
            return [] 