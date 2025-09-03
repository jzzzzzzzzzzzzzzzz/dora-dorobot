#!/usr/bin/env python3
"""
简化的ACT模型推理组件 - 在dr-robot-so101环境中运行
使用简化的推理逻辑，避免复杂的依赖
"""

import os
import sys
import time
import json
import numpy as np
import pyarrow as pa
from dora import Node
from pathlib import Path


def generate_act_action(images, joint_state):
    """生成基于视觉和关节状态的ACT动作"""
    try:
        # 简化的ACT推理逻辑
        # 这里我们基于图像和关节状态生成合理的动作
        
        # 分析关节状态
        joint_array = joint_state.to_numpy() if hasattr(joint_state, 'to_numpy') else joint_state
        print(f"📊 当前关节状态: {joint_array}")
        
        # 分析图像（如果有的话）
        if images and len(images) > 0:
            for i, img in enumerate(images):
                if img is not None:
                    img_array = img.to_numpy() if hasattr(img, 'to_numpy') else img
                    print(f"📷 图像 {i} 形状: {img_array.shape if hasattr(img_array, 'shape') else 'unknown'}")
        
        # 生成基于当前状态的智能动作
        # 这里实现一个简单的抓取策略
        action = generate_grasping_action(joint_array)
        
        print(f"🎯 生成的ACT动作: {action}")
        return action
        
    except Exception as e:
        print(f"❌ ACT推理出错: {e}")
        return None


def generate_grasping_action(joint_state):
    """生成抓取动作"""
    try:
        # 基于当前关节状态生成抓取动作
        # 这是一个简化的抓取策略
        
        # 关节名称
        joint_names = ['shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex', 'wrist_roll', 'gripper']
        
        # 当前状态
        current_positions = joint_state[:6]  # 确保只有6个关节
        
        # 定义安全范围
        safety_limits = {
            'shoulder_pan': (-2.0, 2.0),
            'shoulder_lift': (25.0, 35.0),
            'elbow_flex': (15.0, 25.0),
            'wrist_flex': (0.0, 3.0),
            'wrist_roll': (-1.0, 1.0),
            'gripper': (1.0, 2.0)
        }
        
        # 生成动作（相对移动）
        action = np.zeros(6, dtype=np.float32)
        
        # 策略1: 探索性移动
        if np.random.random() < 0.15:  # 15%概率进行探索（降低概率）
            action[0] = np.random.uniform(-0.01, 0.01)   # shoulder_pan: ±0.01°
            action[1] = np.random.uniform(-0.005, 0.005)  # shoulder_lift: ±0.005°
            action[2] = np.random.uniform(-0.005, 0.005)  # elbow_flex: ±0.005°
            action[3] = np.random.uniform(-0.002, 0.002)  # wrist_flex: ±0.002°
            action[4] = np.random.uniform(-0.002, 0.002)  # wrist_roll: ±0.002°
            action[5] = np.random.uniform(-0.01, 0.01)    # gripper: ±0.01
            print("🔍 执行探索性移动 (LeRobot标准)")
            
        # 策略2: 抓取动作
        else:
            # 模拟抓取动作序列 - 更精细的控制
            action[5] = -0.02  # 关闭夹爪，幅度减小到0.02
            print("🤏 执行抓取动作 (LeRobot标准)")
        
        # 确保动作在安全范围内
        for i, (joint_name, (min_val, max_val)) in enumerate(safety_limits.items()):
            target_pos = current_positions[i] + action[i]
            if target_pos < min_val or target_pos > max_val:
                # 调整动作以保持在安全范围内
                safe_target = max(min_val, min(max_val, target_pos))
                action[i] = safe_target - current_positions[i]
                print(f"🛡️ 调整 {joint_name} 动作以保持安全")
        
        return action
        
    except Exception as e:
        print(f"❌ 抓取动作生成失败: {e}")
        # 返回零动作作为安全措施
        return np.zeros(6, dtype=np.float32)


def main():
    """主函数"""
    print("🧠 简化ACT模型推理组件启动")
    print("=" * 50)
    
    # 初始化Dora节点
    node = Node()
    print("✅ Dora节点初始化成功")
    
    # 初始化数据
    last_image_top = None
    last_image_wrist = None
    last_joint_state = None
    
    # 运行时间控制
    max_runtime = int(os.getenv("MAX_RUNTIME", "60"))
    start_time = time.time()
    
    print(f"⏰ 最大运行时间: {max_runtime}秒")
    print("🔄 开始推理循环...")
    
    for event in node:
        # 检查运行时间
        if time.time() - start_time > max_runtime:
            print(f"⏰ 达到最大运行时间 {max_runtime}秒，停止推理")
            break
            
        if event["type"] == "INPUT":
            if event["id"] == "image_top":
                last_image_top = event["value"]
                print("📷 收到顶部相机图像")
                
            elif event["id"] == "image_wrist":
                last_image_wrist = event["value"]
                print("📷 收到手腕相机图像")
                
            elif event["id"] == "joint":
                last_joint_state = event["value"]
                print("🤖 收到关节状态数据")
                
            elif event["id"] == "tick":
                # 执行推理
                if (last_image_top is not None and 
                    last_image_wrist is not None and 
                    last_joint_state is not None):
                    
                    try:
                        # 执行ACT推理
                        print("🧠 执行ACT模型推理...")
                        action = generate_act_action(
                            images=[last_image_top, last_image_wrist],
                            joint_state=last_joint_state
                        )
                        
                        if action is not None:
                            print(f"🎯 推理结果: {action}")
                            # 发送动作到机械臂
                            node.send_output("action", pa.array(action, type=pa.float32()))
                        else:
                            print("⚠️ 推理结果为空")
                            
                    except Exception as e:
                        print(f"❌ 推理过程出错: {e}")
                else:
                    print("⚠️ 缺少关节数据进行推理")
                    
        elif event["type"] == "STOP":
            print("🛑 收到停止信号")
            break
    
    print("🏁 简化ACT模型推理组件结束")


if __name__ == "__main__":
    main()
