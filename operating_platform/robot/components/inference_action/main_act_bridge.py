#!/usr/bin/env python3
"""
ACT模型推理桥接组件 - 在dorobot环境中运行真正的ACT模型
"""

import os
import sys
import time
import json
import numpy as np
import pyarrow as pa
from dora import Node
from pathlib import Path

# 添加operating_platform路径
sys.path.insert(0, '/data/dora/DoRobot-Preview')

try:
    from operating_platform.inference.policy import DoRobotPolicy
    print("✅ 成功导入DoRobotPolicy")
except ImportError as e:
    print(f"❌ 导入DoRobotPolicy失败: {e}")
    print("请确保在dorobot环境中运行此组件")
    sys.exit(1)


def load_act_model():
    """加载ACT模型"""
    model_path = os.getenv("MODEL_PATH", "/data/dora/act_dorobot/pretrained_model")
    device = os.getenv("DEVICE", "auto")
    use_real_model = os.getenv("USE_REAL_MODEL", "true").lower() == "true"
    
    print(f"🤖 加载ACT模型:")
    print(f"   模型路径: {model_path}")
    print(f"   设备: {device}")
    print(f"   使用真实模型: {use_real_model}")
    
    try:
        policy = DoRobotPolicy(
            model_path=model_path,
            device=device,
            use_real_model=use_real_model
        )
        print("✅ ACT模型加载成功")
        return policy
    except Exception as e:
        print(f"❌ ACT模型加载失败: {e}")
        return None


def preprocess_observation(image_top, image_wrist, joint_state):
    """预处理观察数据"""
    try:
        # 转换图像数据
        if image_top is not None:
            image_top = image_top.to_numpy()
        if image_wrist is not None:
            image_wrist = image_wrist.to_numpy()
        
        # 转换关节数据
        if joint_state is not None:
            joint_state = joint_state.to_numpy()
        
        return image_top, image_wrist, joint_state
    except Exception as e:
        print(f"⚠️ 数据预处理警告: {e}")
        return None, None, None


def main():
    """主函数"""
    print("🧠 ACT模型推理桥接组件启动")
    print("=" * 50)
    
    # 加载ACT模型
    policy = load_act_model()
    if policy is None:
        print("❌ 无法加载ACT模型，退出")
        return
    
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
                        # 预处理数据
                        image_top, image_wrist, joint_state = preprocess_observation(
                            last_image_top, last_image_wrist, last_joint_state
                        )
                        
                        if image_top is not None and image_wrist is not None and joint_state is not None:
                            # 执行推理
                            print("🧠 执行ACT模型推理...")
                            action = policy.get_single_action(
                                images=[image_top, image_wrist],
                                joint_state=joint_state
                            )
                            
                            if action is not None:
                                print(f"🎯 推理结果: {action}")
                                # 发送动作到机械臂
                                node.send_output("action", pa.array(action, type=pa.float32()))
                            else:
                                print("⚠️ 推理结果为空")
                        else:
                            print("⚠️ 数据预处理失败")
                            
                    except Exception as e:
                        print(f"❌ 推理过程出错: {e}")
                else:
                    print("⚠️ 缺少关节数据进行推理")
                    
        elif event["type"] == "STOP":
            print("🛑 收到停止信号")
            break
    
    print("🏁 ACT模型推理桥接组件结束")


if __name__ == "__main__":
    main()
