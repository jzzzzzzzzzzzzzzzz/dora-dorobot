#!/bin/bash

# 为开发板设置代理的脚本

BOARD_IP="192.168.3.137"
BOARD_USER="HwHiAiUser"
BOARD_PASSWORD="Mind@123"
LOCAL_PROXY_PORT="7897"

echo "=========================================="
echo "    开发板代理设置脚本"
echo "=========================================="
echo ""

echo "选择代理设置方式:"
echo "1. SSH动态端口转发 (SOCKS代理)"
echo "2. 使用本地HTTP代理"
echo "3. 配置开发板环境变量"
echo "4. SSH反向隧道 (推荐)"
echo "5. 测试代理连接"
echo ""

read -p "请选择 (1-5): " choice

case $choice in
    1)
        echo "设置SSH动态端口转发..."
        echo "建立SOCKS代理隧道..."
        
        # 检查是否已有相同的隧道
        if pgrep -f "ssh.*-D.*$LOCAL_PROXY_PORT.*$BOARD_IP" > /dev/null; then
            echo "SOCKS代理隧道已存在"
        else
            # 建立SOCKS代理
            sshpass -p "$BOARD_PASSWORD" ssh -D $LOCAL_PROXY_PORT -N -f $BOARD_USER@$BOARD_IP
            if [ $? -eq 0 ]; then
                echo "✓ SOCKS代理建立成功，监听端口: $LOCAL_PROXY_PORT"
            else
                echo "✗ SOCKS代理建立失败"
                exit 1
            fi
        fi
        
        echo ""
        echo "在开发板上设置代理环境变量..."
        sshpass -p "$BOARD_PASSWORD" ssh $BOARD_USER@$BOARD_IP << EOF
            echo "export http_proxy=socks5://127.0.0.1:$LOCAL_PROXY_PORT" >> ~/.bashrc
            echo "export https_proxy=socks5://127.0.0.1:$LOCAL_PROXY_PORT" >> ~/.bashrc
            echo "export HTTP_PROXY=socks5://127.0.0.1:$LOCAL_PROXY_PORT" >> ~/.bashrc
            echo "export HTTPS_PROXY=socks5://127.0.0.1:$LOCAL_PROXY_PORT" >> ~/.bashrc
            echo "代理环境变量已添加到 ~/.bashrc"
EOF
        ;;
        
    2)
        read -p "请输入本地HTTP代理端口 (默认8080): " http_port
        http_port=${http_port:-8080}
        
        echo "设置本地HTTP代理转发..."
        sshpass -p "$BOARD_PASSWORD" ssh -L $http_port:localhost:$http_port $BOARD_USER@$BOARD_IP << EOF
            export http_proxy=http://127.0.0.1:$http_port
            export https_proxy=http://127.0.0.1:$http_port
            echo "HTTP代理已设置: http://127.0.0.1:$http_port"
            echo "请在SSH会话中使用代理"
EOF
        ;;
        
    3)
        read -p "请输入代理地址 (例: http://192.168.1.102:8080): " proxy_url
        
        echo "在开发板上配置代理环境变量..."
        sshpass -p "$BOARD_PASSWORD" ssh $BOARD_USER@$BOARD_IP << EOF
            echo "export http_proxy=$proxy_url" >> ~/.bashrc
            echo "export https_proxy=$proxy_url" >> ~/.bashrc
            echo "export HTTP_PROXY=$proxy_url" >> ~/.bashrc
            echo "export HTTPS_PROXY=$proxy_url" >> ~/.bashrc
            echo "代理环境变量已添加到 ~/.bashrc"
            echo "重新登录SSH或运行 'source ~/.bashrc' 生效"
EOF
        ;;
        
    4)
        echo "设置SSH反向隧道代理..."
        echo "检查现有隧道..."
        
        # 检查是否已有反向隧道
        if pgrep -f "ssh.*-R.*$LOCAL_PROXY_PORT.*$BOARD_IP" > /dev/null; then
            echo "反向隧道已存在"
        else
            # 建立反向隧道
            echo "创建SSH反向隧道: $LOCAL_PROXY_PORT:127.0.0.1:$LOCAL_PROXY_PORT"
            sshpass -p "$BOARD_PASSWORD" ssh -R $LOCAL_PROXY_PORT:127.0.0.1:$LOCAL_PROXY_PORT $BOARD_USER@$BOARD_IP -N -f
            if [ $? -eq 0 ]; then
                echo "✓ SSH反向隧道建立成功"
            else
                echo "✗ SSH反向隧道建立失败"
                exit 1
            fi
        fi
        
        echo ""
        echo "在开发板上设置代理环境变量..."
        sshpass -p "$BOARD_PASSWORD" ssh $BOARD_USER@$BOARD_IP << EOF
            echo "export http_proxy=socks5://127.0.0.1:$LOCAL_PROXY_PORT" >> ~/.bashrc
            echo "export https_proxy=socks5://127.0.0.1:$LOCAL_PROXY_PORT" >> ~/.bashrc
            echo "export HTTP_PROXY=socks5://127.0.0.1:$LOCAL_PROXY_PORT" >> ~/.bashrc
            echo "export HTTPS_PROXY=socks5://127.0.0.1:$LOCAL_PROXY_PORT" >> ~/.bashrc
            echo "代理环境变量已添加到 ~/.bashrc"
            echo "测试代理连接..."
            export http_proxy=socks5://127.0.0.1:$LOCAL_PROXY_PORT
            export https_proxy=socks5://127.0.0.1:$LOCAL_PROXY_PORT
            curl -I --connect-timeout 10 http://www.google.com && echo "✓ 代理连接测试成功" || echo "✗ 代理连接测试失败"
EOF
        ;;
        
    5)
        echo "测试代理连接..."
        sshpass -p "$BOARD_PASSWORD" ssh $BOARD_USER@$BOARD_IP << 'EOF'
            echo "当前代理环境变量:"
            env | grep -i proxy
            echo ""
            echo "测试网络连接..."
            
            # 测试国内网站
            if curl -I --connect-timeout 5 http://www.baidu.com > /dev/null 2>&1; then
                echo "✓ 国内网站访问正常"
            else
                echo "✗ 国内网站访问失败"
            fi
            
            # 测试国外网站
            if curl -I --connect-timeout 5 http://www.google.com > /dev/null 2>&1; then
                echo "✓ 国外网站访问正常 (代理可能工作)"
            else
                echo "✗ 国外网站访问失败"
            fi
            
            # 测试pip源
            if curl -I --connect-timeout 5 https://pypi.org > /dev/null 2>&1; then
                echo "✓ PyPI访问正常"
            else
                echo "✗ PyPI访问失败"
            fi
EOF
        ;;
        
    *)
        echo "无效选择"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "代理设置完成"
echo "=========================================="

# 显示使用说明
case $choice in
    1)
        echo ""
        echo "SOCKS代理使用说明:"
        echo "1. SSH到开发板: ssh $BOARD_USER@$BOARD_IP"
        echo "2. 运行: source ~/.bashrc"
        echo "3. 测试: curl -I http://www.google.com"
        echo ""
        echo "停止代理: pkill -f 'ssh.*-D.*$LOCAL_PROXY_PORT'"
        ;;
    2)
        echo ""
        echo "HTTP代理在当前SSH会话中有效"
        echo "如需持久化，请选择选项3"
        ;;
    3)
        echo ""
        echo "代理已持久化到 ~/.bashrc"
        echo "重新登录SSH或运行 'source ~/.bashrc' 生效"
        ;;
    4)
        echo ""
        echo "SSH反向隧道代理使用说明:"
        echo "1. 隧道已建立并自动测试"
        echo "2. SSH到开发板: ssh $BOARD_USER@$BOARD_IP"
        echo "3. 运行: source ~/.bashrc"
        echo "4. 代理将自动生效"
        echo ""
        echo "停止隧道: pkill -f 'ssh.*-R.*$LOCAL_PROXY_PORT'"
        echo "查看隧道: ps aux | grep 'ssh.*-R.*$LOCAL_PROXY_PORT'"
        ;;
esac
