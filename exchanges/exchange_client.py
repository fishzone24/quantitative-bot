import os
import logging
import ccxt
from binance.client import Client
from binance.exceptions import BinanceAPIException
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import time
from decimal import Decimal

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('exchange_client')

class ExchangeClient:
    """交易所客户端类"""
    
    def __init__(self, exchange_name: str = "binance"):
        """
        初始化交易所客户端
        
        Args:
            exchange_name: 交易所名称，默认为binance
        """
        self.exchange_name = exchange_name.lower()
        self.api_key = os.getenv(f"{exchange_name.upper()}_API_KEY")
        self.api_secret = os.getenv(f"{exchange_name.upper()}_API_SECRET")
        
        # 初始化交易所API
        self._init_exchange()
        
        logger.info(f"初始化{exchange_name}交易所客户端")
    
    def _init_exchange(self):
        """初始化交易所API"""
        try:
            if self.exchange_name == "binance":
                # 初始化Binance API
                self.client = Client(self.api_key, self.api_secret)
                self.exchange = ccxt.binance({
                    'apiKey': self.api_key,
                    'secret': self.api_secret,
                    'enableRateLimit': True
                })
            elif self.exchange_name == "okx":
                # 动态导入OKX模块
                from okx import Account, Market, Trade
                self.account_api = Account()
                self.market_api = Market()
                self.trade_api = Trade()
                self.exchange = ccxt.okx({
                    'apiKey': self.api_key,
                    'secret': self.api_secret,
                    'password': os.getenv('OKX_PASSPHRASE'),
                    'enableRateLimit': True
                })
            else:
                raise ValueError(f"不支持的交易所: {self.exchange_name}")
            
            logger.info(f"{self.exchange_name} API初始化成功")
            
        except Exception as e:
            logger.error(f"初始化{self.exchange_name} API失败: {str(e)}")
            raise
    
    def get_balance(self, asset: str = "USDT") -> float:
        """
        获取账户余额
        
        Args:
            asset: 资产类型，默认为USDT
            
        Returns:
            float: 可用余额
        """
        try:
            if self.exchange_name == "binance":
                balance = self.client.get_asset_balance(asset=asset)
                return float(balance['free'])
            elif self.exchange_name == "okx":
                balance = self.account_api.get_account_balance()
                for item in balance['data']:
                    if item['ccy'] == asset:
                        return float(item['availBal'])
                return 0.0
            else:
                raise ValueError(f"不支持的交易所: {self.exchange_name}")
                
        except Exception as e:
            logger.error(f"获取{asset}余额失败: {str(e)}")
            return 0.0
    
    def get_symbol_price(self, symbol: str) -> float:
        """
        获取交易对当前价格
        
        Args:
            symbol: 交易对名称
            
        Returns:
            float: 当前价格
        """
        try:
            if self.exchange_name == "binance":
                ticker = self.client.get_symbol_ticker(symbol=symbol)
                return float(ticker['price'])
            elif self.exchange_name == "okx":
                ticker = self.market_api.get_ticker(instId=symbol)
                return float(ticker['data'][0]['last'])
            else:
                raise ValueError(f"不支持的交易所: {self.exchange_name}")
                
        except Exception as e:
            logger.error(f"获取{symbol}价格失败: {str(e)}")
            return 0.0
    
    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> pd.DataFrame:
        """
        获取K线数据
        
        Args:
            symbol: 交易对名称
            interval: K线间隔
            limit: 获取数量
            
        Returns:
            pd.DataFrame: K线数据
        """
        try:
            if self.exchange_name == "binance":
                klines = self.client.get_klines(
                    symbol=symbol,
                    interval=interval,
                    limit=limit
                )
                df = pd.DataFrame(klines, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                    'taker_buy_quote', 'ignore'
                ])
            elif self.exchange_name == "okx":
                klines = self.market_api.get_candlesticks(
                    instId=symbol,
                    bar=interval,
                    limit=str(limit)
                )
                df = pd.DataFrame(klines['data'], columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'volCcy', 'volCcyQuote', 'confirm'
                ])
            else:
                raise ValueError(f"不支持的交易所: {self.exchange_name}")
            
            # 转换数据类型
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            return df
            
        except Exception as e:
            logger.error(f"获取{symbol} K线数据失败: {str(e)}")
            return pd.DataFrame()
    
    def place_order(self, symbol: str, side: str, quantity: float, order_type: str = "MARKET") -> Dict:
        """
        下单
        
        Args:
            symbol: 交易对名称
            side: 交易方向，BUY或SELL
            quantity: 交易数量
            order_type: 订单类型，默认为市价单
            
        Returns:
            Dict: 订单信息
        """
        try:
            if self.exchange_name == "binance":
                order = self.client.create_order(
                    symbol=symbol,
                    side=side,
                    type=order_type,
                    quantity=quantity
                )
            elif self.exchange_name == "okx":
                order = self.trade_api.place_order(
                    instId=symbol,
                    tdMode='cross',
                    side=side.lower(),
                    ordType=order_type.lower(),
                    sz=str(quantity)
                )
            else:
                raise ValueError(f"不支持的交易所: {self.exchange_name}")
            
            logger.info(f"下单成功: {order}")
            return order
            
        except Exception as e:
            logger.error(f"下单失败: {str(e)}")
            return {}
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """
        取消订单
        
        Args:
            symbol: 交易对名称
            order_id: 订单ID
            
        Returns:
            bool: 是否取消成功
        """
        try:
            if self.exchange_name == "binance":
                self.client.cancel_order(symbol=symbol, orderId=order_id)
            elif self.exchange_name == "okx":
                self.trade_api.cancel_order(
                    instId=symbol,
                    ordId=order_id
                )
            else:
                raise ValueError(f"不支持的交易所: {self.exchange_name}")
            
            logger.info(f"取消订单成功: {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"取消订单失败: {str(e)}")
            return False
    
    def get_order_status(self, symbol: str, order_id: str) -> Dict:
        """
        获取订单状态
        
        Args:
            symbol: 交易对名称
            order_id: 订单ID
            
        Returns:
            Dict: 订单状态信息
        """
        try:
            if self.exchange_name == "binance":
                order = self.client.get_order(symbol=symbol, orderId=order_id)
            elif self.exchange_name == "okx":
                order = self.trade_api.get_order(
                    instId=symbol,
                    ordId=order_id
                )
            else:
                raise ValueError(f"不支持的交易所: {self.exchange_name}")
            
            return order
            
        except Exception as e:
            logger.error(f"获取订单状态失败: {str(e)}")
            return {}
    
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
            if self.exchange_name == "binance":
                trades = self.client.get_my_trades(symbol=symbol, limit=limit)
            elif self.exchange_name == "okx":
                trades = self.trade_api.get_orders_history(
                    instId=symbol,
                    limit=str(limit)
                )
            else:
                raise ValueError(f"不支持的交易所: {self.exchange_name}")
            
            return trades
            
        except Exception as e:
            logger.error(f"获取交易历史失败: {str(e)}")
            return []
    
    def get_open_orders(self, symbol: str) -> List[Dict]:
        """
        获取未完成订单
        
        Args:
            symbol: 交易对名称
            
        Returns:
            List[Dict]: 未完成订单列表
        """
        try:
            if self.exchange_name == "binance":
                orders = self.client.get_open_orders(symbol=symbol)
            elif self.exchange_name == "okx":
                orders = self.trade_api.get_order_list(
                    instId=symbol,
                    state="live"
                )
                if 'data' in orders:
                    return orders['data']
                return []
            else:
                raise ValueError(f"不支持的交易所: {self.exchange_name}")
            
            return orders
            
        except Exception as e:
            logger.error(f"获取未完成订单失败: {str(e)}")
            return [] 