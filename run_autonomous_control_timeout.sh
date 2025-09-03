#!/bin/bash

echo "🚀 启动 DoRobot 自主控制系统（带超时控制）"
echo "================================"

# 检查环境
if ! conda env list | grep -q "dr-robot-so101"; then
    echo "❌ 错误: 找不到 dr-robot-so101 环境"
    echo "请先安装并激活正确的环境"
    exit 1
fi

# 检查设备
echo "📋 检查设备状态..."
if [ ! -e "/dev/ttyACM4" ]; then
    echo "❌ 错误: 找不到从臂设备 /dev/ttyACM4"
    echo "📋 可用设备:"
    ls -la /dev/ttyACM* 2>/dev/null || echo "   无可用设备"
    exit 1
fi

if [ ! -e "/dev/video1" ] || [ ! -e "/dev/video2" ]; then
    echo "❌ 错误: 找不到摄像头设备"
    exit 1
fi

echo "✅ 设备检查通过"

# 询问运行时间
echo ""
echo "⏰ 设置运行时间（秒）:"
echo "1) 30秒 - 快速测试"
echo "2) 60秒 - 中等测试"
echo "3) 120秒 - 完整测试"
echo "4) 自定义时间"
read -p "请选择 (1/2/3/4): " choice

case $choice in
    1)
        runtime=30
        ;;
    2)
        runtime=60
        ;;
    3)
        runtime=120
        ;;
    4)
        read -p "请输入运行时间（秒）: " runtime
        ;;
    *)
        runtime=30
        echo "使用默认30秒"
        ;;
esac

echo "⏰ 设置运行时间: ${runtime}秒"

# 询问是否先复位机器人
echo ""
echo "🤖 是否在启动前复位机器人到安全位置？"
echo "1) 是 - 先复位到安全位置"
echo "2) 否 - 直接启动自主控制"
read -p "请选择 (1/2): " reset_choice

if [ "$reset_choice" = "1" ]; then
    echo "🔄 正在复位机器人到安全位置..."
    conda activate dorobot && python reset_robot.py
    if [ $? -eq 0 ]; then
        echo "✅ 机器人复位成功"
    else
        echo "⚠️ 机器人复位失败，但继续启动自主控制"
    fi
    echo ""
fi

# 启动自主数据流
echo "🤖 启动自主数据流..."
echo "⏰ 将在 ${runtime} 秒后自动停止"
echo "按 Ctrl+C 可提前停止"
echo ""

# 使用timeout命令确保超时停止
timeout ${runtime}s dora run operating_platform/robot/robots/so101_v1/dora_working_autonomous_dataflow.yml

echo ""
echo "🏁 自主控制系统运行完成"
echo "📊 运行时间: ${runtime}秒"
