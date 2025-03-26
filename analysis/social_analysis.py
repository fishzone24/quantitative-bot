import tweepy
import pandas as pd
import numpy as np
import logging
import re
import time
from datetime import datetime, timedelta
from textblob import TextBlob
import nltk
from nltk.tokenize import word_tokenize
from collections import Counter
import os

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('social_analysis')

# 确保NLTK的必要资源已下载
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    logger.info("下载NLTK punkt分词器...")
    nltk.download('punkt', quiet=True)

class SocialMediaAnalyzer:
    """社交媒体分析类"""
    
    def __init__(self, config=None):
        """
        初始化社交媒体分析模块
        
        Args:
            config: 社交媒体分析配置参数
        """
        self.config = config or {}
        self.twitter_accounts = self.config.get("twitter_accounts", [])
        self.important_keywords = self.config.get("important_keywords", [])
        self.sentiment_threshold = self.config.get("sentiment_threshold", {
            "positive": 0.6,
            "negative": -0.3
        })
        
        # 初始化Twitter API
        self.twitter_api = None
        self.init_twitter_api()
        
        logger.info("初始化社交媒体分析模块")
    
    def init_twitter_api(self):
        """初始化Twitter API"""
        try:
            # 获取Twitter API凭证
            api_key = os.getenv("TWITTER_API_KEY")
            api_secret = os.getenv("TWITTER_API_SECRET")
            access_token = os.getenv("TWITTER_ACCESS_TOKEN")
            access_secret = os.getenv("TWITTER_ACCESS_SECRET")
            bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
            
            if not all([api_key, api_secret, access_token, access_secret]):
                logger.warning("Twitter API凭证不完整，社交媒体分析将被禁用")
                return
            
            # 设置Twitter API客户端
            auth = tweepy.OAuth1UserHandler(
                api_key, api_secret, access_token, access_secret
            )
            self.twitter_api = tweepy.API(auth)
            
            # 测试API连接
            self.twitter_api.verify_credentials()
            logger.info("Twitter API连接成功")
            
        except Exception as e:
            logger.error(f"初始化Twitter API失败: {str(e)}")
            self.twitter_api = None
    
    def fetch_tweets(self, account_name, count=100):
        """
        获取指定账户的最新推文
        
        Args:
            account_name: Twitter账户名称
            count: 获取的推文数量
            
        Returns:
            list: 推文列表
        """
        if not self.twitter_api:
            logger.warning("Twitter API未初始化，无法获取推文")
            return []
            
        try:
            # 获取用户最新推文
            tweets = self.twitter_api.user_timeline(
                screen_name=account_name,
                count=count,
                include_rts=False,  # 不包括转发
                tweet_mode="extended"  # 获取完整文本
            )
            
            logger.info(f"已获取{len(tweets)}条{account_name}的推文")
            
            # 格式化推文数据
            formatted_tweets = []
            for tweet in tweets:
                formatted_tweets.append({
                    'id': tweet.id_str,
                    'text': tweet.full_text,
                    'created_at': tweet.created_at,
                    'user': tweet.user.screen_name,
                    'favorite_count': tweet.favorite_count,
                    'retweet_count': tweet.retweet_count
                })
            
            return formatted_tweets
            
        except Exception as e:
            logger.error(f"获取{account_name}的推文失败: {str(e)}")
            return []
    
    def analyze_tweet_sentiment(self, tweet_text):
        """
        分析推文情感
        
        Args:
            tweet_text: 推文文本
            
        Returns:
            float: 情感分数，范围[-1, 1]，正数表示积极，负数表示消极
        """
        try:
            # 清理文本
            cleaned_text = self._clean_text(tweet_text)
            
            # 使用TextBlob进行情感分析
            blob = TextBlob(cleaned_text)
            sentiment_score = blob.sentiment.polarity
            
            return sentiment_score
            
        except Exception as e:
            logger.error(f"分析推文情感失败: {str(e)}")
            return 0.0
    
    def _clean_text(self, text):
        """
        清理文本，去除URL、@提及、特殊字符等
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理后的文本
        """
        # 去除URL
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # 去除@提及
        text = re.sub(r'@\w+', '', text)
        
        # 去除特殊字符和数字
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\d+', '', text)
        
        # 转换为小写
        text = text.lower()
        
        return text
    
    def detect_important_keywords(self, text):
        """
        检测文本中的重要关键词
        
        Args:
            text: 文本内容
            
        Returns:
            list: 检测到的关键词列表
        """
        try:
            # 转换为小写
            text = text.lower()
            
            # 检测重要关键词
            found_keywords = []
            for keyword in self.important_keywords:
                if keyword.lower() in text:
                    found_keywords.append(keyword)
            
            return found_keywords
            
        except Exception as e:
            logger.error(f"检测关键词失败: {str(e)}")
            return []
    
    def extract_common_topics(self, tweets, top_n=10):
        """
        提取推文中的常见话题
        
        Args:
            tweets: 推文列表
            top_n: 返回的话题数量
            
        Returns:
            list: 常见话题列表
        """
        try:
            # 合并所有推文文本
            all_text = " ".join([tweet['text'] for tweet in tweets])
            
            # 清理文本
            cleaned_text = self._clean_text(all_text)
            
            # 分词
            tokens = word_tokenize(cleaned_text)
            
            # 过滤停用词
            stop_words = ['the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 
                         'were', 'to', 'of', 'in', 'for', 'with', 'by', 'at', 'on']
            filtered_tokens = [word for word in tokens if word.lower() not in stop_words and len(word) > 2]
            
            # 统计词频
            word_counts = Counter(filtered_tokens)
            
            # 返回最常见的词
            return word_counts.most_common(top_n)
            
        except Exception as e:
            logger.error(f"提取常见话题失败: {str(e)}")
            return []
    
    def analyze_binance_tweets(self):
        """
        分析币安相关账户的推文
        
        Returns:
            dict: 分析结果
        """
        if not self.twitter_api:
            logger.warning("Twitter API未初始化，无法分析币安推文")
            return self._generate_mock_analysis()
            
        all_tweets = []
        
        # 获取所有配置的Twitter账户的推文
        for account in self.twitter_accounts:
            account_tweets = self.fetch_tweets(account, count=20)
            all_tweets.extend(account_tweets)
        
        # 如果无法获取真实推文，使用模拟数据
        if not all_tweets:
            logger.warning("无法获取真实推文，使用模拟数据")
            return self._generate_mock_analysis()
        
        # 按时间排序
        all_tweets.sort(key=lambda x: x['created_at'], reverse=True)
        
        # 只保留最近24小时的推文
        recent_time = datetime.now() - timedelta(hours=24)
        recent_tweets = [tweet for tweet in all_tweets if tweet['created_at'] > recent_time]
        
        # 分析每条推文的情感和关键词
        for tweet in recent_tweets:
            tweet['sentiment_score'] = self.analyze_tweet_sentiment(tweet['text'])
            tweet['important_keywords'] = self.detect_important_keywords(tweet['text'])
            
            # 根据情感分数确定情感类别
            if tweet['sentiment_score'] >= self.sentiment_threshold['positive']:
                tweet['sentiment'] = 'positive'
            elif tweet['sentiment_score'] <= self.sentiment_threshold['negative']:
                tweet['sentiment'] = 'negative'
            else:
                tweet['sentiment'] = 'neutral'
        
        # 计算总体情感分数
        if recent_tweets:
            overall_sentiment = sum(tweet['sentiment_score'] for tweet in recent_tweets) / len(recent_tweets)
        else:
            overall_sentiment = 0
            
        # 提取常见话题
        common_topics = self.extract_common_topics(recent_tweets)
        
        # 找出重要公告
        important_announcements = [
            tweet for tweet in recent_tweets 
            if tweet['important_keywords'] and 
            (tweet['retweet_count'] > 50 or tweet['favorite_count'] > 100)
        ]
        
        # 整合分析结果
        analysis_result = {
            'timestamp': datetime.now(),
            'total_tweets_analyzed': len(recent_tweets),
            'overall_sentiment': overall_sentiment,
            'sentiment_category': self._get_sentiment_category(overall_sentiment),
            'common_topics': common_topics,
            'important_announcements': important_announcements[:5],  # 只返回最重要的5条
            'market_insights': self._generate_market_insights(recent_tweets, overall_sentiment),
            'recent_tweets': recent_tweets[:10]  # 只返回最新的10条推文
        }
        
        return analysis_result
    
    def _generate_mock_analysis(self):
        """
        生成模拟的社交媒体分析数据
        
        Returns:
            dict: 模拟的分析结果
        """
        # 当无法访问真实API时使用的模拟数据
        mock_tweets = [
            {
                'id': '1',
                'text': 'We are excited to announce a new listing on Binance: XYZ Token (XYZ)!',
                'created_at': datetime.now() - timedelta(hours=2),
                'user': 'binance',
                'favorite_count': 530,
                'retweet_count': 210,
                'sentiment_score': 0.75,
                'sentiment': 'positive',
                'important_keywords': ['listing', 'announcement']
            },
            {
                'id': '2',
                'text': 'Market update: Bitcoin has shown strong resilience in the past 24 hours.',
                'created_at': datetime.now() - timedelta(hours=5),
                'user': 'BinanceResearch',
                'favorite_count': 320,
                'retweet_count': 95,
                'sentiment_score': 0.45,
                'sentiment': 'neutral',
                'important_keywords': ['update']
            },
            {
                'id': '3',
                'text': 'Warning: Beware of phishing attempts. Always verify you are on the official Binance website.',
                'created_at': datetime.now() - timedelta(hours=10),
                'user': 'cz_binance',
                'favorite_count': 850,
                'retweet_count': 420,
                'sentiment_score': -0.2,
                'sentiment': 'neutral',
                'important_keywords': []
            }
        ]
        
        return {
            'timestamp': datetime.now(),
            'total_tweets_analyzed': len(mock_tweets),
            'overall_sentiment': 0.33,
            'sentiment_category': 'neutral',
            'common_topics': [('listing', 3), ('market', 2), ('bitcoin', 2)],
            'important_announcements': [mock_tweets[0]],
            'market_insights': '社交媒体情绪整体为中性偏积极，主要关注新上币和市场动态。',
            'recent_tweets': mock_tweets,
            'is_mock_data': True
        }
    
    def _get_sentiment_category(self, sentiment_score):
        """
        根据情感分数确定情感类别
        
        Args:
            sentiment_score: 情感分数
            
        Returns:
            str: 情感类别
        """
        if sentiment_score >= self.sentiment_threshold['positive']:
            return 'positive'
        elif sentiment_score <= self.sentiment_threshold['negative']:
            return 'negative'
        else:
            return 'neutral'
    
    def _generate_market_insights(self, tweets, overall_sentiment):
        """
        根据推文和情感分析生成市场洞察
        
        Args:
            tweets: 推文列表
            overall_sentiment: 总体情感分数
            
        Returns:
            str: 市场洞察
        """
        # 计算带有重要关键词的推文比例
        important_tweets_count = sum(1 for tweet in tweets if tweet['important_keywords'])
        important_tweet_ratio = important_tweets_count / len(tweets) if tweets else 0
        
        # 计算积极和消极推文的比例
        positive_tweets = [tweet for tweet in tweets if tweet.get('sentiment') == 'positive']
        negative_tweets = [tweet for tweet in tweets if tweet.get('sentiment') == 'negative']
        
        positive_ratio = len(positive_tweets) / len(tweets) if tweets else 0
        negative_ratio = len(negative_tweets) / len(tweets) if tweets else 0
        
        # 生成市场洞察
        insights = "社交媒体分析："
        
        # 情感洞察
        if overall_sentiment >= 0.5:
            insights += "整体情绪十分积极，市场可能处于乐观状态。"
        elif overall_sentiment >= 0.2:
            insights += "整体情绪偏积极，市场情绪良好。"
        elif overall_sentiment >= -0.2:
            insights += "整体情绪中性，市场情绪稳定。"
        elif overall_sentiment >= -0.5:
            insights += "整体情绪偏消极，市场可能存在担忧。"
        else:
            insights += "整体情绪十分消极，市场可能处于悲观状态。"
        
        # 重要消息洞察
        if important_tweet_ratio >= 0.3:
            insights += "有大量重要消息发布，需密切关注市场反应。"
        elif important_tweet_ratio >= 0.1:
            insights += "有少量重要消息发布，可能会影响部分币种表现。"
        else:
            insights += "未发现重要消息，市场可能维持目前趋势。"
        
        # 积极/消极比例洞察
        if positive_ratio > negative_ratio * 3:
            insights += "正面消息远多于负面消息，可能利好市场。"
        elif positive_ratio > negative_ratio * 1.5:
            insights += "正面消息多于负面消息，市场整体偏乐观。"
        elif negative_ratio > positive_ratio * 3:
            insights += "负面消息远多于正面消息，可能利空市场。"
        elif negative_ratio > positive_ratio * 1.5:
            insights += "负面消息多于正面消息，市场整体偏谨慎。"
        else:
            insights += "正面消息与负面消息基本平衡，市场情绪中立。"
        
        return insights 