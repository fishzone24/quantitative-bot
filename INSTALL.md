# CryptoQuantTrader 一键安装指南

## 简介

本文档提供了在 Ubuntu VPS 上一键安装 CryptoQuantTrader 量化交易系统的方法。通过简单的命令，您可以快速部署整个系统，无需手动执行复杂的安装步骤。

## 系统要求

- Ubuntu 18.04 或更高版本
- 至少 1GB RAM
- 至少 10GB 磁盘空间
- 互联网连接

## 一键安装命令

方法一：使用curl直接下载并执行安装脚本（推荐）：

```bash
curl -fsSL https://raw.githubusercontent.com/fishzone24/quantitative-bot/main/install-quan-bot.sh -o install-quan-bot.sh && chmod +x install-quan-bot.sh && ./install-quan-bot.sh
```

方法二：逐步手动安装：

1. 下载安装脚本：
```bash
curl -fsSL https://raw.githubusercontent.com/fishzone24/quantitative-bot/main/install-quan-bot.sh -o install-quan-bot.sh
```

2. 给脚本添加执行权限：
```bash
chmod +x install-quan-bot.sh
```

3. 运行安装脚本：
```bash
./install-quan-bot.sh
```

安装过程中，脚本将引导您：
1. 自动检查并安装必要的系统依赖（Python3、Git等）
2. 从GitHub克隆最新代码
3. 创建并配置 Python 虚拟环境
4. 安装所有必要的 Python 依赖包
5. 设置环境配置文件
6. 创建便捷的启动脚本

## 安装后配置

安装完成后，您需要配置您的 API 密钥和交易参数：

1. 编辑环境配置文件：
   ```bash
   nano ~/crypto-quant-trader/.env
   ```
   
2. 在配置文件中填入您的交易所 API 密钥和其他必要信息。

## 启动系统

安装完成后，您可以通过以下两种方式启动系统：

### 方式一：使用快捷脚本

```bash
~/start-quant-trader.sh
```

### 方式二：手动启动

```bash
cd ~/crypto-quant-trader
source venv/bin/activate
python run.py
```

## 常见问题

**Q: 安装过程中出现"克隆失败"错误怎么办？**

A: 可能是网络连接问题或GitHub访问受限。请确保您的服务器能够正常访问GitHub，或者尝试使用代理。

**Q: 如何更新到最新版本？**

A: 进入项目目录，然后拉取最新代码：
```bash
cd ~/crypto-quant-trader
git pull
```

**Q: 如何查看运行日志？**

A: 日志文件存储在 `~/crypto-quant-trader/data/logs/` 目录下。

## 支持与帮助

如有任何问题，请访问项目 GitHub 页面提交 Issue 或查看更多文档。 