#!/bin/bash

# 网络连接检查脚本

BOARD_IP="192.168.1.100"
BOARD_USER="HwHiAiUser"
BOARD_PASSWORD="Mind@123"

echo "=========================================="
echo "    网络连接检查脚本"
echo "    目标: Orange Pi AI Pro 20T"
echo "=========================================="
echo ""

echo "检查项目:"
echo "1. 网络连通性"
echo "2. SSH连接"
echo "3. 开发板状态"
echo ""

# 检查网络连通性
echo "1. 检查网络连通性..."
if ping -c 3 $BOARD_IP > /dev/null 2>&1; then
    echo "✓ 网络连通正常"
else
    echo "✗ 网络连通失败"
    echo "  可能原因:"
    echo "  - 开发板未开机"
    echo "  - 网络配置问题"
    echo "  - 防火墙阻止ping"
fi

# 检查ARP表
echo ""
echo "2. 检查ARP表..."
ARP_RESULT=$(arp -a | grep $BOARD_IP)
if [ -n "$ARP_RESULT" ]; then
    echo "✓ 开发板在ARP表中: $ARP_RESULT"
else
    echo "✗ 开发板不在ARP表中"
fi

# 检查SSH连接
echo ""
echo "3. 检查SSH连接..."
if sshpass -p "$BOARD_PASSWORD" ssh -o ConnectTimeout=5 -o BatchMode=yes $BOARD_USER@$BOARD_IP "echo 'SSH连接成功'" > /dev/null 2>&1; then
    echo "✓ SSH连接正常"
else
    echo "✗ SSH连接失败"
    echo "  可能原因:"
    echo "  - SSH服务未运行"
    echo "  - 用户名或密码错误"
    echo "  - 网络连接问题"
fi

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="
