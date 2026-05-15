#!/bin/bash

# A股量化交易选股系统 - 环境安装脚本
set -e

echo "=========================================="
echo "  A股量化交易选股系统 - 环境安装"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Python 版本
echo -e "${YELLOW}[1/6] 检查 Python 版本...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
        echo -e "${GREEN}✓ Python $PYTHON_VERSION 已安装${NC}"
    else
        echo -e "${RED}✗ Python 版本过低 (需要 3.10+)${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Python3 未安装${NC}"
    exit 1
fi

# 检查 Node.js 版本
echo ""
echo -e "${YELLOW}[2/6] 检查 Node.js 版本...${NC}"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version | sed 's/v//')
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)
    
    if [ "$NODE_MAJOR" -ge 18 ]; then
        echo -e "${GREEN}✓ Node.js $NODE_VERSION 已安装${NC}"
    else
        echo -e "${RED}✗ Node.js 版本过低 (需要 18+)${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Node.js 未安装${NC}"
    exit 1
fi

# 创建 Python 虚拟环境
echo ""
echo -e "${YELLOW}[3/6] 创建 Python 虚拟环境...${NC}"
if [ ! -d "backend/venv" ]; then
    python3 -m venv backend/venv
    echo -e "${GREEN}✓ 虚拟环境创建成功${NC}"
else
    echo -e "${GREEN}✓ 虚拟环境已存在${NC}"
fi

# 安装 Python 依赖
echo ""
echo -e "${YELLOW}[4/6] 安装 Python 依赖...${NC}"
source backend/venv/Scripts/activate 2>/dev/null || source backend/venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
echo -e "${GREEN}✓ Python 依赖安装完成${NC}"

# 安装前端依赖
echo ""
echo -e "${YELLOW}[5/6] 安装前端依赖...${NC}"
cd frontend && npm install
cd ..
echo -e "${GREEN}✓ 前端依赖安装完成${NC}"

# 提示配置环境变量
echo ""
echo -e "${YELLOW}[6/6] 配置环境变量...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ 已创建 .env 文件，请编辑它并填写配置${NC}"
    echo -e "${YELLOW}  特别注意：需要填写 TUSHARE_TOKEN${NC}"
else
    echo -e "${GREEN}✓ .env 文件已存在${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}  安装完成！${NC}"
echo "=========================================="
echo ""
echo "下一步："
echo "  1. 编辑 .env 文件，填写 TUSHARE_TOKEN"
echo "  2. 启动后端: cd backend && source venv/Scripts/activate && uvicorn app.main:app --reload"
echo "  3. 启动前端: cd frontend && npm run dev"
echo "  4. 访问 http://localhost:3000 查看前端"
echo "  5. 访问 http://localhost:8000/docs 查看 API 文档"
echo ""
