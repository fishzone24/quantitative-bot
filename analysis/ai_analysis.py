import os
import json
import logging
import time
from datetime import datetime
import requests
import pandas as pd
from typing import Dict, List, Optional

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ai_analysis')

class AIAnalyzer:
    """AI分析类"""
    
    def __init__(self, config=None):
        """
        初始化AI分析模块
        
        Args:
            config: AI分析配置参数
        """
        self.config = config or {}
        self.symbols = self.config.get("symbols", ["BTC/USDT"])
        
        # 初始化API配置
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.api_url = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1")
        self.api_path = os.getenv("DEEPSEEK_API_PATH", "/chat/completions")
        
        logger.info("初始化AI分析模块")
    
    def analyze_market_data(self, market_data: Dict, social_data: Dict = None) -> Dict:
        """
        分析市场数据
        
        Args:
            market_data: 市场数据
            social_data: 社交媒体数据
            
        Returns:
            Dict: 分析结果
        """
        try:
            # 如果没有API密钥，返回模拟数据
            if not self.api_key:
                logger.info("未设置API密钥，使用模拟分析")
                return self._generate_mock_analysis(market_data["symbol"])
            
            # 准备AI提示
            prompt = self._generate_prompt(market_data, social_data)
            
            # 调用API
            response = self._call_api(prompt)
            
            # 解析API响应
            analysis = self._parse_api_response(response, market_data["symbol"])
            
            return analysis
            
        except Exception as e:
            logger.error(f"分析市场数据失败: {str(e)}")
            return self._generate_mock_analysis(market_data["symbol"])
    
    def _generate_prompt(self, market_data: Dict, social_data: Dict = None) -> str:
        """生成AI提示"""
        symbol = market_data["symbol"]
        prompt = f"""
        分析以下加密货币市场数据，并提供交易建议:
        
        交易对: {symbol}
        当前价格: {market_data.get('current_price', 'N/A')}
        时间: {datetime.now().isoformat()}
        
        技术指标:
        """
        
        # 添加技术指标
        indicators = market_data.get("indicators", {})
        for indicator_name, indicator_data in indicators.items():
            prompt += f"- {indicator_name}: {json.dumps(indicator_data, ensure_ascii=False)}\n"
        
        # 添加交易信号
        signals = market_data.get("signals", {})
        prompt += "\n交易信号:\n"
        if signals.get("buy", False):
            prompt += f"- 买入信号 (强度: {signals.get('strength', 0)})\n"
            prompt += f"- 原因: {', '.join(signals.get('reason', []))}\n"
        if signals.get("sell", False):
            prompt += f"- 卖出信号 (强度: {abs(signals.get('strength', 0))})\n"
            prompt += f"- 原因: {', '.join(signals.get('reason', []))}\n"
        
        # 添加社交媒体数据
        if social_data:
            prompt += "\n社交媒体数据:\n"
            prompt += f"- 情感得分: {social_data.get('sentiment_score', 'N/A')}\n"
            prompt += f"- 市场情绪: {social_data.get('market_sentiment', 'N/A')}\n"
            prompt += f"- 热门话题: {', '.join(social_data.get('hot_topics', []))}\n"
            prompt += f"- 重要新闻: {', '.join(social_data.get('important_news', []))}\n"
        
        prompt += """
        请分析以上数据，并提供以下内容:
        1. 市场趋势预测 (看涨/看跌/震荡)
        2. 置信度 (0-100%)
        3. 建议操作 (买入/卖出/持有)
        4. 理由
        
        请以JSON格式返回结果，格式如下:
        {
            "trend": "看涨",
            "confidence": 80,
            "action": "买入",
            "reason": "技术指标显示超卖，有反弹机会"
        }
        """
        
        return prompt
    
    def _call_api(self, prompt: str) -> Dict:
        """调用AI API"""
        try:
            endpoint = f"{self.api_url}{self.api_path}"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "你是一位专业的加密货币分析师，根据市场数据提供交易建议。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2
            }
            
            response = requests.post(endpoint, headers=headers, json=data)
            
            if response.status_code != 200:
                logger.error(f"API调用失败: {response.status_code} {response.text}")
                raise Exception(f"API调用失败: {response.status_code}")
            
            return response.json()
            
        except Exception as e:
            logger.error(f"API调用失败: {str(e)}")
            raise
    
    def _parse_api_response(self, response: Dict, symbol: str) -> Dict:
        """解析API响应"""
        try:
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # 从响应中提取JSON
            start_pos = content.find("{")
            end_pos = content.rfind("}")
            
            if start_pos != -1 and end_pos != -1:
                json_str = content[start_pos:end_pos+1]
                analysis = json.loads(json_str)
                analysis["symbol"] = symbol
                analysis["timestamp"] = datetime.now().isoformat()
                
                return analysis
            else:
                raise Exception("未找到有效的JSON响应")
                
        except Exception as e:
            logger.error(f"解析API响应失败: {str(e)}")
            return self._generate_mock_analysis(symbol)
    
    def _generate_mock_analysis(self, symbol: str) -> Dict:
        """生成模拟分析结果"""
        # 随机模拟分析结果
        import random
        
        trends = ["看涨", "看跌", "震荡"]
        actions = ["买入", "卖出", "持有"]
        reasons = [
            "技术指标显示超卖，有反弹机会",
            "价格突破关键阻力位，上升趋势形成",
            "成交量放大，市场情绪积极",
            "出现顶部反转信号，可能开始下跌",
            "价格跌破重要支撑位，下行压力增加",
            "成交量低迷，缺乏上涨动力",
            "市场处于盘整阶段，等待方向确认",
            "技术指标中性，无明显信号",
            "价格波动减小，可能即将突破"
        ]
        
        trend = random.choice(trends)
        action = random.choice(actions)
        confidence = random.randint(50, 95)
        
        if trend == "看涨":
            reason = random.choice(reasons[:3])
        elif trend == "看跌":
            reason = random.choice(reasons[3:6])
        else:
            reason = random.choice(reasons[6:])
        
        return {
            "symbol": symbol,
            "trend": trend,
            "confidence": confidence,
            "action": action,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_ai_summary(self) -> Dict:
        """
        获取AI分析摘要
        
        Returns:
            Dict: AI分析摘要
        """
        summary = {
            "timestamp": datetime.now().isoformat(),
            "symbols": {}
        }
        
        for symbol in self.symbols:
            # 生成模拟分析
            analysis = self._generate_mock_analysis(symbol)
            summary["symbols"][symbol] = analysis
        
        return summary 