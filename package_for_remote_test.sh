#!/bin/bash

echo "🚀 开始打包DoRobot项目用于远程测试"
echo "================================"

# 设置变量
PROJECT_NAME="DoRobot-Preview"
REMOTE_HOST="HwHiAiUser@192.168.3.137"
REMOTE_PATH="/home/HwHiAiUser/DoRobot-Preview"
PACKAGE_NAME="dorobot_remote_test_$(date +%Y%m%d_%H%M%S).tar.gz"

# 检查当前目录
if [ ! -f "operating_platform/robot/robots/so101_v1/dora_working_autonomous_dataflow.yml" ]; then
    echo "❌ 错误: 请在DoRobot-Preview项目根目录下运行此脚本"
    exit 1
fi

echo "📦 创建项目打包文件..."

# 创建临时目录
TEMP_DIR=$(mktemp -d)
echo "📁 临时目录: $TEMP_DIR"

# 复制项目文件到临时目录
echo "📋 复制项目文件..."
cp -r . "$TEMP_DIR/$PROJECT_NAME"

# 进入临时目录
cd "$TEMP_DIR"

# 清理不必要的文件
echo "🧹 清理不必要的文件..."
cd "$PROJECT_NAME"

# 删除一些不需要的文件和目录
rm -rf .git
rm -rf __pycache__
rm -rf */__pycache__
rm -rf */*/__pycache__
rm -rf */*/*/__pycache__
rm -rf .pytest_cache
rm -rf .vscode
rm -rf .idea
rm -rf *.log
rm -rf logs/
rm -rf temp/
rm -rf tmp/

# 删除一些测试文件（保留核心功能）
rm -f test_*.py
rm -f *_test.py
rm -f dora_test_*.yml
rm -f read_current_position.py

echo "📦 创建压缩包..."
cd ..
tar -czf "$PACKAGE_NAME" "$PROJECT_NAME"

# 显示打包信息
PACKAGE_SIZE=$(du -h "$PACKAGE_NAME" | cut -f1)
echo "✅ 打包完成: $PACKAGE_NAME (大小: $PACKAGE_SIZE)"

# 发送到远程服务器
echo "📤 发送到远程开发板..."
echo "目标: $REMOTE_HOST:$REMOTE_PATH"

# 创建远程目录
ssh "$REMOTE_HOST" "mkdir -p $REMOTE_PATH"

# 发送文件
scp "$PACKAGE_NAME" "$REMOTE_HOST:$REMOTE_PATH/"

if [ $? -eq 0 ]; then
    echo "✅ 文件发送成功！"
    
    # 在远程服务器上解压
    echo "📂 在远程服务器上解压..."
    ssh "$REMOTE_HOST" "cd $REMOTE_PATH && tar -xzf $PACKAGE_NAME && rm $PACKAGE_NAME"
    
    echo "🎉 远程部署完成！"
    echo ""
    echo "📋 远程测试指南："
    echo "1. 登录远程服务器: ssh $REMOTE_HOST"
    echo "2. 进入项目目录: cd $REMOTE_PATH/$PROJECT_NAME"
    echo "3. 检查设备: ls -la /dev/ttyACM*"
    echo "4. 运行测试: conda activate dr-robot-so101 && timeout 30 dora run operating_platform/robot/robots/so101_v1/dora_working_autonomous_dataflow.yml"
    echo ""
    echo "📁 远程项目路径: $REMOTE_PATH/$PROJECT_NAME"
    
else
    echo "❌ 文件发送失败！"
    echo "请检查网络连接和远程服务器状态"
fi

# 清理临时目录
echo "🧹 清理临时文件..."
rm -rf "$TEMP_DIR"

echo "🏁 打包和部署流程完成！"
