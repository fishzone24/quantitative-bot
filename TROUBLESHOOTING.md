# 故障排除指南

## 安装依赖问题

### pandas安装失败

如果在安装pandas时遇到以下错误：

```
Preparing metadata (pyproject.toml) did not run successfully...
error: subprocess-exited-with-error
```

这可能是因为您的Python版本太新，尝试以下解决方法：

1. 指定使用预编译的二进制包而不是从源代码构建：

```bash
pip install pandas==2.0.3 --only-binary=pandas
```

2. 如果使用的是Python 3.12，考虑降级到Python 3.10或3.11：

```bash
# 在Ubuntu/Debian上
sudo apt-get install python3.10 python3.10-venv

# 创建新的虚拟环境
python3.10 -m venv venv_py310
source venv_py310/bin/activate
```

### 安装ta-lib问题

如果ta-lib安装失败，可能是因为缺少构建依赖：

1. 在Ubuntu/Debian上安装依赖：

```bash
sudo apt-get update
sudo apt-get install -y build-essential
```

2. 尝试使用替代方案：

```bash
pip uninstall ta-lib-python
pip install pandas-ta
```

然后修改代码，使用pandas-ta替代ta-lib。

## 运行问题

### 找不到模块

如果遇到"No module named 'xxx'"错误：

1. 确保已安装所有依赖：

```bash
pip install -r requirements.txt
```

2. 检查虚拟环境是否激活：

```bash
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 交易所API错误

1. 确保已正确设置API密钥和密码：

```bash
# 编辑.env文件
nano .env
```

2. 对于OKX，确保设置了密码短语：

```
OKX_API_KEY=your_api_key
OKX_API_SECRET=your_api_secret
OKX_PASSPHRASE=your_passphrase
```

### Chrome浏览器问题

如果社交分析功能遇到Chrome相关错误：

1. 手动安装Chrome：

```bash
# Debian/Ubuntu
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt-get update
sudo apt-get install -y google-chrome-stable

# CentOS/RHEL
sudo dnf install -y chromium
```

2. 检查Chrome是否安装成功：

```bash
google-chrome --version
# 或
chromium --version
```

## 其他问题

如果遇到其他问题，请参考详细的错误日志，或联系开发者提供支持。 