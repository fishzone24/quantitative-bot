import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
from exchanges.exchange_client import ExchangeClient

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('trading_engine')

class TradingEngine:
    """交易引擎类"""
    
    def __init__(self, config=None):
        """
        初始化交易引擎
        
        Args:
            config: 交易配置参数
        """
        self.config = config or {}
        self.exchange_name = os.getenv("EXCHANGE", "binance")
        self.exchange = ExchangeClient(self.exchange_name)
        
        # 交易参数
        self.symbols = self.config.get("symbols", ["BTC/USDT"])
        self.timeframes = self.config.get("timeframes", ["1h"])
        self.take_profit = float(os.getenv("TAKE_PROFIT", "2.0"))
        self.stop_loss = float(os.getenv("STOP_LOSS", "3.0"))
        
        logger.info("初始化交易引擎")
    
    def execute_trade(self, symbol: str, side: str, quantity: float, order_type: str = "MARKET") -> Dict:
        """
        执行交易
        
        Args:
            symbol: 交易对名称
            side: 交易方向，BUY或SELL
            quantity: 交易数量
            order_type: 订单类型，默认为市价单
            
        Returns:
            Dict: 交易结果
        """
        try:
            # 检查余额
            balance = self.exchange.get_balance()
            if balance < quantity:
                logger.error(f"余额不足: {balance} < {quantity}")
                return {"status": "ERROR", "message": "余额不足"}
            
            # 下单
            order = self.exchange.place_order(symbol, side, quantity, order_type)
            if not order:
                return {"status": "ERROR", "message": "下单失败"}
            
            # 设置止盈止损
            if side == "BUY":
                self._set_take_profit_stop_loss(symbol, order['orderId'], order['price'])
            
            return {"status": "SUCCESS", "order": order}
            
        except Exception as e:
            logger.error(f"执行交易失败: {str(e)}")
            return {"status": "ERROR", "message": str(e)}
    
    def _set_take_profit_stop_loss(self, symbol: str, order_id: str, entry_price: float):
        """
        设置止盈止损
        
        Args:
            symbol: 交易对名称
            order_id: 订单ID
            entry_price: 入场价格
        """
        try:
            # 计算止盈止损价格
            take_profit_price = entry_price * (1 + self.take_profit / 100)
            stop_loss_price = entry_price * (1 - self.stop_loss / 100)
            
            # 设置止盈单
            self.exchange.place_order(
                symbol=symbol,
                side="SELL",
                quantity=self._get_position_size(symbol),
                order_type="LIMIT",
                price=take_profit_price
            )
            
            # 设置止损单
            self.exchange.place_order(
                symbol=symbol,
                side="SELL",
                quantity=self._get_position_size(symbol),
                order_type="STOP_MARKET",
                price=stop_loss_price
            )
            
            logger.info(f"设置止盈止损成功 - 止盈: {take_profit_price}, 止损: {stop_loss_price}")
            
        except Exception as e:
            logger.error(f"设置止盈止损失败: {str(e)}")
    
    def _get_position_size(self, symbol: str) -> float:
        """
        获取持仓数量
        
        Args:
            symbol: 交易对名称
            
        Returns:
            float: 持仓数量
        """
        try:
            # 获取账户余额
            balance = self.exchange.get_balance()
            
            # 获取当前价格
            current_price = self.exchange.get_symbol_price(symbol)
            
            # 计算可交易数量
            position_size = balance / current_price
            
            return position_size
            
        except Exception as e:
            logger.error(f"获取持仓数量失败: {str(e)}")
            return 0.0
    
    def cancel_all_orders(self, symbol: str) -> bool:
        """
        取消所有订单
        
        Args:
            symbol: 交易对名称
            
        Returns:
            bool: 是否取消成功
        """
        try:
            # 获取所有未完成订单
            orders = self.exchange.get_open_orders(symbol)
            
            # 取消每个订单
            for order in orders:
                self.exchange.cancel_order(symbol, order['orderId'])
            
            logger.info(f"取消{symbol}所有订单成功")
            return True
            
        except Exception as e:
            logger.error(f"取消所有订单失败: {str(e)}")
            return False
    
    def get_trade_history(self, symbol: str, limit: int = 100) -> List[Dict]:
        """
        获取交易历史
        
        Args:
            symbol: 交易对名称
            limit: 获取数量
            
        Returns:
            List[Dict]: 交易历史列表
        """
        try:
            return self.exchange.get_trade_history(symbol, limit)
            
        except Exception as e:
            logger.error(f"获取交易历史失败: {str(e)}")
            return [] 