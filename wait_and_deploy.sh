#!/bin/bash

# 等待网络恢复并自动部署脚本

BOARD_IP="192.168.1.100"
BOARD_USER="HwHiAiUser"
BOARD_PASSWORD="Mind@123"

echo "=========================================="
echo "    等待网络恢复并自动部署脚本"
echo "    目标: Orange Pi AI Pro 20T"
echo "=========================================="
echo ""

echo "正在等待开发板网络连接恢复..."
echo "按 Ctrl+C 取消等待"
echo ""

# 检查部署包是否存在
if [ ! -f "/tmp/dorobot_deploy.tar.gz" ]; then
    echo "错误: 部署包不存在，请先运行 ./deploy_to_board.sh"
    exit 1
fi

echo "部署包已准备就绪: $(ls -lh /tmp/dorobot_deploy.tar.gz | awk '{print $5}')"
echo ""

# 等待网络恢复
while true; do
    echo -n "检查网络连接... "
    
    # 检查ping
    if ping -c 1 -W 1 $BOARD_IP > /dev/null 2>&1; then
        echo "✓ 网络连通"
        
        # 检查SSH
        echo -n "检查SSH连接... "
        if sshpass -p "$BOARD_PASSWORD" ssh -o ConnectTimeout=3 -o BatchMode=yes $BOARD_USER@$BOARD_IP "echo 'test'" > /dev/null 2>&1; then
            echo "✓ SSH连接正常"
            echo ""
            echo "网络连接已恢复！开始自动部署..."
            echo ""
            
            # 运行手动部署脚本
            ./manual_deploy.sh
            exit $?
        else
            echo "✗ SSH连接失败"
        fi
    else
        echo "✗ 网络不通"
    fi
    
    # 等待5秒后重试
    sleep 5
done
