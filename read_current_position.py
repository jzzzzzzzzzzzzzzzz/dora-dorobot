#!/usr/bin/env python3
"""
读取当前从臂位置作为新的安全位置
"""

import os
import sys
import time
import numpy as np
import pyarrow as pa
from dora import Node


def read_current_position():
    """读取当前从臂位置"""
    print("📊 读取当前从臂位置...")
    
    node = Node()
    position_received = False
    current_position = None
    start_time = time.time()
    max_wait_time = 10
    
    print("⏳ 等待关节数据...")
    
    for event in node:
        if time.time() - start_time > max_wait_time:
            print("⏰ 超时，未收到关节数据")
            break
            
        if event["type"] == "INPUT":
            if event["id"] == "joint":
                current_position = event["value"].to_numpy()
                print(f"✅ 当前位置: {current_position}")
                print(f"📊 关节角度:")
                joint_names = ['shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex', 'wrist_roll', 'gripper']
                for i, (name, angle) in enumerate(zip(joint_names, current_position)):
                    print(f"   {name}: {angle:.2f}°")
                position_received = True
                break
                
        elif event["type"] == "STOP":
            break
    
    return current_position if position_received else None


def main():
    """主函数"""
    print("🔍 读取当前从臂安全位置")
    print("=" * 50)
    
    # 读取当前位置
    current_pos = read_current_position()
    
    if current_pos is not None:
        print("\n💾 新的安全位置配置:")
        print("```python")
        print("SAFE_POSITION = {")
        joint_names = ['shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex', 'wrist_roll', 'gripper']
        for i, (name, angle) in enumerate(zip(joint_names, current_pos)):
            print(f"    '{name}': {angle:.2f},")
        print("}")
        print("```")
        
        print("\n📝 请将此配置更新到相关文件中")
    else:
        print("❌ 无法读取当前位置")


if __name__ == "__main__":
    main()
