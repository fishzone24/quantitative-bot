#!/bin/bash

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

echo -e "${BLUE}=====================================${NC}"
echo -e "${GREEN}CryptoQuantTrader 自动安装脚本${NC}"
echo -e "${BLUE}=====================================${NC}"

# 检查系统环境
echo -e "${YELLOW}正在检查系统环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}未检测到Python3，开始安装...${NC}"
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv
else
    echo -e "${GREEN}检测到Python3: $(python3 --version)${NC}"
fi

if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}未检测到pip3，请先安装pip3${NC}"
    exit 1
fi

# 安装Chrome浏览器
echo -e "${YELLOW}安装Chrome浏览器...${NC}"
if [ -f /etc/debian_version ]; then
    # Debian/Ubuntu系统
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
    sudo apt-get update
    sudo apt-get install -y google-chrome-stable
elif [ -f /etc/redhat-release ]; then
    # CentOS/RHEL系统
    sudo dnf install -y chromium chromium-headless chromium-libs
else
    echo -e "${RED}不支持的操作系统${NC}"
    exit 1
fi

# 检查Chrome安装
if ! command -v google-chrome &> /dev/null && ! command -v chromium &> /dev/null; then
    echo -e "${RED}Chrome浏览器安装失败${NC}"
    exit 1
fi

# 创建项目目录
echo -e "${YELLOW}创建项目目录...${NC}"
if [ -d ~/crypto-quant-trader ]; then
    echo -e "${YELLOW}检测到已存在的安装目录，正在删除...${NC}"
    rm -rf ~/crypto-quant-trader
fi

# 询问是否从GitHub克隆
echo -e "${YELLOW}您希望如何获取代码?${NC}"
echo "1) 从GitHub克隆最新代码 (推荐)"
echo "2) 使用当前目录的代码 (如果已经有代码)"
read -p "请选择 [1/2]: " clone_choice

if [ "$clone_choice" = "1" ]; then
    # 检查git是否安装
    if ! command -v git &> /dev/null; then
        echo -e "${RED}未检测到Git，开始安装...${NC}"
        sudo apt install -y git
    fi
    
    # 克隆代码库
    echo -e "${YELLOW}正在从GitHub克隆代码...${NC}"
    cd ~
    rm -rf temp_quant_bot
    mkdir temp_quant_bot
    cd temp_quant_bot
    git clone https://github.com/fishzone24/quantitative-bot.git .
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}克隆失败! 请检查网络连接或GitHub仓库地址。${NC}"
        cd ~
        rm -rf temp_quant_bot
        exit 1
    fi
    
    # 移动到目标目录
    echo -e "${YELLOW}正在移动文件到目标目录...${NC}"
    mkdir -p ~/crypto-quant-trader
    mv * ~/crypto-quant-trader/
    mv .* ~/crypto-quant-trader/ 2>/dev/null || true
    cd ~
    rm -rf temp_quant_bot
    cd ~/crypto-quant-trader
else
    echo -e "${GREEN}使用当前目录的代码继续安装。${NC}"
    mkdir -p ~/crypto-quant-trader
    cd ~/crypto-quant-trader
fi

# 创建并激活虚拟环境
echo -e "${YELLOW}正在创建Python虚拟环境...${NC}"
python3 -m venv venv
source venv/bin/activate

# 检查Python版本
echo -e "${YELLOW}检查Python版本...${NC}"
py_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}Python版本: ${py_version}${NC}"

# 安装依赖
echo -e "${YELLOW}安装依赖...${NC}"
if [[ "$py_version" == "3.12" ]]; then
    echo -e "${YELLOW}检测到Python 3.12，使用兼容性设置...${NC}"
    # Python 3.12特定的依赖安装
    pip install wheel
    pip install numpy matplotlib 
    pip install pandas>=2.1.1 scipy>=1.11.0
    # 安装其他依赖，但排除已安装的包
    grep -v "pandas\|numpy\|matplotlib\|scipy\|ta-lib-python" requirements.txt > temp_requirements.txt
    pip install -r temp_requirements.txt
    rm temp_requirements.txt
else
    # 标准安装方式
    pip install -r requirements.txt --no-cache-dir
fi

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}标准安装失败，尝试替代安装方法...${NC}"
    pip install wheel
    pip install numpy pandas>=2.1.1 matplotlib scipy>=1.11.0
    pip install ccxt python-binance okx
    pip install selenium webdriver-manager textblob nltk
    pip install requests json5 python-dotenv
    pip install pandas-ta scikit-learn
    pip install tqdm colorama
fi

# 设置环境变量
echo -e "${YELLOW}正在设置环境变量...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}已创建.env文件，请编辑此文件并配置您的API密钥。${NC}"
    echo -e "${YELLOW}提示: 使用 nano .env 命令编辑配置文件${NC}"
else
    echo -e "${GREEN}检测到已存在的.env文件。${NC}"
fi

# 设置执行权限
echo -e "${YELLOW}设置脚本执行权限...${NC}"
chmod +x run.py

# 创建快捷脚本
echo -e "${YELLOW}创建启动脚本...${NC}"
cat > ~/start-quant-trader.sh << EOF
#!/bin/bash
cd ~/crypto-quant-trader
source venv/bin/activate
python run.py
EOF

chmod +x ~/start-quant-trader.sh

# 完成
echo -e "${BLUE}=====================================${NC}"
echo -e "${GREEN}安装完成! 您可以通过以下方式启动:${NC}"
echo -e "${YELLOW}方式1: ${NC}cd ~/crypto-quant-trader && source venv/bin/activate && python run.py"
echo -e "${YELLOW}方式2: ${NC}~/start-quant-trader.sh"
echo -e "${BLUE}=====================================${NC}"
echo -e "${YELLOW}首次使用前，请确保编辑.env文件配置您的API密钥。${NC}"
echo -e "${YELLOW}使用命令: ${NC}nano ~/crypto-quant-trader/.env"
echo -e "${BLUE}=====================================${NC}" 