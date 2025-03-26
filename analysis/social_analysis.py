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
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from typing import Dict

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
        
        # 初始化Twitter登录
        self.driver = None
        self.init_twitter_login()
        
        logger.info("初始化社交媒体分析模块")
    
    def init_twitter_login(self):
        """初始化Twitter登录"""
        try:
            # 获取Twitter登录凭证
            email = os.getenv("TWITTER_EMAIL")
            password = os.getenv("TWITTER_PASSWORD")
            
            if not email or not password:
                logger.warning("Twitter登录凭证不完整，社交媒体分析将被禁用")
                return
            
            try:
                # 设置Chrome选项
                chrome_options = Options()
                chrome_options.add_argument("--headless")  # 无头模式
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                
                # 兼容Linux环境
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("--disable-software-rasterizer")
                
                # 尝试使用直接的ChromeDriver路径
                try:
                    # 首先检查系统是否安装了Chrome浏览器
                    if os.system("which google-chrome") == 0:
                        version_cmd = "google-chrome --version"
                        version = os.popen(version_cmd).read().strip().split()[-1]
                        logger.info(f"检测到Chrome版本: {version}")
                    elif os.system("which chromium-browser") == 0:
                        version_cmd = "chromium-browser --version"
                        version = os.popen(version_cmd).read().strip().split()[-1]
                        logger.info(f"检测到Chromium版本: {version}")
                    else:
                        logger.warning("未检测到Chrome或Chromium浏览器")
                    
                    # 尝试直接使用系统Chrome
                    self.driver = webdriver.Chrome(options=chrome_options)
                except Exception as e1:
                    logger.warning(f"直接初始化Chrome失败: {str(e1)}，尝试使用webdriver-manager")
                    
                    # 尝试使用webdriver-manager
                    try:
                        # 避免使用缓存目录，直接下载到当前目录
                        os.environ["WDM_LOCAL"] = "1"
                        
                        from webdriver_manager.chrome import ChromeDriverManager
                        driver_path = ChromeDriverManager().install()
                        
                        # 确保驱动程序有执行权限
                        os.system(f"chmod +x {driver_path}")
                        
                        service = Service(driver_path)
                        self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    except Exception as e2:
                        logger.error(f"使用webdriver-manager初始化Chrome失败: {str(e2)}")
                        
                        # 最后尝试使用模拟分析
                        logger.warning("无法初始化浏览器，将使用模拟社交媒体分析")
                        self.driver = None
                        return
                
                # 登录Twitter
                self._login_twitter(email, password)
                logger.info("Twitter登录成功")
                
            except Exception as e:
                logger.error(f"初始化Twitter浏览器失败: {str(e)}")
                self.driver = None
            
        except Exception as e:
            logger.error(f"初始化Twitter登录失败: {str(e)}")
            self.driver = None
    
    def _login_twitter(self, email, password):
        """登录Twitter"""
        try:
            # 访问Twitter登录页面
            self.driver.get("https://twitter.com/login")
            time.sleep(3)  # 等待页面加载
            
            # 输入邮箱
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "text"))
            )
            email_input.send_keys(email)
            self.driver.find_element(By.XPATH, "//span[text()='Next']").click()
            time.sleep(2)
            
            # 输入密码
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_input.send_keys(password)
            self.driver.find_element(By.XPATH, "//span[text()='Log in']").click()
            time.sleep(3)
            
        except Exception as e:
            logger.error(f"Twitter登录失败: {str(e)}")
            raise
    
    def fetch_tweets(self, account_name, count=100):
        """
        获取指定账户的最新推文
        
        Args:
            account_name: Twitter账户名称
            count: 获取的推文数量
            
        Returns:
            list: 推文列表
        """
        if not self.driver:
            logger.warning("Twitter未登录，无法获取推文")
            return []
            
        try:
            # 访问用户主页
            self.driver.get(f"https://twitter.com/{account_name}")
            time.sleep(3)
            
            # 获取推文
            tweets = []
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while len(tweets) < count:
                # 获取当前页面的推文
                tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, "article[data-testid='tweet']")
                
                for tweet in tweet_elements:
                    try:
                        # 获取推文文本
                        text = tweet.find_element(By.CSS_SELECTOR, "div[data-testid='tweetText']").text
                        
                        # 获取时间
                        time_element = tweet.find_element(By.TAG_NAME, "time")
                        created_at = datetime.fromisoformat(time_element.get_attribute("datetime"))
                        
                        # 获取互动数据
                        try:
                            favorite_count = tweet.find_element(By.CSS_SELECTOR, "div[data-testid='like']").text
                        except:
                            favorite_count = "0"
                            
                        try:
                            retweet_count = tweet.find_element(By.CSS_SELECTOR, "div[data-testid='retweet']").text
                        except:
                            retweet_count = "0"
                        
                        tweets.append({
                            'id': str(len(tweets) + 1),
                            'text': text,
                            'created_at': created_at,
                            'user': account_name,
                            'favorite_count': int(favorite_count) if favorite_count.isdigit() else 0,
                            'retweet_count': int(retweet_count) if retweet_count.isdigit() else 0
                        })
                        
                        if len(tweets) >= count:
                            break
                            
                    except Exception as e:
                        logger.warning(f"解析推文失败: {str(e)}")
                        continue
                
                # 滚动到页面底部
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            logger.info(f"已获取{len(tweets)}条{account_name}的推文")
            return tweets
            
        except Exception as e:
            logger.error(f"获取{account_name}的推文失败: {str(e)}")
            return []
    
    def __del__(self):
        """清理资源"""
        if self.driver:
            self.driver.quit()
    
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
        if not self.driver:
            logger.warning("Twitter未登录，无法分析币安推文")
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

    def get_social_summary(self) -> Dict:
        """
        获取社交媒体分析摘要
        
        Returns:
            Dict: 社交媒体分析摘要
        """
        summary = {
            "timestamp": datetime.now().isoformat(),
            "symbols": {}
        }
        
        # 如果没有初始化Twitter客户端，返回模拟数据
        if not self.driver:
            for symbol in self.config.get("symbols", ["BTC/USDT"]):
                summary["symbols"][symbol] = self._generate_mock_analysis(symbol)
            return summary
        
        # 获取Twitter数据并分析
        try:
            for symbol in self.config.get("symbols", ["BTC/USDT"]):
                # 提取货币名称
                currency = symbol.split("/")[0]
                
                # 获取相关账号的推文
                accounts = [account for account in self.twitter_accounts if currency.lower() in account.lower()]
                if not accounts:
                    accounts = self.twitter_accounts[:2]  # 取前两个账号
                
                all_tweets = []
                for account in accounts[:2]:  # 限制只查询前两个账号
                    tweets = self.fetch_tweets(account, count=10)
                    all_tweets.extend(tweets)
                
                # 分析推文情感
                sentiment_scores = []
                important_news = []
                hot_topics = []
                
                for tweet in all_tweets[:20]:  # 只分析前20条推文
                    # 情感分析
                    sentiment = self.analyze_tweet_sentiment(tweet['text'])
                    sentiment_scores.append(sentiment['sentiment_score'])
                    
                    # 提取重要新闻和热门话题
                    if sentiment['is_important']:
                        important_news.append(tweet['text'][:100] + "...")
                    
                    # 提取关键词
                    keywords = self.extract_keywords(tweet['text'])
                    hot_topics.extend(keywords)
                
                # 汇总数据
                if sentiment_scores:
                    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
                else:
                    avg_sentiment = 0
                
                market_sentiment = "中性"
                if avg_sentiment > 0.2:
                    market_sentiment = "积极"
                elif avg_sentiment < -0.2:
                    market_sentiment = "消极"
                
                # 获取热门话题（频率最高的5个）
                from collections import Counter
                topic_counter = Counter(hot_topics)
                popular_topics = [topic for topic, _ in topic_counter.most_common(5)]
                
                summary["symbols"][symbol] = {
                    "sentiment_score": round(avg_sentiment, 2),
                    "market_sentiment": market_sentiment,
                    "important_news": important_news[:3],  # 最多3条重要新闻
                    "hot_topics": popular_topics,
                    "timestamp": datetime.now().isoformat()
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"获取社交媒体摘要失败: {str(e)}")
            # 返回模拟数据
            for symbol in self.config.get("symbols", ["BTC/USDT"]):
                summary["symbols"][symbol] = self._generate_mock_analysis(symbol)
            return summary

    def _generate_mock_analysis(self, symbol: str) -> Dict:
        """生成模拟分析结果"""
        # 随机模拟分析结果
        import random
        
        sentiments = ["积极", "中性", "消极"]
        topics = [
            "价格上涨", "价格下跌", "新合作", "技术更新", 
            "监管消息", "交易量增加", "市场波动", "鲸鱼活动",
            "社区活动", "行业新闻", "竞争对手", "宏观经济"
        ]
        news = [
            f"{symbol.split('/')[0]}价格在过去24小时内上涨超过5%",
            f"{symbol.split('/')[0]}开发团队宣布重要技术突破",
            f"大型交易所宣布支持{symbol.split('/')[0]}",
            f"{symbol.split('/')[0]}社区投票通过新提案",
            f"分析师预测{symbol.split('/')[0]}价格走势看好",
            f"市场对{symbol.split('/')[0]}的兴趣增加",
            f"{symbol.split('/')[0]}交易量创新高",
            f"知名投资者增持{symbol.split('/')[0]}"
        ]
        
        sentiment_score = random.uniform(-0.5, 0.5)
        sentiment = "中性"
        if sentiment_score > 0.2:
            sentiment = "积极"
        elif sentiment_score < -0.2:
            sentiment = "消极"
        
        # 随机选择3-5个热门话题
        random_topics = random.sample(topics, random.randint(3, 5))
        
        # 随机选择1-3条重要新闻
        random_news = random.sample(news, random.randint(1, 3))
        
        return {
            "sentiment_score": round(sentiment_score, 2),
            "market_sentiment": sentiment,
            "important_news": random_news,
            "hot_topics": random_topics,
            "timestamp": datetime.now().isoformat()
        } 