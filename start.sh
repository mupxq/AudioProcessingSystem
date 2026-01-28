#!/bin/bash

# Fun-ASR 语音识别批量处理系统 - 启动脚本

echo "=================================="
echo "Fun-ASR 语音识别批量处理系统"
echo "=================================="
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3，请先安装 Python 3.8+"
    exit 1
fi

# 检查依赖是否安装
echo "检查依赖..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "依赖未安装，正在安装..."
    pip3 install -r requirements.txt
fi

# 创建必要的目录
mkdir -p models outputs

echo ""
echo "启动服务器..."
echo ""

# 启动应用
python3 backend/app.py
