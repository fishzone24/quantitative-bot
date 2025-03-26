#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
交互式菜单系统 - 为加密货币量化交易系统提供用户界面
"""

import os
import sys
import logging
import time
from dotenv import load_dotenv
import config

logger = logging.getLogger('menu')

class Menu:
    """交互式菜单系统"""
    
    def __init__(self):
        """初始化菜单系统"""
        # 加载环境变量
        load_dotenv()
    
    def clear_screen(self):
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_banner(self):
        """显示系统横幅"""
        self.clear_screen()
        print("\n" + "=" * 60)
        print("  🚀 CryptoQuantTrader - 加密货币量化交易系统 🚀")
        print("=" * 60 + "\n")
    
    def show_main_menu(self):
        """显示主菜单"""
        self.show_banner()
        print("📋 主菜单选项：")
        print("  1. 启动交易系统")
        print("  2. 仅运行市场分析")
        print("  3. 交易所设置")
        print("  4. 社交媒体设置")
        print("  5. AI决策系统设置")
        print("  6. 自动交易设置")
        print("  7. 查看交易记录")
        print("  8. 生成交易报告")
        print("  9. 关闭所有头寸")
        print("  0. 退出程序")
        print("\n" + "-" * 60)
        
        return self.get_choice(0, 9)
    
    def get_choice(self, min_value, max_value):
        """获取用户选择"""
        while True:
            try:
                choice = input("\n请输入您的选择 [0-9]: ")
                choice = int(choice)
                if min_value <= choice <= max_value:
                    return choice
                else:
                    print(f"❌ 无效选择，请输入 {min_value}-{max_value} 之间的数字")
            except ValueError:
                print("❌ 无效输入，请输入数字")
    
    def get_string_input(self, prompt, allow_empty=False):
        """获取字符串输入"""
        while True:
            value = input(prompt)
            if value or allow_empty:
                return value
            print("❌ 输入不能为空，请重新输入")
    
    def get_float_input(self, prompt, min_value=None, max_value=None):
        """获取浮点数输入"""
        while True:
            try:
                value = input(prompt)
                value = float(value)
                
                if min_value is not None and value < min_value:
                    print(f"❌ 输入值不能小于 {min_value}")
                    continue
                    
                if max_value is not None and value > max_value:
                    print(f"❌ 输入值不能大于 {max_value}")
                    continue
                
                return value
            except ValueError:
                print("❌ 无效输入，请输入数字")
    
    def show_exchange_menu(self):
        """显示交易所设置菜单"""
        self.show_banner()
        print("📊 交易所设置")
        print("  1. 设置交易所 (Binance/OKX)")
        print("  2. 配置API密钥")
        print("  3. 返回主菜单")
        print("\n" + "-" * 60)
        
        choice = self.get_choice(1, 3)
        
        if choice == 1:
            self.set_exchange()
        elif choice == 2:
            self.set_api_keys()
        else:
            return
    
    def set_exchange(self):
        """设置交易所"""
        self.show_banner()
        print("🔄 设置交易所")
        print("  1. Binance (币安)")
        print("  2. OKX")
        print("\n" + "-" * 60)
        
        choice = self.get_choice(1, 2)
        
        exchange = "binance" if choice == 1 else "okx"
        
        # 更新配置
        self.update_env_var("EXCHANGE", exchange)
        print(f"✅ 已设置交易所为: {exchange.upper()}")
        input("\n按 Enter 继续...")
    
    def set_api_keys(self):
        """设置API密钥"""
        self.show_banner()
        print("🔑 配置API密钥")
        
        # 获取当前交易所
        exchange = os.getenv("EXCHANGE", "binance").lower()
        print(f"当前交易所: {exchange.upper()}")
        
        if exchange == "binance":
            # 显示已有的配置
            current_api_key = os.getenv("BINANCE_API_KEY", "")
            current_api_secret = os.getenv("BINANCE_API_SECRET", "")
            
            # 显示已有的值（部分隐藏）
            if current_api_key:
                masked_key = current_api_key[:4] + "*" * (len(current_api_key) - 8) + current_api_key[-4:]
                print(f"当前API Key: {masked_key}")
            if current_api_secret:
                masked_secret = current_api_secret[:4] + "*" * (len(current_api_secret) - 8) + current_api_secret[-4:]
                print(f"当前API Secret: {masked_secret}")
            
            # 提示用户是否需要更新
            update = input("\n是否更新API密钥? (y/n，默认n): ").lower()
            if update != 'y':
                print("保持原有设置")
                input("\n按 Enter 继续...")
                return
            
            api_key = self.get_string_input("请输入 Binance API Key: ")
            api_secret = self.get_string_input("请输入 Binance API Secret: ")
            
            self.update_env_var("BINANCE_API_KEY", api_key)
            self.update_env_var("BINANCE_API_SECRET", api_secret)
            
        elif exchange == "okx":
            # 显示已有的配置
            current_api_key = os.getenv("OKX_API_KEY", "")
            current_api_secret = os.getenv("OKX_API_SECRET", "")
            current_passphrase = os.getenv("OKX_PASSPHRASE", "")
            
            # 显示已有的值（部分隐藏）
            if current_api_key:
                masked_key = current_api_key[:4] + "*" * (len(current_api_key) - 8) + current_api_key[-4:]
                print(f"当前API Key: {masked_key}")
            if current_api_secret:
                masked_secret = current_api_secret[:4] + "*" * (len(current_api_secret) - 8) + current_api_secret[-4:]
                print(f"当前API Secret: {masked_secret}")
            if current_passphrase:
                masked_pass = "*" * len(current_passphrase)
                print(f"当前Passphrase: {masked_pass}")
            
            # 提示用户是否需要更新
            update = input("\n是否更新API密钥? (y/n，默认n): ").lower()
            if update != 'y':
                print("保持原有设置")
                input("\n按 Enter 继续...")
                return
            
            api_key = self.get_string_input("请输入 OKX API Key: ")
            api_secret = self.get_string_input("请输入 OKX API Secret: ")
            passphrase = self.get_string_input("请输入 OKX Passphrase: ")
            
            self.update_env_var("OKX_API_KEY", api_key)
            self.update_env_var("OKX_API_SECRET", api_secret)
            self.update_env_var("OKX_PASSPHRASE", passphrase)
        
        print(f"✅ {exchange.upper()} API密钥配置已更新")
        input("\n按 Enter 继续...")
    
    def show_social_media_menu(self):
        """显示社交媒体设置菜单"""
        self.show_banner()
        print("🐦 社交媒体设置")
        
        # 显示当前模拟模式设置
        simulation_mode = os.getenv("SOCIAL_SIMULATION_MODE", "false").lower() in ["true", "1", "yes", "y"]
        simulation_status = "已启用" if simulation_mode else "已禁用"
        print(f"\n当前模拟模式: {simulation_status}")
        
        print("\n  1. 连接推特账户")
        print("  2. 添加关注账号")
        print(f"  3. {'禁用' if simulation_mode else '启用'}模拟模式")
        print("  4. 返回主菜单")
        print("\n" + "-" * 60)
        
        choice = self.get_choice(1, 4)
        
        if choice == 1:
            self.set_twitter_account()
        elif choice == 2:
            self.add_twitter_follows()
        elif choice == 3:
            self.toggle_simulation_mode()
        else:
            return
    
    def set_twitter_account(self):
        """设置推特账户"""
        self.show_banner()
        print("🐦 连接推特账户")
        
        # 显示已有的配置
        current_email = os.getenv("TWITTER_EMAIL", "")
        current_password = os.getenv("TWITTER_PASSWORD", "")
        
        # 显示已有的值（部分隐藏）
        if current_email:
            masked_email = current_email[:3] + "*" * (len(current_email.split('@')[0]) - 3) + "@" + current_email.split('@')[1]
            print(f"当前邮箱: {masked_email}")
        if current_password:
            print(f"当前密码: {'*' * len(current_password)}")
        
        # 提示用户是否需要更新
        update = input("\n是否更新推特账户信息? (y/n，默认n): ").lower()
        if update != 'y':
            print("保持原有设置")
            input("\n按 Enter 继续...")
            return
        
        email = self.get_string_input("请输入推特邮箱: ")
        password = self.get_string_input("请输入推特密码: ")
        
        self.update_env_var("TWITTER_EMAIL", email)
        self.update_env_var("TWITTER_PASSWORD", password)
        
        print("✅ 推特账户信息已更新")
        input("\n按 Enter 继续...")
    
    def add_twitter_follows(self):
        """添加推特关注账号"""
        self.show_banner()
        print("👥 添加推特关注账号")
        
        # 显示已有的关注账号
        current_accounts = config.SOCIAL_CONFIG.get("twitter_accounts", [])
        if current_accounts:
            print("\n当前关注的账号:")
            for i, account in enumerate(current_accounts, 1):
                print(f"  {i}. {account}")
        else:
            print("\n当前未关注任何账号")
        
        print("\n请输入要关注的推特账号用户名（每行一个，输入空行结束）")
        print("注意: 只需输入用户名部分，无需输入完整URL或@符号")
        print("示例: 输入 'binance' 而不是 '@binance' 或 'https://x.com/binance'")
        print("---------------------------------------------------------------")
        
        accounts = []
        while True:
            account = input("> ")
            if not account:
                break
            
            # 清理输入，去除可能的URL部分和@符号
            # 处理形如 https://x.com/username 或 @username 的输入
            if 'x.com/' in account or 'twitter.com/' in account:
                # 从URL中提取用户名
                parts = account.split('/')
                account = parts[-1]  # 获取URL最后一部分
            
            # 去除开头的@符号
            if account.startswith('@'):
                account = account[1:]
            
            # 去除可能的查询参数
            if '?' in account:
                account = account.split('?')[0]
            
            if account:
                accounts.append(account)
                print(f"已添加: {account}")
            else:
                print("❌ 无效的用户名，请重新输入")
        
        if accounts:
            # 添加新账号并去重
            updated_accounts = list(set(current_accounts + accounts))
            
            # 更新配置
            self.update_config_list("SOCIAL_CONFIG", "twitter_accounts", updated_accounts)
            
            print(f"✅ 已添加 {len(accounts)} 个推特关注账号，现在共有 {len(updated_accounts)} 个关注账号")
        else:
            print("ℹ️ 未添加任何账号")
        
        input("\n按 Enter 继续...")
    
    def toggle_simulation_mode(self):
        """切换社交媒体模拟模式"""
        self.show_banner()
        
        # 获取当前设置
        current_mode = os.getenv("SOCIAL_SIMULATION_MODE", "false").lower() in ["true", "1", "yes", "y"]
        status = "已启用" if current_mode else "已禁用"
        
        print(f"🔄 社交媒体模拟模式设置 (当前: {status})")
        print("\n模拟模式说明:")
        print("  • 启用模拟模式: 生成随机的社交媒体分析数据，不连接真实Twitter")
        print("  • 禁用模拟模式: 尝试连接真实Twitter账户获取分析数据")
        print("\n注意: 如果无法连接到Twitter或登录失败，系统会自动使用模拟模式")
        
        new_mode = not current_mode
        new_status = "启用" if new_mode else "禁用"
        
        confirm = input(f"\n确定要{new_status}模拟模式吗? (y/n): ").lower()
        if confirm != 'y':
            print("\n操作已取消")
            input("\n按 Enter 继续...")
            return
        
        # 更新设置
        self.update_env_var("SOCIAL_SIMULATION_MODE", "true" if new_mode else "false")
        
        # 更新配置对象
        if hasattr(config, "SOCIAL_CONFIG"):
            config.SOCIAL_CONFIG["simulation_mode"] = new_mode
        
        print(f"\n✅ 已{new_status}社交媒体模拟模式")
        
        if not new_mode:
            print("\n提示: 系统将在下次分析时尝试连接Twitter")
            print("若Twitter登录失败，系统会自动切换回模拟模式")
        
        input("\n按 Enter 继续...")
    
    def show_ai_settings_menu(self):
        """显示AI设置菜单"""
        self.show_banner()
        print("🧠 AI决策系统设置")
        
        # 显示已有的配置
        current_api_key = os.getenv("DEEPSEEK_API_KEY", "")
        current_api_url = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1")
        current_api_path = os.getenv("DEEPSEEK_API_PATH", "/chat/completions")
        
        # 从配置中获取模型名称
        current_model = getattr(config, "AI_CONFIG", {}).get("model", "deepseek-chat")
        
        # 显示已有的值
        if current_api_key:
            masked_key = current_api_key[:4] + "*" * (len(current_api_key) - 8) + current_api_key[-4:] if len(current_api_key) > 8 else "*" * len(current_api_key)
            print(f"当前API Key: {masked_key}")
        print(f"当前模型名称: {current_model}")
        print(f"当前API URL: {current_api_url}")
        print(f"当前API 路径: {current_api_path}")
        
        # 提示用户是否需要更新
        update = input("\n是否更新AI设置? (y/n，默认n): ").lower()
        if update != 'y':
            print("保持原有设置")
            input("\n按 Enter 继续...")
            return
        
        api_key = self.get_string_input("请输入 AI模型 API Key: ")
        model_name = self.get_string_input("请输入模型名称 (默认: deepseek-chat): ", allow_empty=True) or "deepseek-chat"
        api_url = self.get_string_input("请输入 API 域名 (默认: https://api.deepseek.com): ", allow_empty=True) or "https://api.deepseek.com"
        api_path = self.get_string_input("请输入 API 路径 (默认: /chat/completions): ", allow_empty=True) or "/chat/completions"
        
        # 更新配置
        self.update_env_var("DEEPSEEK_API_KEY", api_key)
        self.update_env_var("DEEPSEEK_API_URL", f"{api_url}/v1")
        self.update_env_var("DEEPSEEK_API_PATH", api_path)
        
        # 更新配置文件中的模型名称
        self.update_config_value("AI_CONFIG", "model", model_name)
        
        print("✅ AI决策系统配置已更新")
        input("\n按 Enter 继续...")
    
    def show_auto_trading_menu(self):
        """显示自动交易设置菜单"""
        self.show_banner()
        print("🤖 自动交易设置")
        print("  1. 调整止盈止损线")
        print("  2. 设置交易类别")
        print("  3. 设置交易金额")
        print("  4. 选择交易对")
        print("  5. 添加自定义交易对")
        print("  6. 返回主菜单")
        print("\n" + "-" * 60)
        
        choice = self.get_choice(1, 6)
        
        if choice == 1:
            self.set_stop_levels()
        elif choice == 2:
            self.set_trading_timeframe()
        elif choice == 3:
            self.set_trade_amount()
        elif choice == 4:
            self.select_trading_pairs()
        elif choice == 5:
            self.add_custom_trading_pair()
        else:
            return
    
    def set_stop_levels(self):
        """设置止盈止损水平"""
        self.show_banner()
        print("🎯 调整止盈止损线")
        
        # 显示当前设置
        current_take_profit = os.getenv("TAKE_PROFIT", "2.0")
        current_stop_loss = os.getenv("STOP_LOSS", "3.0")
        
        print(f"\n当前止盈线: {current_take_profit}%")
        print(f"当前止损线: {current_stop_loss}%")
        
        print("\n  1. 调整止盈线")
        print("  2. 调整止损线")
        print("  3. 返回上级菜单")
        print("\n" + "-" * 60)
        
        choice = self.get_choice(1, 3)
        
        if choice == 1:
            value = self.get_float_input("请输入止盈百分比 (例如输入 2 表示 2%): ", min_value=0.1)
            self.update_env_var("TAKE_PROFIT", str(value))
            print(f"✅ 止盈线已设置为 {value}%")
            
        elif choice == 2:
            value = self.get_float_input("请输入止损百分比 (例如输入 3 表示 3%): ", min_value=0.1)
            self.update_env_var("STOP_LOSS", str(value))
            print(f"✅ 止损线已设置为 {value}%")
        
        else:
            return
        
        input("\n按 Enter 继续...")
    
    def set_trading_timeframe(self):
        """设置交易时间周期"""
        self.show_banner()
        print("⏱️ 设置交易类别")
        
        timeframes = {
            "1m": "超短期交易 (1分钟K线)",
            "5m": "短线交易 (5分钟K线)",
            "15m": "短中线交易 (15分钟K线)",
            "30m": "中短线交易 (30分钟K线)",
            "1h": "中线交易 (1小时K线)",
            "4h": "中长线交易 (4小时K线)",
            "1d": "长线交易 (1日K线)"
        }
        
        # 显示当前设置
        current_timeframe = config.TIMEFRAME if hasattr(config, "TIMEFRAME") else "1h"
        current_desc = timeframes.get(current_timeframe, "未知")
        
        print(f"\n当前交易类别: {current_desc} ({current_timeframe})")
        
        print("\n  1. 超短期交易 (1分钟K线)")
        print("  2. 短线交易 (5分钟K线)")
        print("  3. 短中线交易 (15分钟K线)")
        print("  4. 中短线交易 (30分钟K线)")
        print("  5. 中线交易 (1小时K线)")
        print("  6. 中长线交易 (4小时K线)")
        print("  7. 长线交易 (1日K线)")
        print("  8. 返回上级菜单")
        print("\n" + "-" * 60)
        
        choice = self.get_choice(1, 8)
        
        if choice == 8:
            return
        
        timeframe_map = {
            1: "1m",
            2: "5m",
            3: "15m",
            4: "30m",
            5: "1h",
            6: "4h",
            7: "1d"
        }
        
        selected_timeframe = timeframe_map[choice]
        
        # 更新配置
        self.update_config_value("TIMEFRAME", selected_timeframe)
        
        print(f"✅ 交易时间周期已设置为 {selected_timeframe}")
        input("\n按 Enter 继续...")
    
    def set_trade_amount(self):
        """设置交易金额"""
        self.show_banner()
        print("💰 设置交易金额")
        
        # 显示当前设置
        current_amount = os.getenv("MAX_TRADE_SIZE", "10")
        
        print(f"\n当前交易金额: {current_amount} USDT")
        
        # 提示用户输入新的交易金额
        amount = self.get_float_input("\n请输入新的交易金额 (USDT): ", min_value=1)
        
        # 更新配置
        self.update_env_var("MAX_TRADE_SIZE", str(int(amount)))
        
        print(f"\n✅ 交易金额已设置为 {int(amount)} USDT")
        input("\n按 Enter 继续...")
    
    def view_trade_records(self):
        """查看交易记录"""
        self.show_banner()
        print("📝 正在加载交易记录...")
        
        # 导入交易记录器
        from trading.trade_recorder import TradeRecorder
        trade_recorder = TradeRecorder()
        
        # 获取交易历史
        trades = trade_recorder.get_trade_history(limit=10)
        
        self.show_banner()
        print("📝 最近交易记录")
        
        if not trades:
            print("\n暂无交易记录")
        else:
            print("\n" + "-" * 80)
            print(f"{'交易对':<10} {'方向':<6} {'状态':<8} {'入场价格':<12} {'出场价格':<12} {'盈亏':<10} {'入场时间':<20}")
            print("-" * 80)
            
            for trade in trades:
                symbol = trade['symbol']
                side = trade['side'].upper()
                status = trade['status']
                entry_price = f"{float(trade['entry_price']):.4f}"
                exit_price = f"{float(trade['exit_price']):.4f}" if trade['exit_price'] else "N/A"
                
                profit_loss = "N/A"
                if status == 'CLOSED':
                    pl = float(trade['profit_loss'])
                    pl_pct = float(trade['profit_loss_pct'])
                    profit_loss = f"{pl:.2f} ({pl_pct:.2f}%)"
                
                entry_time = trade['entry_time']
                
                print(f"{symbol:<10} {side:<6} {status:<8} {entry_price:<12} {exit_price:<12} {profit_loss:<10} {entry_time}")
        
        print("\n" + "-" * 80)
        input("\n按 Enter 返回主菜单...")
    
    def generate_reports(self):
        """生成交易报告"""
        self.show_banner()
        print("📊 生成交易报告")
        print("  1. 生成绩效报告")
        print("  2. 生成交易列表报告")
        print("  3. 生成全部报告")
        print("  4. 返回主菜单")
        print("\n" + "-" * 60)
        
        choice = self.get_choice(1, 4)
        
        if choice == 4:
            return
        
        print("\n🔄 正在生成报告...")
        
        # 导入报告生成器
        from report import TradingReportGenerator
        report_generator = TradingReportGenerator()
        
        if choice == 1:
            report_file = report_generator.generate_performance_report()
            report_type = "绩效报告"
        elif choice == 2:
            report_file = report_generator.generate_trade_list_report()
            report_type = "交易列表报告"
        else:
            report_file1 = report_generator.generate_performance_report()
            report_file2 = report_generator.generate_trade_list_report()
            report_file = report_file1  # 用于显示
            report_type = "全部报告"
        
        if report_file:
            print(f"\n✅ {report_type}已生成: {report_file}")
        else:
            print(f"\n❌ 生成{report_type}失败")
        
        input("\n按 Enter 返回主菜单...")
    
    def close_all_positions(self):
        """关闭所有头寸"""
        self.show_banner()
        print("⚠️ 关闭所有头寸")
        confirm = input("确定要关闭所有交易头寸吗? (y/n): ")
        
        if confirm.lower() != 'y':
            print("\n❌ 操作已取消")
            input("\n按 Enter 返回主菜单...")
            return
        
        print("\n🔄 正在关闭所有头寸...")
        
        try:
            # 导入所需模块
            from exchanges.exchange_client import ExchangeClientFactory
            from trading.trade_recorder import TradeRecorder
            from trading.auto_trader import AutoTrader
            import config
            
            # 创建所需对象
            exchange_client = ExchangeClientFactory.create_client(config.EXCHANGE)
            trade_recorder = TradeRecorder()
            auto_trader = AutoTrader(
                exchange_client=exchange_client,
                trade_recorder=trade_recorder,
                config=config.__dict__
            )
            
            # 关闭所有头寸
            closed_trades = auto_trader.close_all_positions("用户手动平仓")
            
            if closed_trades:
                print(f"\n✅ 成功关闭 {len(closed_trades)} 个头寸:")
                for trade in closed_trades:
                    print(f"  • {trade['symbol']} @ {trade['price']}")
            else:
                print("\nℹ️ 没有需要关闭的头寸")
            
        except Exception as e:
            print(f"\n❌ 关闭头寸出错: {str(e)}")
        
        input("\n按 Enter 返回主菜单...")
    
    def update_env_var(self, key, value):
        """更新环境变量"""
        env_file = ".env"
        
        # 读取现有.env文件
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = []
        
        # 查找并更新键值对
        key_found = False
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith('#'):
                if line.strip().split('=')[0] == key:
                    lines[i] = f"{key}={value}\n"
                    key_found = True
                    break
        
        # 如果键不存在，添加新行
        if not key_found:
            lines.append(f"{key}={value}\n")
        
        # 写回文件
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
            
        # 更新运行时环境变量
        os.environ[key] = value
    
    def update_config_value(self, section, key, value):
        """更新配置文件中的值"""
        # 实现更新配置的逻辑，这里我们直接修改内存中的配置
        if hasattr(config, section) and isinstance(getattr(config, section), dict):
            getattr(config, section)[key] = value
        else:
            setattr(config, key, value)
    
    def update_config_list(self, section, key, value_list):
        """更新配置文件中的列表"""
        if hasattr(config, section) and isinstance(getattr(config, section), dict):
            getattr(config, section)[key] = value_list

    def select_trading_pairs(self):
        """选择默认交易对"""
        self.show_banner()
        print("🔄 选择交易对")
        
        # 定义默认可选交易对
        available_pairs = [
            "BTC/USDT",
            "ETH/USDT",
            "BNB/USDT",
            "DOGE/USDT",
            "SOL/USDT"
        ]
        
        # 获取当前选择的交易对
        current_pairs = config.TRADING_PAIRS if hasattr(config, "TRADING_PAIRS") else []
        
        print("\n当前选择的交易对:")
        if current_pairs:
            for i, pair in enumerate(current_pairs, 1):
                print(f"  {i}. {pair}")
        else:
            print("  未选择任何交易对")
        
        print("\n可选的默认交易对:")
        for i, pair in enumerate(available_pairs, 1):
            status = "✓" if pair in current_pairs else " "
            print(f"  {i}. [{status}] {pair}")
        
        print("\n选择操作:")
        print("  1. 添加交易对")
        print("  2. 移除交易对")
        print("  3. 返回上级菜单")
        
        choice = self.get_choice(1, 3)
        
        if choice == 3:
            return
        
        if choice == 1:
            # 添加交易对
            print("\n请选择要添加的交易对 (输入数字，多个用逗号分隔):")
            selection = input("> ")
            
            try:
                # 解析用户输入
                indices = [int(x.strip()) for x in selection.split(",")]
                
                # 验证索引范围
                valid_indices = [i for i in indices if 1 <= i <= len(available_pairs)]
                
                if not valid_indices:
                    print("❌ 无效的选择")
                    input("\n按 Enter 继续...")
                    return
                
                # 添加选择的交易对
                selected_pairs = [available_pairs[i-1] for i in valid_indices]
                updated_pairs = list(set(current_pairs + selected_pairs))
                
                # 更新配置
                config.TRADING_PAIRS = updated_pairs
                
                added_pairs = [pair for pair in selected_pairs if pair not in current_pairs]
                if added_pairs:
                    print(f"\n✅ 已添加交易对: {', '.join(added_pairs)}")
                else:
                    print("\nℹ️ 选择的交易对已在列表中")
            
            except ValueError:
                print("❌ 无效的输入，请输入数字")
        
        elif choice == 2:
            # 移除交易对
            if not current_pairs:
                print("\nℹ️ 当前没有选择的交易对")
                input("\n按 Enter 继续...")
                return
            
            print("\n请选择要移除的交易对 (输入数字，多个用逗号分隔):")
            for i, pair in enumerate(current_pairs, 1):
                print(f"  {i}. {pair}")
            
            selection = input("> ")
            
            try:
                # 解析用户输入
                indices = [int(x.strip()) for x in selection.split(",")]
                
                # 验证索引范围
                valid_indices = [i for i in indices if 1 <= i <= len(current_pairs)]
                
                if not valid_indices:
                    print("❌ 无效的选择")
                    input("\n按 Enter 继续...")
                    return
                
                # 移除选择的交易对
                pairs_to_remove = [current_pairs[i-1] for i in valid_indices]
                updated_pairs = [pair for pair in current_pairs if pair not in pairs_to_remove]
                
                # 更新配置
                config.TRADING_PAIRS = updated_pairs
                
                print(f"\n✅ 已移除交易对: {', '.join(pairs_to_remove)}")
            
            except ValueError:
                print("❌ 无效的输入，请输入数字")
        
        input("\n按 Enter 继续...")

    def add_custom_trading_pair(self):
        """添加自定义交易对"""
        self.show_banner()
        print("➕ 添加自定义交易对")
        
        # 获取当前选择的交易对
        current_pairs = config.TRADING_PAIRS if hasattr(config, "TRADING_PAIRS") else []
        
        print("\n当前选择的交易对:")
        if current_pairs:
            for i, pair in enumerate(current_pairs, 1):
                print(f"  {i}. {pair}")
        else:
            print("  未选择任何交易对")
        
        print("\n请输入要添加的自定义交易对，格式为: 币种/计价币 (例如: PEPE/USDC)")
        print("可以一次输入多个交易对，用逗号分隔 (例如: PEPE/USDC, SHIB/USDT)")
        print("注意: 请确保交易对在交易所中存在，否则交易将失败")
        
        custom_pairs = input("\n> ")
        
        if not custom_pairs.strip():
            print("❌ 输入为空，未添加任何交易对")
            input("\n按 Enter 继续...")
            return
        
        # 解析用户输入
        pairs_list = [pair.strip() for pair in custom_pairs.split(",")]
        valid_pairs = []
        
        # 验证交易对格式
        for pair in pairs_list:
            # 检查基本格式
            if '/' in pair:
                base, quote = pair.split('/')
                if base and quote:
                    valid_pairs.append(pair.upper())  # 转换为大写
                else:
                    print(f"❌ 无效交易对格式: {pair}")
            else:
                print(f"❌ 无效交易对格式: {pair} (缺少 '/' 分隔符)")
        
        if not valid_pairs:
            print("❌ 未提供有效的交易对")
            input("\n按 Enter 继续...")
            return
        
        # 确认添加
        print("\n将添加以下交易对:")
        for pair in valid_pairs:
            print(f"  • {pair}")
        
        confirm = input("\n确认添加这些交易对? (y/n): ").lower()
        if confirm != 'y':
            print("\n❌ 操作已取消")
            input("\n按 Enter 继续...")
            return
        
        # 添加新交易对并去重
        updated_pairs = list(set(current_pairs + valid_pairs))
        
        # 更新配置
        config.TRADING_PAIRS = updated_pairs
        
        # 获取实际添加的交易对（过滤掉已存在的）
        added_pairs = [pair for pair in valid_pairs if pair not in current_pairs]
        
        if added_pairs:
            print(f"\n✅ 已添加交易对: {', '.join(added_pairs)}")
        else:
            print("\nℹ️ 所有交易对已在列表中")
        
        input("\n按 Enter 继续...")

    def run(self):
        """运行菜单"""
        while True:
            choice = self.show_main_menu()
            
            if choice == 0:
                # 退出程序
                print("👋 感谢使用加密货币量化交易系统!")
                print("正在退出...\n")
                break
            
            elif choice == 1:
                # 启动交易系统
                self.show_banner()
                print("🚀 正在启动交易系统...")
                time.sleep(1)
                
                # 导入并运行交易系统
                try:
                    from main import CryptoQuantTrader
                    trader = CryptoQuantTrader()
                    
                    print("\n✅ 交易系统已启动，按 Ctrl+C 停止")
                    try:
                        trader.start()
                    except KeyboardInterrupt:
                        print("\n⚠️ 用户中断，交易系统已停止")
                    except Exception as e:
                        print(f"\n❌ 交易系统出错: {str(e)}")
                except Exception as e:
                    print(f"\n❌ 无法启动交易系统: {str(e)}")
            
            elif choice == 2:
                # 仅运行市场分析
                self.show_banner()
                print("🔍 正在运行市场分析...")
                time.sleep(1)
                
                # 导入并运行市场分析
                try:
                    from analysis.market_analysis import MarketAnalyzer
                    from analysis.social_analysis import SocialMediaAnalyzer
                    from analysis.ai_analysis import AIAnalyzer
                    
                    # 市场分析
                    market_analyzer = MarketAnalyzer()
                    market_summary = market_analyzer.get_market_summary()
                    
                    # 显示市场分析结果
                    print("\n📊 市场分析结果:")
                    for symbol, timeframes in market_summary["symbols"].items():
                        print(f"\n{symbol}:")
                        for timeframe, analysis in timeframes.items():
                            print(f"\n{timeframe}周期:")
                            print(f"当前价格: {analysis['current_price']}")
                            print("技术指标:")
                            for indicator, value in analysis['indicators'].items():
                                print(f"- {indicator}: {value}")
                            print("交易信号:")
                            signals = analysis['signals']
                            if signals['buy']:
                                print(f"- 买入信号 (强度: {signals['strength']})")
                                print(f"- 原因: {', '.join(signals['reason'])}")
                            if signals['sell']:
                                print(f"- 卖出信号 (强度: {abs(signals['strength'])})")
                                print(f"- 原因: {', '.join(signals['reason'])}")
                    
                    # AI分析
                    print("\n🤖 正在运行AI分析...")
                    ai_analyzer = AIAnalyzer()
                    ai_summary = ai_analyzer.get_ai_summary()
                    
                    # 显示AI分析结果
                    print("\n📈 AI分析结果:")
                    for symbol, analysis in ai_summary["symbols"].items():
                        print(f"\n{symbol}:")
                        print(f"趋势预测: {analysis['trend']}")
                        print(f"置信度: {analysis['confidence']}")
                        print(f"建议操作: {analysis['action']}")
                        print(f"理由: {analysis['reason']}")
                    
                    # 社交媒体分析
                    print("\n💬 正在分析社交媒体...")
                    social_analyzer = SocialMediaAnalyzer()
                    social_summary = social_analyzer.get_social_summary()
                    
                    # 显示社交媒体分析结果
                    print("\n📱 社交媒体分析结果:")
                    for symbol, analysis in social_summary["symbols"].items():
                        print(f"\n{symbol}:")
                        print(f"情感得分: {analysis['sentiment_score']}")
                        print(f"市场情绪: {analysis['market_sentiment']}")
                        print(f"热门话题: {', '.join(analysis['hot_topics'])}")
                        print(f"重要新闻: {', '.join(analysis['important_news'])}")
                    
                    print("\n✅ 分析完成")
                except Exception as e:
                    print(f"\n❌ 市场分析出错: {str(e)}")
                
            elif choice == 3:
                # 交易所设置
                self.show_exchange_menu()
            
            elif choice == 4:
                # 社交媒体设置
                self.show_social_media_menu()
            
            elif choice == 5:
                # AI决策系统设置
                self.show_ai_settings_menu()
            
            elif choice == 6:
                # 自动交易设置
                self.show_auto_trading_menu()
            
            elif choice == 7:
                # 查看交易记录
                self.view_trade_records()
            
            elif choice == 8:
                # 生成交易报告
                self.generate_reports()
            
            elif choice == 9:
                # 关闭所有头寸
                self.close_all_positions()
            
            # 每次操作后暂停
            input("\n按 Enter 继续...")

# 主菜单循环
def run_menu():
    """运行菜单系统"""
    menu = Menu()
    
    while True:
        choice = menu.show_main_menu()
        
        if choice == 0:
            # 退出程序
            menu.show_banner()
            print("👋 感谢使用加密货币量化交易系统!")
            print("正在退出...\n")
            break
            
        elif choice == 1:
            # 启动交易系统
            menu.show_banner()
            print("🚀 正在启动交易系统...")
            time.sleep(1)
            
            # 导入并运行交易系统
            from main import CryptoQuantTrader
            trader = CryptoQuantTrader()
            
            print("\n✅ 交易系统已启动，按 Ctrl+C 停止")
            try:
                trader.start()
            except KeyboardInterrupt:
                print("\n⚠️ 用户中断，交易系统已停止")
            except Exception as e:
                print(f"\n❌ 交易系统出错: {str(e)}")
            
            input("\n按 Enter 返回主菜单...")
            
        elif choice == 2:
            # 仅运行市场分析
            menu.show_banner()
            print("🔍 正在运行市场分析...")
            time.sleep(1)
            
            # 导入并运行市场分析
            import argparse
            from main import CryptoQuantTrader
            
            args = argparse.Namespace()
            args.analysis_only = True
            trader = CryptoQuantTrader(args)
            
            try:
                trader.run_analysis()
                print("\n✅ 市场分析完成")
            except Exception as e:
                print(f"\n❌ 市场分析出错: {str(e)}")
            
            input("\n按 Enter 返回主菜单...")
            
        elif choice == 3:
            # 交易所设置
            menu.show_exchange_menu()
            
        elif choice == 4:
            # 社交媒体设置
            menu.show_social_media_menu()
            
        elif choice == 5:
            # AI决策系统设置
            menu.show_ai_settings_menu()
            
        elif choice == 6:
            # 自动交易设置
            menu.show_auto_trading_menu()
            
        elif choice == 7:
            # 查看交易记录
            menu.view_trade_records()
            
        elif choice == 8:
            # 生成交易报告
            menu.generate_reports()
            
        elif choice == 9:
            # 关闭所有头寸
            menu.close_all_positions()


if __name__ == "__main__":
    run_menu() 