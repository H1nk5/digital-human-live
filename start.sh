#!/bin/bash
echo "========================================"
echo "  数字人直播系统 - 启动"
echo "========================================"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python3"
    exit 1
fi

# 虚拟环境
if [ ! -d ".venv" ]; then
    echo "[1/3] 创建虚拟环境..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "[2/3] 安装依赖..."
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

echo "[3/3] 启动系统..."
python3 main.py -i "$@"
