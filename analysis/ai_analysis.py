import os
import json
import logging
import time
from datetime import datetime
import requests
import pandas as pd

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ai_analysis')

class AIAnalyzer:
    """AI分析器类"""
    
    def __init__(self, config=None):
        """
        初始化AI分析器
        
        Args:
            config: AI分析配置参数
        """
        self.config = config or {}
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.api_url = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1")
        self.api_path = os.getenv("DEEPSEEK_API_PATH", "/chat/completions")
        
        # 配置参数
        self.model = self.config.get("model", "deepseek-chat")
        self.confidence_threshold = self.config.get("confidence_threshold", 0.7)
        self.context_window = self.config.get("context_window", 24)  # 分析的历史数据窗口(小时)
        self.enable_predictions = self.config.get("enable_predictions", True)
        
        # 初始化检查
        if not self.api_key and self.enable_predictions:
            logger.warning("未设置DeepSeek API密钥，AI决策分析功能将被禁用")
            self.enable_predictions = False
        
        logger.info("初始化AI分析器")
    
    def analyze_market_data(self, technical_data, social_data, trading_pair):
        """
        分析市场数据并提供交易建议
        
        Args:
            technical_data: 技术分析数据
            social_data: 社交媒体分析数据
            trading_pair: 交易对
            
        Returns:
            dict: 分析结果
        """
        if not self.enable_predictions:
            logger.warning("AI决策分析功能已禁用，返回模拟分析结果")
            return self._generate_mock_analysis(trading_pair)
        
        try:
            # 准备分析请求
            prompt = self._generate_prompt(technical_data, social_data, trading_pair)
            
            # 调用DeepSeek API
            response = self._call_deepseek_api(prompt)
            
            if not response:
                logger.error("DeepSeek API返回空响应")
                return self._generate_mock_analysis(trading_pair)
            
            # 解析响应
            parsed_response = self._parse_ai_response(response)
            
            # 添加元数据
            parsed_response['timestamp'] = datetime.now()
            parsed_response['trading_pair'] = trading_pair
            
            return parsed_response
            
        except Exception as e:
            logger.error(f"AI分析失败: {str(e)}")
            return self._generate_mock_analysis(trading_pair)
    
    def _generate_prompt(self, technical_data, social_data, trading_pair):
        """
        生成DeepSeek API的提示词
        
        Args:
            technical_data: 技术分析数据
            social_data: 社交媒体分析数据
            trading_pair: 交易对
            
        Returns:
            str: 提示词
        """
        # 提取技术指标摘要
        current_price = technical_data.get('current_price', 'N/A')
        signal = technical_data.get('signal', 'neutral')
        
        rsi = 'N/A'
        rsi_signal = 'neutral'
        if 'indicators' in technical_data and 'rsi' in technical_data['indicators']:
            rsi = technical_data['indicators']['rsi'].get('value', 'N/A')
            rsi_signal = technical_data['indicators']['rsi'].get('signal', 'neutral')
        
        macd_info = 'N/A'
        macd_signal = 'neutral'
        if 'indicators' in technical_data and 'macd' in technical_data['indicators']:
            macd_values = technical_data['indicators']['macd'].get('value', {})
            macd_info = f"MACD: {macd_values.get('macd', 'N/A')}, Signal: {macd_values.get('signal', 'N/A')}, Histogram: {macd_values.get('histogram', 'N/A')}"
            macd_signal = technical_data['indicators']['macd'].get('signal', 'neutral')
        
        # 提取趋势信息
        trend_info = 'N/A'
        if 'trend' in technical_data:
            short_trend = technical_data['trend'].get('short_trend', 'unknown')
            long_trend = technical_data['trend'].get('long_trend', 'unknown')
            short_change = technical_data['trend'].get('short_change_pct', 0)
            long_change = technical_data['trend'].get('long_change_pct', 0)
            trend_info = f"短期趋势({6}h): {short_trend} ({short_change:.2f}%), 长期趋势({24}h): {long_trend} ({long_change:.2f}%)"
        
        # 提取支撑位和阻力位
        support_resistance_info = 'N/A'
        if 'support_resistance' in technical_data:
            supports = technical_data['support_resistance'].get('support', [])
            resistances = technical_data['support_resistance'].get('resistance', [])
            support_resistance_info = f"支撑位: {', '.join([str(round(s, 2)) for s in supports[:3]])}, 阻力位: {', '.join([str(round(r, 2)) for r in resistances[:3]])}"
        
        # 提取波动率信息
        volatility_info = 'N/A'
        if 'volatility' in technical_data:
            volatility = technical_data['volatility'].get('volatility', 'N/A')
            atr = technical_data['volatility'].get('atr', 'N/A')
            volatility_info = f"波动率: {volatility:.2f}%, ATR: {atr:.4f}"
        
        # 提取社交媒体分析信息
        social_sentiment = 'N/A'
        social_insights = 'N/A'
        important_announcements = []
        if social_data:
            social_sentiment = social_data.get('sentiment_category', 'neutral')
            social_insights = social_data.get('market_insights', 'N/A')
            
            # 获取重要公告
            announcements = social_data.get('important_announcements', [])
            for announcement in announcements[:2]:  # 只取前2条
                important_announcements.append(f"{announcement.get('user', 'Unknown')}: {announcement.get('text', 'N/A')}")
        
        # 构建提示词
        prompt = f"""你是一位加密货币市场专家分析师。请基于以下数据，分析{trading_pair}的市场状况，并给出交易建议(买入/卖出/观望)和置信度评分(0-100)。

技术分析数据:
- 当前价格: {current_price}
- 整体技术信号: {signal}
- RSI: {rsi} ({rsi_signal})
- {macd_info} ({macd_signal})
- 趋势: {trend_info}
- 支撑与阻力: {support_resistance_info}
- 波动性: {volatility_info}

社交媒体分析:
- 整体情绪: {social_sentiment}
- 市场洞察: {social_insights}"""

        if important_announcements:
            prompt += "\n- 重要公告:"
            for announcement in important_announcements:
                prompt += f"\n  * {announcement}"

        prompt += """

请提供以下格式的分析:
1. 简短的市场状况概述
2. 技术面分析
3. 社交媒体影响分析
4. 最终建议 (买入/卖出/观望)
5. 置信度 (0-100)
6. 风险评估

仅使用JSON格式响应，格式为:
{
  "market_overview": "市场概述...",
  "technical_analysis": "技术分析...",
  "social_analysis": "社交媒体分析...",
  "recommendation": "买入/卖出/观望",
  "confidence": 75,
  "risk_assessment": "风险评估..."
}"""

        return prompt
    
    def _call_deepseek_api(self, prompt):
        """
        调用DeepSeek API
        
        Args:
            prompt: 提示词
            
        Returns:
            str: API响应
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3  # 低温度以获得更一致的输出
            }
            
            # API端点
            endpoint = f"{self.api_url}{self.api_path}"
            
            logger.info(f"调用API: {endpoint}")
            
            # 发送请求
            response = requests.post(endpoint, headers=headers, json=payload)
            
            # 检查响应状态
            if response.status_code != 200:
                logger.error(f"DeepSeek API请求失败: {response.status_code} - {response.text}")
                return None
            
            # 解析响应
            response_json = response.json()
            
            # 获取内容
            content = response_json.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            return content
            
        except Exception as e:
            logger.error(f"调用DeepSeek API失败: {str(e)}")
            return None
    
    def _parse_ai_response(self, response_text):
        """
        解析AI响应
        
        Args:
            response_text: AI响应文本
            
        Returns:
            dict: 解析后的响应
        """
        try:
            # 查找JSON内容
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("在AI响应中找不到有效的JSON")
                return self._generate_default_response()
            
            json_content = response_text[json_start:json_end]
            
            # 解析JSON
            parsed = json.loads(json_content)
            
            # 验证必需字段
            required_fields = ['market_overview', 'technical_analysis', 'social_analysis', 'recommendation', 'confidence']
            for field in required_fields:
                if field not in parsed:
                    logger.warning(f"AI响应缺少必需字段: {field}")
                    parsed[field] = "N/A" if field != 'confidence' else 50
            
            # 标准化建议
            recommendation = parsed['recommendation'].lower()
            if 'buy' in recommendation:
                parsed['recommendation'] = 'buy'
            elif 'sell' in recommendation:
                parsed['recommendation'] = 'sell'
            else:
                parsed['recommendation'] = 'neutral'
            
            # 确保置信度在0-100范围内
            parsed['confidence'] = max(0, min(100, int(parsed['confidence'])))
            
            return parsed
            
        except Exception as e:
            logger.error(f"解析AI响应失败: {str(e)}")
            return self._generate_default_response()
    
    def _generate_default_response(self):
        """
        生成默认响应
        
        Returns:
            dict: 默认响应
        """
        return {
            'market_overview': '无法获取市场概述',
            'technical_analysis': '无法获取技术分析',
            'social_analysis': '无法获取社交媒体分析',
            'recommendation': 'neutral',
            'confidence': 50,
            'risk_assessment': '由于无法完成分析，建议保持谨慎并等待更多信息'
        }
    
    def _generate_mock_analysis(self, trading_pair):
        """
        生成模拟的AI分析结果
        
        Args:
            trading_pair: 交易对
            
        Returns:
            dict: 模拟的分析结果
        """
        # 随机选择一个建议
        import random
        recommendations = ['buy', 'sell', 'neutral']
        recommendation = random.choice(recommendations)
        
        # 根据建议生成相应的分析内容
        if recommendation == 'buy':
            market_overview = f"{trading_pair}显示出积极的上涨趋势，短期支撑位强劲，成交量增加表明买入兴趣上升。"
            technical_analysis = "RSI处于上升趋势但未达到超买区域，MACD显示看涨交叉，价格突破了关键阻力位。短期趋势向上，长期趋势开始形成底部。"
            social_analysis = "社交媒体情绪呈现积极，有关于项目发展和合作的正面消息，未发现重大负面声音。"
            risk_assessment = "上升趋势可能在短期内遇到阻力，建议设置3%的止损位以控制风险。"
            confidence = random.randint(70, 90)
        elif recommendation == 'sell':
            market_overview = f"{trading_pair}出现下跌信号，价格接近阻力位，市场情绪谨慎，成交量减少。"
            technical_analysis = "RSI进入超买区域并开始回落，MACD显示看跌交叉，价格遇到明显阻力。短期和长期趋势均向下，支撑位面临压力。"
            social_analysis = "社交媒体情绪转向负面，市场对近期发展表示担忧，部分投资者开始减仓。"
            risk_assessment = "市场可能出现短期反弹，建议分批卖出以降低时机风险。"
            confidence = random.randint(65, 85)
        else:  # neutral
            market_overview = f"{trading_pair}目前处于盘整阶段，价格在支撑位和阻力位之间波动，市场方向不明确。"
            technical_analysis = "RSI在中性区域徘徊，MACD线和信号线纠缠在一起，未形成明确方向。短期趋势小幅波动，长期趋势尚未确立。"
            social_analysis = "社交媒体情绪中性，无重大消息影响市场，投资者普遍持观望态度。"
            risk_assessment = "市场可能继续横盘一段时间，建议等待更明确的信号再采取行动。"
            confidence = random.randint(50, 65)
        
        return {
            'market_overview': market_overview,
            'technical_analysis': technical_analysis,
            'social_analysis': social_analysis,
            'recommendation': recommendation,
            'confidence': confidence,
            'risk_assessment': risk_assessment,
            'timestamp': datetime.now(),
            'trading_pair': trading_pair,
            'is_mock_data': True
        } 