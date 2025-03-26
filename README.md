# 🚀 CryptoQuantTrader - 加密货币量化交易系统

一个功能强大的自动化量化交易系统，专为加密货币市场设计，支持币安(Binance)、OKX等中心化交易所。

## ✨ 主要功能

### 1. 📊 交易对监控系统
- 支持多交易对同时监控
- 实时价格数据轮询与更新

### 2. 📈 技术分析
- RSI、MACD、布林带等指标计算
- 价格波动率与成交量分析
- 短期(6h)和长期(24h)趋势分析
- 自动计算支撑位和阻力位

### 3. 🐦 社交媒体分析
- 币安Twitter推文实时分析
- 15分钟更新一次
- 情感分析和市场影响评估
- 重要公告和关键词识别

### 4. 🤖 自动交易
- 智能买入/卖出信号执行
- 完善的风险管理：
  - 止损设置(默认3%)
  - 止盈设置(默认2%)
  - 动态止损策略
- 固定交易量管理(默认10单位)

### 5. 📝 交易记录系统
- CSV格式保存完整交易记录
- 详细信息包括：交易ID、交易对、操作类型、交易量、入场/出场价格和时间、盈亏情况
- 交易统计分析和性能评估

### 6. 🧠 AI决策系统
- 集成DeepSeek API进行智能分析
- 综合考量技术指标、市场状态和社交媒体信息
- 提供买入/卖出/观望建议
- 包含置信度和详细分析理由

### 7. 📱 交互式菜单系统
- 用户友好的菜单界面
- 交易所和API设置向导
- 社交媒体账户配置
- 止盈止损和交易类别调整
- 一键启动交易或分析系统

## 🚀 一键安装 (Ubuntu VPS)

如果您使用Ubuntu系统，可以使用我们提供的一键安装脚本快速部署：

```bash
curl -fsSL https://raw.githubusercontent.com/fishzone24/quantitative-bot/main/install-quan-bot.sh -o install-quan-bot.sh && chmod +x install-quan-bot.sh && ./install-quan-bot.sh
```

此命令将自动完成所有安装步骤，包括：
- 检查并安装系统依赖
- 克隆项目代码
- 设置Python环境
- 安装所有需要的包
- 创建配置文件
- 设置启动脚本

详细说明请参考 [INSTALL.md](INSTALL.md) 文件。

## 🛠️ 安装与配置

1. 克隆此仓库
```
git clone https://github.com/fishzone24/crypto-quant-trader.git
cd crypto-quant-trader
```

2. 安装依赖
```
pip install -r requirements.txt
```

3. 配置环境变量
复制`.env.example`文件为`.env`，并填写您的API密钥和其他配置信息。
```
cp .env.example .env
```

4. 配置交易参数
编辑`config.py`文件，根据您的需求设置交易对、交易策略和风险管理参数。

## 🚀 使用方法

### 简易启动

使用交互式菜单启动系统：
```
python run.py
```

### 基本命令

如果您喜欢命令行界面，可以使用以下命令：

启动完整的交易系统（包含自动交易功能）：
```
python main.py
```

仅运行市场分析而不执行交易：
```
python main.py --analysis-only
```

启动交互式菜单系统：
```
python main.py --menu
```

查看可用的命令行选项：
```
python main.py --help
```

### 交互式菜单操作

启动交互式菜单后，您可以：

1. **交易所设置**
   - 选择交易所(Binance/OKX)
   - 配置API密钥

2. **社交媒体设置**
   - 连接推特账户
   - 添加关注账号

3. **AI决策系统设置**
   - 配置API密钥
   - 设置模型名称与API地址

4. **自动交易设置**
   - 调整止盈止损线
   - 设置交易类别和时间周期
     - 超短期(1分钟K线)
     - 短线(5分钟K线)
     - 短中线(15分钟K线)
     - 中短线(30分钟K线)
     - 中线(1小时K线)
     - 中长线(4小时K线)
     - 长线(1日K线)

5. **交易管理**
   - 查看交易记录
   - 生成交易报告
   - 关闭所有头寸

### 生成交易报告

生成绩效报告和交易历史：
```
python report.py
```

仅生成绩效报告：
```
python report.py --performance
```

仅生成交易列表报告：
```
python report.py --trades
```

指定报告时间范围：
```
python report.py --performance --period daily
```

查看报告工具的所有选项：
```
python report.py --help
```

### 管理交易头寸

查看交易历史记录：
```
python main.py --list-trades
```

关闭所有头寸：
```
python main.py --close-all
```

### 目录结构

```
crypto-quant-trader/
├── analysis/              # 分析模块
│   ├── technical_analysis.py  # 技术分析
│   ├── social_analysis.py     # 社交媒体分析
│   └── ai_analysis.py         # AI决策系统
├── exchanges/             # 交易所API模块
│   └── exchange_client.py     # 交易所客户端
├── trading/               # 交易模块
│   ├── auto_trader.py         # 自动交易
│   └── trade_recorder.py      # 交易记录
├── data/                  # 数据目录
│   ├── trade_records/         # 交易记录
│   ├── logs/                  # 日志文件
│   └── reports/               # 生成的报告
├── config.py              # 配置文件
├── main.py                # 主程序
├── menu.py                # 交互式菜单系统
├── report.py              # 报告工具
├── run.py                 # 启动脚本
├── requirements.txt       # 依赖包列表
└── .env.example           # 环境变量示例
```

## 🔧 高级配置

### 自定义交易策略

您可以通过修改`config.py`文件中的参数来调整交易策略：

```python
# 风险管理配置
STOP_LOSS = 3.0     # 止损百分比
TAKE_PROFIT = 2.0   # 止盈百分比
USE_DYNAMIC_SL = True  # 是否使用动态止损

# 技术分析参数
TA_CONFIG = {
    "RSI": {
        "period": 14,
        "overbought": 70,
        "oversold": 30
    },
    "MACD": {
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9
    },
    # ...其他参数
}
```

### 添加新的交易所

如果需要添加新的交易所支持，可以在`exchanges/exchange_client.py`中扩展`ExchangeClient`类：

1. 创建一个新的交易所客户端类，继承自`ExchangeClient`
2. 实现所有必需的方法
3. 在`ExchangeClientFactory`中添加新交易所的支持

### 定制AI分析系统

可以修改`analysis/ai_analysis.py`中的提示词模板，以获得更适合您交易风格的AI建议。

## ⚠️ 风险提示

加密货币交易涉及高风险，本系统不构成投资建议。请在使用前充分了解相关风险，并自行承担所有交易结果。建议在实盘交易前，先在模拟环境中测试系统性能。

## �� 许可证

MIT License 