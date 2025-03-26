import numpy as np
import pandas as pd
import logging
import ta
from ta.trend import MACD, SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import VolumeWeightedAveragePrice

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('technical_analysis')

class TechnicalAnalysis:
    """技术分析类"""
    
    def __init__(self, config=None):
        """
        初始化技术分析模块
        
        Args:
            config: 技术分析配置参数
        """
        self.config = config or {}
        logger.info("初始化技术分析模块")
    
    def prepare_data(self, ohlcv_data, add_all_ta=False):
        """
        准备数据，将OHLCV数据转换为pandas DataFrame
        
        Args:
            ohlcv_data: OHLCV格式的K线数据，结构为[[timestamp, open, high, low, close, volume], ...]
            add_all_ta: 是否添加所有技术指标
            
        Returns:
            pandas DataFrame: 包含OHLCV和技术指标的数据
        """
        if not ohlcv_data or len(ohlcv_data) == 0:
            logger.error("OHLCV数据为空")
            return pd.DataFrame()
            
        try:
            # 创建DataFrame
            df = pd.DataFrame(
                ohlcv_data, 
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # 设置时间戳为索引
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # 确保所有价格列都是数值类型
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
            
            # 如果需要，添加所有技术指标
            if add_all_ta:
                df = self.add_all_indicators(df)
                
            return df
            
        except Exception as e:
            logger.error(f"准备数据失败: {str(e)}")
            return pd.DataFrame()
    
    def add_all_indicators(self, df):
        """
        添加所有技术指标到DataFrame
        
        Args:
            df: 包含OHLCV数据的DataFrame
            
        Returns:
            pandas DataFrame: 添加了所有技术指标的DataFrame
        """
        try:
            # 添加RSI
            rsi_period = self.config.get("RSI", {}).get("period", 14)
            rsi = RSIIndicator(close=df['close'], window=rsi_period)
            df['rsi'] = rsi.rsi()
            
            # 添加MACD
            macd_config = self.config.get("MACD", {})
            fast_period = macd_config.get("fast_period", 12)
            slow_period = macd_config.get("slow_period", 26)
            signal_period = macd_config.get("signal_period", 9)
            
            macd = MACD(
                close=df['close'], 
                window_fast=fast_period, 
                window_slow=slow_period, 
                window_sign=signal_period
            )
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_histogram'] = macd.macd_diff()
            
            # 添加布林带
            bb_config = self.config.get("BOLLINGER", {})
            bb_period = bb_config.get("period", 20)
            bb_std_dev = bb_config.get("std_dev", 2)
            
            bollinger = BollingerBands(
                close=df['close'], 
                window=bb_period, 
                window_dev=bb_std_dev
            )
            df['bb_upper'] = bollinger.bollinger_hband()
            df['bb_middle'] = bollinger.bollinger_mavg()
            df['bb_lower'] = bollinger.bollinger_lband()
            df['bb_width'] = bollinger.bollinger_wband()
            
            # 添加移动平均线
            df['sma_20'] = SMAIndicator(close=df['close'], window=20).sma_indicator()
            df['sma_50'] = SMAIndicator(close=df['close'], window=50).sma_indicator()
            df['sma_200'] = SMAIndicator(close=df['close'], window=200).sma_indicator()
            df['ema_20'] = EMAIndicator(close=df['close'], window=20).ema_indicator()
            
            # 添加ATR（波动率指标）
            atr = AverageTrueRange(
                high=df['high'], 
                low=df['low'], 
                close=df['close'], 
                window=14
            )
            df['atr'] = atr.average_true_range()
            
            # 添加随机震荡指标
            stoch = StochasticOscillator(
                high=df['high'],
                low=df['low'],
                close=df['close'],
                window=14,
                smooth_window=3
            )
            df['stoch_k'] = stoch.stoch()
            df['stoch_d'] = stoch.stoch_signal()
            
            # 添加成交量加权平均价格
            df['vwap'] = VolumeWeightedAveragePrice(
                high=df['high'],
                low=df['low'],
                close=df['close'],
                volume=df['volume'],
                window=14
            ).volume_weighted_average_price()
            
            return df
            
        except Exception as e:
            logger.error(f"添加指标失败: {str(e)}")
            return df
    
    def calculate_rsi(self, df, period=14):
        """计算RSI指标"""
        try:
            rsi = RSIIndicator(close=df['close'], window=period)
            return rsi.rsi()
        except Exception as e:
            logger.error(f"计算RSI失败: {str(e)}")
            return None
    
    def calculate_macd(self, df, fast_period=12, slow_period=26, signal_period=9):
        """计算MACD指标"""
        try:
            macd = MACD(
                close=df['close'], 
                window_fast=fast_period, 
                window_slow=slow_period, 
                window_sign=signal_period
            )
            return {
                'macd': macd.macd(),
                'signal': macd.macd_signal(),
                'histogram': macd.macd_diff()
            }
        except Exception as e:
            logger.error(f"计算MACD失败: {str(e)}")
            return None
    
    def calculate_bollinger_bands(self, df, period=20, std_dev=2):
        """计算布林带指标"""
        try:
            bollinger = BollingerBands(
                close=df['close'], 
                window=period, 
                window_dev=std_dev
            )
            return {
                'upper': bollinger.bollinger_hband(),
                'middle': bollinger.bollinger_mavg(),
                'lower': bollinger.bollinger_lband(),
                'width': bollinger.bollinger_wband()
            }
        except Exception as e:
            logger.error(f"计算布林带失败: {str(e)}")
            return None
    
    def calculate_support_resistance(self, df, lookback_periods=None, price_threshold=1.0):
        """
        计算支撑位和阻力位
        
        Args:
            df: 包含OHLCV数据的DataFrame
            lookback_periods: 回顾的周期列表，单位为小时
            price_threshold: 价格偏差阈值百分比
            
        Returns:
            dict: 支撑位和阻力位
        """
        try:
            if lookback_periods is None:
                lookback_config = self.config.get("SUPPORT_RESISTANCE", {})
                lookback_periods = lookback_config.get("lookback_periods", [6, 12, 24])
                price_threshold = lookback_config.get("price_threshold", 1.0)
            
            # 获取当前价格
            current_price = df['close'].iloc[-1]
            
            # 初始化支撑位和阻力位列表
            support_levels = []
            resistance_levels = []
            
            # 根据不同的回顾周期计算
            for period in lookback_periods:
                if len(df) < period:
                    continue
                    
                # 获取回顾期间的数据
                lookback_data = df.iloc[-period:]
                
                # 寻找局部最低点作为支撑位
                for i in range(1, len(lookback_data) - 1):
                    if (lookback_data['low'].iloc[i] < lookback_data['low'].iloc[i-1] and 
                        lookback_data['low'].iloc[i] < lookback_data['low'].iloc[i+1]):
                        level = lookback_data['low'].iloc[i]
                        # 如果价格水平接近当前价格的下方，添加为支撑位
                        if level < current_price * (1 - price_threshold / 100):
                            support_levels.append(level)
                
                # 寻找局部最高点作为阻力位
                for i in range(1, len(lookback_data) - 1):
                    if (lookback_data['high'].iloc[i] > lookback_data['high'].iloc[i-1] and 
                        lookback_data['high'].iloc[i] > lookback_data['high'].iloc[i+1]):
                        level = lookback_data['high'].iloc[i]
                        # 如果价格水平接近当前价格的上方，添加为阻力位
                        if level > current_price * (1 + price_threshold / 100):
                            resistance_levels.append(level)
            
            # 对支撑位和阻力位进行聚类，合并相近的价格水平
            support_levels = self._cluster_price_levels(support_levels, current_price * 0.002)
            resistance_levels = self._cluster_price_levels(resistance_levels, current_price * 0.002)
            
            return {
                'support': support_levels,
                'resistance': resistance_levels
            }
            
        except Exception as e:
            logger.error(f"计算支撑位和阻力位失败: {str(e)}")
            return {'support': [], 'resistance': []}
    
    def _cluster_price_levels(self, levels, threshold):
        """
        对价格水平进行聚类，合并相近的水平
        
        Args:
            levels: 价格水平列表
            threshold: 合并阈值
            
        Returns:
            list: 合并后的价格水平列表
        """
        if not levels:
            return []
            
        # 排序价格水平
        sorted_levels = sorted(levels)
        clustered_levels = []
        current_cluster = [sorted_levels[0]]
        
        for i in range(1, len(sorted_levels)):
            if sorted_levels[i] - sorted_levels[i-1] <= threshold:
                # 如果当前价格与上一个价格相近，添加到当前集群
                current_cluster.append(sorted_levels[i])
            else:
                # 否则，计算当前集群的平均值，并开始新的集群
                clustered_levels.append(sum(current_cluster) / len(current_cluster))
                current_cluster = [sorted_levels[i]]
        
        # 添加最后一个集群的平均值
        if current_cluster:
            clustered_levels.append(sum(current_cluster) / len(current_cluster))
        
        return clustered_levels
    
    def analyze_trend(self, df, short_period=6, long_period=24):
        """
        分析短期和长期趋势
        
        Args:
            df: 包含OHLCV数据的DataFrame
            short_period: 短期周期(小时)
            long_period: 长期周期(小时)
            
        Returns:
            dict: 趋势分析结果
        """
        try:
            if len(df) < long_period:
                return {'short_trend': 'unknown', 'long_trend': 'unknown'}
            
            # 计算短期趋势
            short_df = df.iloc[-short_period:]
            short_start_price = short_df['close'].iloc[0]
            short_end_price = short_df['close'].iloc[-1]
            short_trend = 'up' if short_end_price > short_start_price else 'down'
            short_change_pct = (short_end_price - short_start_price) / short_start_price * 100
            
            # 计算长期趋势
            long_df = df.iloc[-long_period:]
            long_start_price = long_df['close'].iloc[0]
            long_end_price = long_df['close'].iloc[-1]
            long_trend = 'up' if long_end_price > long_start_price else 'down'
            long_change_pct = (long_end_price - long_start_price) / long_start_price * 100
            
            # 计算EMA趋势
            ema_20 = EMAIndicator(close=df['close'], window=20).ema_indicator()
            ema_50 = EMAIndicator(close=df['close'], window=50).ema_indicator()
            
            ema_trend = 'up' if ema_20.iloc[-1] > ema_50.iloc[-1] else 'down'
            
            # 计算成交量趋势
            vol_short = short_df['volume'].mean()
            vol_long = long_df['volume'].mean()
            volume_trend = 'increasing' if vol_short > vol_long else 'decreasing'
            
            return {
                'short_trend': short_trend,
                'short_change_pct': short_change_pct,
                'long_trend': long_trend,
                'long_change_pct': long_change_pct,
                'ema_trend': ema_trend,
                'volume_trend': volume_trend
            }
            
        except Exception as e:
            logger.error(f"分析趋势失败: {str(e)}")
            return {'short_trend': 'unknown', 'long_trend': 'unknown'}
    
    def analyze_volatility(self, df, period=14):
        """
        分析价格波动率
        
        Args:
            df: 包含OHLCV数据的DataFrame
            period: 分析周期
            
        Returns:
            dict: 波动率分析结果
        """
        try:
            if len(df) < period:
                return {'volatility': None, 'atr': None}
            
            # 计算每日收益率
            df['returns'] = df['close'].pct_change() * 100
            
            # 计算波动率 (标准差)
            volatility = df['returns'].iloc[-period:].std()
            
            # 计算ATR
            atr = AverageTrueRange(
                high=df['high'], 
                low=df['low'], 
                close=df['close'], 
                window=period
            ).average_true_range().iloc[-1]
            
            # 计算波动率相对于历史的百分位
            if len(df) > period * 2:
                historical_volatility = df['returns'].iloc[:-period].std()
                volatility_percentile = 100 * (volatility / historical_volatility)
            else:
                volatility_percentile = 50
            
            return {
                'volatility': volatility,
                'atr': atr,
                'volatility_percentile': volatility_percentile
            }
            
        except Exception as e:
            logger.error(f"分析波动率失败: {str(e)}")
            return {'volatility': None, 'atr': None}
    
    def get_signal(self, df):
        """
        根据技术指标生成交易信号
        
        Args:
            df: 包含技术指标的DataFrame
            
        Returns:
            dict: 交易信号和指标摘要
        """
        try:
            if len(df) < 50:  # 确保有足够的数据
                return {'signal': 'neutral', 'reason': '数据不足'}
            
            # 获取最新的技术指标值
            latest = df.iloc[-1]
            
            # RSI信号
            rsi_config = self.config.get("RSI", {})
            rsi_overbought = rsi_config.get("overbought", 70)
            rsi_oversold = rsi_config.get("oversold", 30)
            
            rsi_signal = 'neutral'
            if latest['rsi'] > rsi_overbought:
                rsi_signal = 'sell'
            elif latest['rsi'] < rsi_oversold:
                rsi_signal = 'buy'
            
            # MACD信号
            macd_signal = 'neutral'
            if latest['macd'] > latest['macd_signal'] and latest['macd_histogram'] > 0:
                macd_signal = 'buy'
            elif latest['macd'] < latest['macd_signal'] and latest['macd_histogram'] < 0:
                macd_signal = 'sell'
            
            # 布林带信号
            bb_signal = 'neutral'
            if latest['close'] > latest['bb_upper']:
                bb_signal = 'sell'
            elif latest['close'] < latest['bb_lower']:
                bb_signal = 'buy'
            
            # 移动平均线信号
            ma_signal = 'neutral'
            if latest['close'] > latest['sma_50'] and latest['sma_20'] > latest['sma_50']:
                ma_signal = 'buy'
            elif latest['close'] < latest['sma_50'] and latest['sma_20'] < latest['sma_50']:
                ma_signal = 'sell'
            
            # 累计信号分数
            buy_signals = sum(1 for signal in [rsi_signal, macd_signal, bb_signal, ma_signal] if signal == 'buy')
            sell_signals = sum(1 for signal in [rsi_signal, macd_signal, bb_signal, ma_signal] if signal == 'sell')
            
            # 确定最终信号
            if buy_signals > sell_signals and buy_signals >= 2:
                final_signal = 'buy'
            elif sell_signals > buy_signals and sell_signals >= 2:
                final_signal = 'sell'
            else:
                final_signal = 'neutral'
            
            # 整合所有指标的状态
            indicator_summary = {
                'rsi': {
                    'value': latest['rsi'],
                    'signal': rsi_signal
                },
                'macd': {
                    'value': {
                        'macd': latest['macd'],
                        'signal': latest['macd_signal'],
                        'histogram': latest['macd_histogram']
                    },
                    'signal': macd_signal
                },
                'bollinger': {
                    'value': {
                        'upper': latest['bb_upper'],
                        'middle': latest['bb_middle'],
                        'lower': latest['bb_lower'],
                        'width': latest['bb_width']
                    },
                    'signal': bb_signal
                },
                'moving_averages': {
                    'value': {
                        'sma_20': latest['sma_20'],
                        'sma_50': latest['sma_50'],
                        'sma_200': latest.get('sma_200'),
                        'ema_20': latest['ema_20']
                    },
                    'signal': ma_signal
                }
            }
            
            # 获取支撑位和阻力位
            support_resistance = self.calculate_support_resistance(df)
            
            # 获取趋势分析
            trend_analysis = self.analyze_trend(df)
            
            # 获取波动率分析
            volatility_analysis = self.analyze_volatility(df)
            
            return {
                'signal': final_signal,
                'indicators': indicator_summary,
                'support_resistance': support_resistance,
                'trend': trend_analysis,
                'volatility': volatility_analysis,
                'current_price': latest['close'],
                'timestamp': df.index[-1]
            }
            
        except Exception as e:
            logger.error(f"生成信号失败: {str(e)}")
            return {'signal': 'error', 'reason': str(e)} 