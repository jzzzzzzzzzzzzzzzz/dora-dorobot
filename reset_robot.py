#!/usr/bin/env python3
"""
机器人复位脚本
将机器人移动到安全的初始位置（收缩状态）
"""

import os
import sys
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from operating_platform.robot.robots.so101_v1.manipulator import SO101Manipulator

def reset_robot():
    """将机器人复位到安全位置"""
    print("🤖 开始机器人复位...")
    
    try:
        # 创建机器人实例
        robot = SO101Manipulator()
        print("✅ 机器人连接成功")
        
        # 定义安全初始位置（收缩状态）
        safe_position = {
            "shoulder_pan": 0.0,      # 中心位置
            "shoulder_lift": 30.0,    # 抬高位置（安全高度）
            "elbow_flex": 20.0,       # 适度弯曲
            "wrist_flex": 1.0,        # 轻微弯曲
            "wrist_roll": 0.0,        # 无旋转
            "gripper": 1.5,           # 部分闭合
        }
        
        print("🔄 移动到安全初始位置...")
        print(f"目标位置: {safe_position}")
        
        # 移动到安全位置
        robot.move_to_position(safe_position)
        
        # 等待移动完成
        time.sleep(5.0)
        
        # 检查当前位置
        current_pos = robot.get_current_position()
        print(f"✅ 复位完成，当前位置: {current_pos}")
        
        return True
        
    except Exception as e:
        print(f"❌ 复位失败: {e}")
        return False

if __name__ == "__main__":
    success = reset_robot()
    if success:
        print("🎉 机器人复位成功！")
    else:
        print("💥 机器人复位失败！")
        sys.exit(1)


