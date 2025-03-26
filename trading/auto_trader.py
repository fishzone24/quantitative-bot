import os
import logging
import time
from datetime import datetime
import math
import json

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('auto_trader')

class AutoTrader:
    """自动交易类"""
    
    def __init__(self, exchange_client, trade_recorder, config=None):
        """
        初始化自动交易器
        
        Args:
            exchange_client: 交易所客户端
            trade_recorder: 交易记录器
            config: 配置参数
        """
        self.exchange_client = exchange_client
        self.trade_recorder = trade_recorder
        self.config = config or {}
        
        # 交易参数
        self.max_trade_size = float(self.config.get("MAX_TRADE_SIZE", 10))
        self.stop_loss_pct = float(self.config.get("STOP_LOSS", 3.0))
        self.take_profit_pct = float(self.config.get("TAKE_PROFIT", 2.0))
        self.use_dynamic_sl = self.config.get("USE_DYNAMIC_SL", True)
        
        # 追踪活跃交易
        self.active_trades = {}
        
        # 加载已有的未平仓交易
        self._load_open_trades()
        
        logger.info("初始化自动交易器")
        logger.info(f"交易参数: 最大交易量={self.max_trade_size}, 止损={self.stop_loss_pct}%, 止盈={self.take_profit_pct}%, 动态止损={self.use_dynamic_sl}")
    
    def _load_open_trades(self):
        """加载未平仓的交易"""
        try:
            open_trades = self.trade_recorder.get_open_trades()
            
            for trade in open_trades:
                trade_id = trade['trade_id']
                symbol = trade['symbol']
                side = trade['side']
                entry_price = float(trade['entry_price'])
                quantity = float(trade['quantity'])
                
                # 加载风险管理数据
                risk_data = self._load_risk_data(trade_id)
                stop_loss = risk_data.get('stop_loss')
                take_profit = risk_data.get('take_profit')
                
                # 将交易添加到活跃交易字典
                self.active_trades[trade_id] = {
                    'symbol': symbol,
                    'side': side,
                    'entry_price': entry_price,
                    'quantity': quantity,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'highest_price': entry_price,  # 用于追踪最高价格，用于动态止损
                    'lowest_price': entry_price,   # 用于追踪最低价格，用于动态止损
                }
            
            logger.info(f"已加载 {len(self.active_trades)} 个未平仓交易")
            
        except Exception as e:
            logger.error(f"加载未平仓交易失败: {str(e)}")
    
    def _load_risk_data(self, trade_id):
        """
        加载交易的风险管理数据
        
        Args:
            trade_id: 交易ID
            
        Returns:
            dict: 风险管理数据
        """
        try:
            # 风险管理记录文件
            risk_file = os.path.join("data/trade_records/risk_management", f"{trade_id}.json")
            
            if os.path.exists(risk_file):
                with open(risk_file, 'r') as f:
                    return json.load(f)
            
            return {}
            
        except Exception as e:
            logger.error(f"加载风险管理数据失败: {str(e)}")
            return {}
    
    def execute_trade(self, symbol, signal, price, confidence=None, ai_analysis=None):
        """
        执行交易
        
        Args:
            symbol: 交易对
            signal: 交易信号 (buy/sell/neutral)
            price: 当前价格
            confidence: 信号置信度
            ai_analysis: AI分析结果
            
        Returns:
            dict: 交易结果
        """
        if signal.lower() not in ['buy', 'sell']:
            logger.info(f"{symbol} 信号为中性或无效 ({signal})，不执行交易")
            return {"status": "ignored", "reason": "中性信号"}
        
        # 检查是否有足够的置信度
        if confidence is not None:
            min_confidence = 70  # 最小执行置信度
            if confidence < min_confidence:
                logger.info(f"{symbol} 信号置信度不足 ({confidence}% < {min_confidence}%)，不执行交易")
                return {"status": "ignored", "reason": "置信度不足"}
        
        try:
            # 检查余额
            balance = self.exchange_client.get_balance()
            
            # 确定交易方向和使用的货币
            side = signal.lower()
            base_currency, quote_currency = symbol.split('/')
            
            # 买入信号，检查 quote_currency 余额
            if side == 'buy':
                currency_to_check = quote_currency
            # 卖出信号，检查 base_currency 余额
            else:
                currency_to_check = base_currency
                
            if currency_to_check not in balance or balance[currency_to_check]['free'] <= 0:
                logger.warning(f"余额不足: {currency_to_check}")
                return {"status": "failed", "reason": "余额不足"}
            
            # 计算交易数量
            quantity = self._calculate_trade_size(symbol, side, price, balance)
            
            if quantity <= 0:
                logger.warning(f"计算得到的交易数量无效: {quantity}")
                return {"status": "failed", "reason": "交易数量无效"}
            
            # 计算止损止盈价格
            stop_loss, take_profit = self._calculate_stop_loss_take_profit(side, price)
            
            # 执行订单
            order_result = self.exchange_client.place_order(
                symbol=symbol,
                order_type="market",
                side=side,
                amount=quantity
            )
            
            if order_result['status'] in ['TEST_SUCCESS', 'SUCCESS']:
                # 记录交易
                trade_notes = f"AI置信度: {confidence}%, 策略: 自动交易" if confidence else "策略: 自动交易"
                
                if ai_analysis:
                    trade_notes += f"\nAI分析: {ai_analysis.get('market_overview', '')}"
                
                trade_id = self.trade_recorder.record_trade_entry(
                    symbol=symbol,
                    side=side,
                    entry_price=price,
                    quantity=quantity,
                    strategy="AI_AUTO" if ai_analysis else "TECHNICAL",
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    tags=["auto_trade"],
                    notes=trade_notes
                )
                
                # 添加到活跃交易
                if trade_id:
                    self.active_trades[trade_id] = {
                        'symbol': symbol,
                        'side': side,
                        'entry_price': price,
                        'quantity': quantity,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'highest_price': price,  # 用于追踪最高价格
                        'lowest_price': price,   # 用于追踪最低价格
                    }
                
                return {
                    "status": "success",
                    "trade_id": trade_id,
                    "symbol": symbol,
                    "side": side,
                    "price": price,
                    "quantity": quantity,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit
                }
            else:
                logger.error(f"下单失败: {order_result}")
                return {"status": "failed", "reason": f"下单失败: {order_result.get('message', '未知错误')}"}
                
        except Exception as e:
            logger.error(f"执行交易失败: {str(e)}")
            return {"status": "error", "reason": str(e)}
    
    def _calculate_trade_size(self, symbol, side, price, balance):
        """
        计算交易数量
        
        Args:
            symbol: 交易对
            side: 买入/卖出
            price: 当前价格
            balance: 账户余额
            
        Returns:
            float: 交易数量
        """
        try:
            base_currency, quote_currency = symbol.split('/')
            
            # 确定使用哪个货币的余额
            if side == 'buy':
                currency = quote_currency
                available_balance = balance[currency]['free']
                # 买入时，用余额/价格计算数量
                max_quantity = available_balance / price
            else:  # sell
                currency = base_currency
                available_balance = balance[currency]['free']
                # 卖出时，直接使用base货币的余额
                max_quantity = available_balance
            
            # 使用配置中的最大交易量和余额中可用的最大量之间的较小值
            quantity = min(self.max_trade_size, max_quantity)
            
            # 向下取整到合适的精度
            precision = 6 if price < 100 else 4  # 简单的精度调整规则
            quantity = math.floor(quantity * 10**precision) / 10**precision
            
            return quantity
            
        except Exception as e:
            logger.error(f"计算交易数量失败: {str(e)}")
            return 0
    
    def _calculate_stop_loss_take_profit(self, side, price):
        """
        计算止损和止盈价格
        
        Args:
            side: 买入/卖出
            price: 当前价格
            
        Returns:
            tuple: (止损价格, 止盈价格)
        """
        if side == 'buy':
            stop_loss = price * (1 - self.stop_loss_pct / 100)
            take_profit = price * (1 + self.take_profit_pct / 100)
        else:  # sell
            stop_loss = price * (1 + self.stop_loss_pct / 100)
            take_profit = price * (1 - self.take_profit_pct / 100)
        
        return stop_loss, take_profit
    
    def check_open_positions(self):
        """
        检查未平仓头寸，执行止损止盈
        
        Returns:
            list: 执行的操作列表
        """
        if not self.active_trades:
            return []
        
        actions_taken = []
        trades_to_remove = []
        
        for trade_id, trade in self.active_trades.items():
            symbol = trade['symbol']
            side = trade['side']
            entry_price = trade['entry_price']
            stop_loss = trade['stop_loss']
            take_profit = trade['take_profit']
            
            # 获取当前价格
            ticker = self.exchange_client.get_ticker(symbol)
            if not ticker:
                logger.warning(f"无法获取 {symbol} 的价格数据")
                continue
                
            current_price = ticker['last']
            
            # 更新最高价和最低价
            trade['highest_price'] = max(trade['highest_price'], current_price)
            trade['lowest_price'] = min(trade['lowest_price'], current_price)
            
            # 计算是否触发止损或止盈
            exit_reason = None
            
            if side == 'buy':
                # 买入止损
                if current_price <= stop_loss:
                    exit_reason = "触发止损"
                # 买入止盈
                elif current_price >= take_profit:
                    exit_reason = "触发止盈"
                # 动态止损
                elif self.use_dynamic_sl and current_price < trade['highest_price'] * (1 - self.stop_loss_pct / 200):
                    exit_reason = "触发动态止损"
            else:  # sell
                # 卖出止损
                if current_price >= stop_loss:
                    exit_reason = "触发止损"
                # 卖出止盈
                elif current_price <= take_profit:
                    exit_reason = "触发止盈"
                # 动态止损
                elif self.use_dynamic_sl and current_price > trade['lowest_price'] * (1 + self.stop_loss_pct / 200):
                    exit_reason = "触发动态止损"
            
            # 如果需要平仓
            if exit_reason:
                # 执行平仓
                close_side = 'sell' if side == 'buy' else 'buy'
                close_result = self.exchange_client.place_order(
                    symbol=symbol,
                    order_type="market",
                    side=close_side,
                    amount=trade['quantity']
                )
                
                if close_result['status'] in ['TEST_SUCCESS', 'SUCCESS']:
                    # 记录交易出场
                    self.trade_recorder.record_trade_exit(
                        trade_id=trade_id,
                        exit_price=current_price,
                        notes=exit_reason
                    )
                    
                    logger.info(f"平仓成功: {trade_id} {symbol} @ {current_price} ({exit_reason})")
                    
                    actions_taken.append({
                        "trade_id": trade_id,
                        "symbol": symbol,
                        "action": "close",
                        "price": current_price,
                        "reason": exit_reason
                    })
                    
                    # 标记此交易待从活跃交易中移除
                    trades_to_remove.append(trade_id)
                else:
                    logger.error(f"平仓失败: {trade_id} {symbol} @ {current_price} - {close_result}")
        
        # 移除已平仓的交易
        for trade_id in trades_to_remove:
            self.active_trades.pop(trade_id, None)
        
        return actions_taken
    
    def update_stop_loss(self, trade_id, new_stop_loss):
        """
        更新止损价格
        
        Args:
            trade_id: 交易ID
            new_stop_loss: 新的止损价格
            
        Returns:
            bool: 是否成功
        """
        if trade_id not in self.active_trades:
            logger.warning(f"交易ID不存在: {trade_id}")
            return False
        
        try:
            # 更新内存中的止损价格
            self.active_trades[trade_id]['stop_loss'] = new_stop_loss
            
            # 更新风险管理文件
            risk_data = self._load_risk_data(trade_id)
            risk_data['stop_loss'] = new_stop_loss
            risk_data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 保存风险管理信息
            risk_dir = os.path.join("data/trade_records/risk_management")
            os.makedirs(risk_dir, exist_ok=True)
            risk_file = os.path.join(risk_dir, f"{trade_id}.json")
            
            with open(risk_file, 'w') as f:
                json.dump(risk_data, f, indent=2)
                
            logger.info(f"已更新止损价格: {trade_id} -> {new_stop_loss}")
            return True
            
        except Exception as e:
            logger.error(f"更新止损价格失败: {str(e)}")
            return False
    
    def close_all_positions(self, reason="手动关闭"):
        """
        关闭所有头寸
        
        Args:
            reason: 关闭原因
            
        Returns:
            list: 关闭的交易列表
        """
        if not self.active_trades:
            return []
        
        closed_trades = []
        
        for trade_id, trade in list(self.active_trades.items()):
            symbol = trade['symbol']
            side = trade['side']
            quantity = trade['quantity']
            
            # 确定平仓方向
            close_side = 'sell' if side == 'buy' else 'buy'
            
            # 获取当前价格
            ticker = self.exchange_client.get_ticker(symbol)
            if not ticker:
                logger.warning(f"无法获取 {symbol} 的价格数据")
                continue
                
            current_price = ticker['last']
            
            # 执行平仓
            close_result = self.exchange_client.place_order(
                symbol=symbol,
                order_type="market",
                side=close_side,
                amount=quantity
            )
            
            if close_result['status'] in ['TEST_SUCCESS', 'SUCCESS']:
                # 记录交易出场
                self.trade_recorder.record_trade_exit(
                    trade_id=trade_id,
                    exit_price=current_price,
                    notes=reason
                )
                
                logger.info(f"平仓成功: {trade_id} {symbol} @ {current_price} ({reason})")
                
                closed_trades.append({
                    "trade_id": trade_id,
                    "symbol": symbol,
                    "price": current_price,
                    "reason": reason
                })
                
                # 从活跃交易中移除
                self.active_trades.pop(trade_id, None)
            else:
                logger.error(f"平仓失败: {trade_id} {symbol} @ {current_price} - {close_result}")
        
        return closed_trades 