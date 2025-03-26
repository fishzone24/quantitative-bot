import os
import ccxt
import logging
from binance.client import Client as BinanceClient
from okx import Account, Market, Trade

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('exchange_client')

class ExchangeClientFactory:
    """交易所客户端工厂类"""
    
    @staticmethod
    def create_client(exchange_name="binance"):
        """
        创建交易所客户端实例
        
        Args:
            exchange_name: 交易所名称 (binance, okx)
            
        Returns:
            ExchangeClient实例
        """
        exchange_name = exchange_name.lower()
        
        if exchange_name == "binance":
            return BinanceExchangeClient()
        elif exchange_name == "okx":
            return OKXExchangeClient()
        else:
            raise ValueError(f"不支持的交易所: {exchange_name}")


class ExchangeClient:
    """交易所客户端基类"""
    
    def __init__(self):
        self.client = None
        self.name = None
        self.trade_mode = os.getenv("TRADE_MODE", "test")
        logger.info(f"初始化交易所客户端，交易模式: {self.trade_mode}")
    
    def get_ticker(self, symbol):
        """获取交易对当前行情"""
        raise NotImplementedError("子类必须实现此方法")
        
    def get_historical_data(self, symbol, timeframe='1h', limit=100):
        """获取历史K线数据"""
        raise NotImplementedError("子类必须实现此方法")
    
    def place_order(self, symbol, order_type, side, amount, price=None):
        """下单"""
        raise NotImplementedError("子类必须实现此方法")
    
    def cancel_order(self, order_id, symbol):
        """取消订单"""
        raise NotImplementedError("子类必须实现此方法")
    
    def get_balance(self, currency=None):
        """获取账户余额"""
        raise NotImplementedError("子类必须实现此方法")
    
    def get_order_status(self, order_id, symbol):
        """获取订单状态"""
        raise NotImplementedError("子类必须实现此方法")


class BinanceExchangeClient(ExchangeClient):
    """币安交易所客户端"""
    
    def __init__(self):
        super().__init__()
        self.name = "binance"
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_secret = os.getenv("BINANCE_API_SECRET")
        
        if not self.api_key or not self.api_secret:
            logger.error("未设置币安API密钥")
            raise ValueError("请在.env文件中设置BINANCE_API_KEY和BINANCE_API_SECRET")
        
        # 初始化币安客户端
        self.client = BinanceClient(self.api_key, self.api_secret)
        # 初始化CCXT客户端(用于获取历史数据)
        self.ccxt_client = ccxt.binance({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True
        })
        
        # 设置测试模式
        if self.trade_mode == "test":
            self.ccxt_client.set_sandbox_mode(True)
            logger.info("币安客户端已设置为测试模式")
        
        logger.info("币安交易所客户端初始化完成")
    
    def get_ticker(self, symbol):
        """获取交易对当前行情"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol.replace("/", ""))
            return {
                'symbol': symbol,
                'last': float(ticker['price']),
                'timestamp': self.client.get_server_time()['serverTime']
            }
        except Exception as e:
            logger.error(f"获取{symbol}行情失败: {str(e)}")
            return None
    
    def get_historical_data(self, symbol, timeframe='1h', limit=100):
        """获取历史K线数据"""
        try:
            # 使用CCXT获取历史数据，格式统一
            ohlcv = self.ccxt_client.fetch_ohlcv(
                symbol=symbol, 
                timeframe=timeframe, 
                limit=limit
            )
            return ohlcv
        except Exception as e:
            logger.error(f"获取{symbol}历史数据失败: {str(e)}")
            return []
    
    def place_order(self, symbol, order_type, side, amount, price=None):
        """下单"""
        try:
            # 转换为币安格式
            symbol_formatted = symbol.replace("/", "")
            side = side.upper()
            order_type = order_type.upper()
            
            if self.trade_mode == "test":
                # 测试模式下使用测试接口
                if order_type == "LIMIT":
                    response = self.client.create_test_order(
                        symbol=symbol_formatted,
                        side=side,
                        type=order_type,
                        timeInForce="GTC",
                        quantity=amount,
                        price=price
                    )
                else:
                    response = self.client.create_test_order(
                        symbol=symbol_formatted,
                        side=side,
                        type=order_type,
                        quantity=amount
                    )
                # 测试接口只返回成功响应，没有订单ID
                return {"status": "TEST_SUCCESS", "order_id": "test_order_id"}
            else:
                # 实盘模式
                if order_type == "LIMIT":
                    response = self.client.create_order(
                        symbol=symbol_formatted,
                        side=side,
                        type=order_type,
                        timeInForce="GTC",
                        quantity=amount,
                        price=price
                    )
                else:
                    response = self.client.create_order(
                        symbol=symbol_formatted,
                        side=side,
                        type=order_type,
                        quantity=amount
                    )
                return {
                    "status": response['status'],
                    "order_id": response['orderId']
                }
                
        except Exception as e:
            logger.error(f"下单失败: {str(e)}")
            return {"status": "ERROR", "message": str(e)}
    
    def cancel_order(self, order_id, symbol):
        """取消订单"""
        try:
            if self.trade_mode == "test":
                return {"status": "TEST_SUCCESS"}
                
            symbol_formatted = symbol.replace("/", "")
            response = self.client.cancel_order(
                symbol=symbol_formatted,
                orderId=order_id
            )
            return {"status": "SUCCESS", "order_id": response['orderId']}
        except Exception as e:
            logger.error(f"取消订单失败: {str(e)}")
            return {"status": "ERROR", "message": str(e)}
    
    def get_balance(self, currency=None):
        """获取账户余额"""
        try:
            if self.trade_mode == "test":
                # 测试模式返回模拟数据
                return {
                    "USDT": {"free": 10000.0, "used": 0.0, "total": 10000.0},
                    "BTC": {"free": 1.0, "used": 0.0, "total": 1.0},
                    "ETH": {"free": 10.0, "used": 0.0, "total": 10.0},
                }
                
            account = self.client.get_account()
            balances = {}
            
            for balance in account['balances']:
                asset = balance['asset']
                if currency and asset != currency:
                    continue
                balances[asset] = {
                    "free": float(balance['free']),
                    "used": float(balance['locked']),
                    "total": float(balance['free']) + float(balance['locked'])
                }
                
            return balances if not currency else balances.get(currency)
        except Exception as e:
            logger.error(f"获取余额失败: {str(e)}")
            return {}
    
    def get_order_status(self, order_id, symbol):
        """获取订单状态"""
        try:
            if self.trade_mode == "test":
                return {"status": "TEST_SUCCESS"}
                
            symbol_formatted = symbol.replace("/", "")
            order = self.client.get_order(
                symbol=symbol_formatted,
                orderId=order_id
            )
            return {
                "order_id": order['orderId'],
                "status": order['status'],
                "symbol": symbol,
                "price": float(order['price']),
                "amount": float(order['origQty']),
                "filled": float(order['executedQty']),
                "side": order['side'].lower()
            }
        except Exception as e:
            logger.error(f"获取订单状态失败: {str(e)}")
            return {"status": "ERROR", "message": str(e)}


class OKXExchangeClient(ExchangeClient):
    """OKX交易所客户端"""
    
    def __init__(self):
        super().__init__()
        self.name = "okx"
        self.api_key = os.getenv("OKX_API_KEY")
        self.api_secret = os.getenv("OKX_API_SECRET")
        self.passphrase = os.getenv("OKX_PASSPHRASE")
        
        if not self.api_key or not self.api_secret or not self.passphrase:
            logger.error("未设置OKX API密钥")
            raise ValueError("请在.env文件中设置OKX_API_KEY, OKX_API_SECRET和OKX_PASSPHRASE")
        
        # 设置测试模式
        flag = "0"  # 实盘模式
        if self.trade_mode == "test":
            flag = "1"  # 测试模式
            
        # 初始化OKX API客户端
        self.account_api = Account(
            api_key=self.api_key,
            api_secret_key=self.api_secret,
            passphrase=self.passphrase,
            flag=flag
        )
        self.market_api = Market(
            api_key=self.api_key,
            api_secret_key=self.api_secret,
            passphrase=self.passphrase,
            flag=flag
        )
        self.trade_api = Trade(
            api_key=self.api_key,
            api_secret_key=self.api_secret,
            passphrase=self.passphrase,
            flag=flag
        )
        
        # 初始化CCXT客户端(用于获取历史数据)
        self.ccxt_client = ccxt.okx({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'password': self.passphrase,
            'enableRateLimit': True
        })
        
        if self.trade_mode == "test":
            self.ccxt_client.set_sandbox_mode(True)
            logger.info("OKX客户端已设置为测试模式")
        
        logger.info("OKX交易所客户端初始化完成")
    
    def get_ticker(self, symbol):
        """获取交易对当前行情"""
        try:
            # 转换为OKX格式
            symbol_formatted = symbol.replace("/", "-")
            result = self.market_api.get_ticker(instId=symbol_formatted)
            
            if result['code'] != '0':
                logger.error(f"获取{symbol}行情失败: {result['msg']}")
                return None
                
            ticker_data = result['data'][0]
            return {
                'symbol': symbol,
                'last': float(ticker_data['last']),
                'timestamp': int(ticker_data['ts'])
            }
        except Exception as e:
            logger.error(f"获取{symbol}行情失败: {str(e)}")
            return None
    
    def get_historical_data(self, symbol, timeframe='1h', limit=100):
        """获取历史K线数据"""
        try:
            # 使用CCXT获取历史数据，格式统一
            ohlcv = self.ccxt_client.fetch_ohlcv(
                symbol=symbol, 
                timeframe=timeframe, 
                limit=limit
            )
            return ohlcv
        except Exception as e:
            logger.error(f"获取{symbol}历史数据失败: {str(e)}")
            return []
    
    def place_order(self, symbol, order_type, side, amount, price=None):
        """下单"""
        try:
            # 转换为OKX格式
            symbol_formatted = symbol.replace("/", "-")
            side_map = {"buy": "buy", "sell": "sell"}
            order_type_map = {
                "limit": "limit",
                "market": "market"
            }
            
            params = {
                "instId": symbol_formatted,
                "tdMode": "cash",  # 现货交易
                "side": side_map.get(side.lower(), side),
                "ordType": order_type_map.get(order_type.lower(), order_type),
                "sz": str(amount)
            }
            
            if order_type.lower() == "limit" and price:
                params["px"] = str(price)
                
            result = self.trade_api.place_order(**params)
            
            if result['code'] != '0':
                logger.error(f"下单失败: {result['msg']}")
                return {"status": "ERROR", "message": result['msg']}
            
            return {
                "status": "SUCCESS",
                "order_id": result['data'][0]['ordId']
            }
        except Exception as e:
            logger.error(f"下单失败: {str(e)}")
            return {"status": "ERROR", "message": str(e)}
    
    def cancel_order(self, order_id, symbol):
        """取消订单"""
        try:
            symbol_formatted = symbol.replace("/", "-")
            result = self.trade_api.cancel_order(
                instId=symbol_formatted,
                ordId=order_id
            )
            
            if result['code'] != '0':
                logger.error(f"取消订单失败: {result['msg']}")
                return {"status": "ERROR", "message": result['msg']}
                
            return {"status": "SUCCESS", "order_id": order_id}
        except Exception as e:
            logger.error(f"取消订单失败: {str(e)}")
            return {"status": "ERROR", "message": str(e)}
    
    def get_balance(self, currency=None):
        """获取账户余额"""
        try:
            if self.trade_mode == "test":
                # 测试模式返回模拟数据
                return {
                    "USDT": {"free": 10000.0, "used": 0.0, "total": 10000.0},
                    "BTC": {"free": 1.0, "used": 0.0, "total": 1.0},
                    "ETH": {"free": 10.0, "used": 0.0, "total": 10.0},
                }
                
            result = self.account_api.get_balance(
                ccy=currency
            )
            
            if result['code'] != '0':
                logger.error(f"获取余额失败: {result['msg']}")
                return {}
                
            balances = {}
            for balance in result['data'][0]['details']:
                asset = balance['ccy']
                balances[asset] = {
                    "free": float(balance['availBal']),
                    "used": float(balance['frozenBal']),
                    "total": float(balance['cashBal'])
                }
                
            return balances if not currency else balances.get(currency, {})
        except Exception as e:
            logger.error(f"获取余额失败: {str(e)}")
            return {}
    
    def get_order_status(self, order_id, symbol):
        """获取订单状态"""
        try:
            symbol_formatted = symbol.replace("/", "-")
            result = self.trade_api.get_order(
                instId=symbol_formatted,
                ordId=order_id
            )
            
            if result['code'] != '0':
                logger.error(f"获取订单状态失败: {result['msg']}")
                return {"status": "ERROR", "message": result['msg']}
                
            order_data = result['data'][0]
            status_map = {
                "live": "NEW",
                "partially_filled": "PARTIALLY_FILLED",
                "filled": "FILLED",
                "cancelled": "CANCELED",
                "failed": "REJECTED"
            }
            
            return {
                "order_id": order_data['ordId'],
                "status": status_map.get(order_data['state'], order_data['state']),
                "symbol": symbol,
                "price": float(order_data['px']) if order_data['px'] else 0,
                "amount": float(order_data['sz']),
                "filled": float(order_data['accFillSz']),
                "side": order_data['side']
            }
        except Exception as e:
            logger.error(f"获取订单状态失败: {str(e)}")
            return {"status": "ERROR", "message": str(e)} 