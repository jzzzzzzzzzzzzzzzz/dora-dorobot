#!/bin/bash

# 手动部署脚本 - 当网络连接恢复后使用

set -e

# 配置信息
BOARD_IP="192.168.1.100"
BOARD_USER="HwHiAiUser"
BOARD_PASSWORD="Mind@123"
BOARD_PATH="/home/HwHiAiUser/dorobot"

echo "=========================================="
echo "    DoRobot 手动部署脚本"
echo "    目标: Orange Pi AI Pro 20T"
echo "=========================================="
echo ""

# 检查部署包是否存在
if [ ! -f "/tmp/dorobot_deploy.tar.gz" ]; then
    echo "错误: 部署包不存在，请先运行 ./deploy_to_board.sh"
    exit 1
fi

echo "部署包大小: $(ls -lh /tmp/dorobot_deploy.tar.gz | awk '{print $5}')"
echo ""

# 上传到开发板
echo "步骤 1: 上传部署包到开发板..."
echo "使用密码: $BOARD_PASSWORD"
sshpass -p "$BOARD_PASSWORD" scp /tmp/dorobot_deploy.tar.gz $BOARD_USER@$BOARD_IP:/tmp/

if [ $? -eq 0 ]; then
    echo "✓ 部署包上传成功"
else
    echo "✗ 部署包上传失败"
    exit 1
fi

echo ""

# 在开发板上安装
echo "步骤 2: 在开发板上安装DoRobot..."
echo "使用密码: $BOARD_PASSWORD"
sshpass -p "$BOARD_PASSWORD" ssh $BOARD_USER@$BOARD_IP << 'REMOTE_SCRIPT'
    set -e
    
    echo "=== 开始安装DoRobot ==="
    
    # 停止现有服务
    echo "停止现有服务..."
    pkill -f dorobot || true
    pkill -f operating_platform || true
    
    # 备份现有版本
    if [ -d /home/HwHiAiUser/dorobot ]; then
        BACKUP_NAME="dorobot_backup_$(date +%Y%m%d_%H%M%S)"
        mv /home/HwHiAiUser/dorobot /home/HwHiAiUser/$BACKUP_NAME
        echo "已备份现有版本到: $BACKUP_NAME"
    fi
    
    # 创建新目录
    mkdir -p /home/HwHiAiUser/dorobot
    cd /home/HwHiAiUser/dorobot
    
    # 解压新版本
    echo "解压新版本..."
    tar -xzf /tmp/dorobot_deploy.tar.gz
    
    # 检查Python环境
    echo "检查Python环境..."
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo "错误: 未找到Python环境"
        exit 1
    fi
    
    # 检查pip
    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        echo "错误: 未找到pip"
        exit 1
    fi
    
    # 安装依赖
    echo "安装Python依赖..."
    if [ -f pyproject.toml ]; then
        # 尝试普通安装方式
        pip3 install . || pip install . || echo "警告: 依赖安装失败，但项目文件已部署"
    else
        echo "警告: 未找到pyproject.toml文件"
    fi
    
    # 设置权限
    echo "设置文件权限..."
    chmod +x scripts/*.sh 2>/dev/null || true
    chmod +x operating_platform/robot/components/*/main.py 2>/dev/null || true
    
    # 验证安装
    echo "验证安装..."
    if $PYTHON_CMD -c "import operating_platform; print('DoRobot安装成功!')" 2>/dev/null; then
        echo "=== DoRobot安装完成 ==="
    else
        echo "警告: 安装验证失败，但文件已部署"
    fi
    
    # 清理临时文件
    rm -f /tmp/dorobot_deploy.tar.gz
    
    echo "安装完成！"
    echo "项目路径: /home/HwHiAiUser/dorobot"
    echo "运行命令: cd /home/HwHiAiUser/dorobot && python3 -m operating_platform.core.main --help"
REMOTE_SCRIPT

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "    DoRobot 部署完成！"
    echo "=========================================="
    echo ""
    echo "使用说明:"
    echo "1. SSH到开发板: ssh $BOARD_USER@$BOARD_IP"
    echo "2. 进入项目目录: cd /home/HwHiAiUser/dorobot"
    echo "3. 查看帮助: python3 -m operating_platform.core.main --help"
    echo "4. 开始录制: python3 -m operating_platform.core.main --record.repo_id=test_data"
    echo ""
    echo "项目路径: /home/HwHiAiUser/dorobot"
    echo "日志文件: /home/HwHiAiUser/dorobot/logs/"
else
    echo "安装过程中出现错误"
    exit 1
fi
