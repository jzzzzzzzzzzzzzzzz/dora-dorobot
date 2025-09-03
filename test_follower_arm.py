#!/usr/bin/env python3
"""
测试从臂连接和关节数据
"""

import os
import sys
import time
import numpy as np
import pyarrow as pa
from dora import Node


def test_follower_arm():
    """测试从臂连接"""
    print("🤖 测试从臂连接...")
    
    # 检查设备权限
    device_path = "/dev/ttyACM4"
    if not os.path.exists(device_path):
        print(f"❌ 设备不存在: {device_path}")
        return False
    
    if not os.access(device_path, os.R_OK | os.W_OK):
        print(f"❌ 设备权限不足: {device_path}")
        print("请运行: sudo chmod 666 /dev/ttyACM4")
        return False
    
    print(f"✅ 设备检查通过: {device_path}")
    return True


def main():
    """主函数"""
    print("🧪 从臂连接测试")
    print("=" * 50)
    
    # 测试设备连接
    if not test_follower_arm():
        return
    
    print("\n🔄 启动Dora节点测试...")
    node = Node()
    
    joint_data_received = False
    start_time = time.time()
    max_wait_time = 10  # 10秒超时
    
    print("⏳ 等待关节数据...")
    
    for event in node:
        if time.time() - start_time > max_wait_time:
            print("⏰ 超时，未收到关节数据")
            break
            
        if event["type"] == "INPUT":
            if event["id"] == "joint":
                joint_data = event["value"].to_numpy()
                print(f"✅ 收到关节数据: {joint_data}")
                print(f"📊 数据形状: {joint_data.shape}")
                print(f"📊 数据类型: {joint_data.dtype}")
                joint_data_received = True
                break
                
        elif event["type"] == "STOP":
            break
    
    if joint_data_received:
        print("🎉 从臂连接测试成功！")
    else:
        print("❌ 从臂连接测试失败")


if __name__ == "__main__":
    main()
