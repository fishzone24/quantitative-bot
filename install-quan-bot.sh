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

# 创建项目目录
echo -e "${YELLOW}创建项目目录...${NC}"
if [ -d ~/crypto-quant-trader ]; then
    echo -e "${YELLOW}检测到已存在的安装目录，正在删除...${NC}"
    rm -rf ~/crypto-quant-trader
fi
mkdir -p ~/crypto-quant-trader
cd ~/crypto-quant-trader

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
    git clone https://github.com/fishzone24/quantitative-bot.git .
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}克隆失败! 请检查网络连接或GitHub仓库地址。${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}使用当前目录的代码继续安装。${NC}"
fi

# 创建并激活虚拟环境
echo -e "${YELLOW}正在创建Python虚拟环境...${NC}"
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo -e "${YELLOW}正在安装依赖...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}依赖安装失败，请检查错误信息。${NC}"
    exit 1
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