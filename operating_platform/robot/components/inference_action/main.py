"""
DoRobot推理动作组件
使用真正的ACT模型进行自主抓取
"""

import os
import sys
import time
import subprocess
import numpy as np
import pyarrow as pa
from dora import Node
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from operating_platform.inference.policy import DoRobotPolicy


def main():
    """主函数"""
    node = Node()
    
    # 获取环境变量
    model_path = os.getenv("MODEL_PATH", "/data/dora/act_dorobot/pretrained_model")
    device = os.getenv("DEVICE", "auto")
    use_real_model = os.getenv("USE_REAL_MODEL", "true").lower() == "true"
    
    print(f"🤖 启动DoRobot推理组件")
    print(f"📁 模型路径: {model_path}")
    print(f"🔧 设备: {device}")
    print(f"🎯 使用真实模型: {use_real_model}")
    
    # 初始化策略
    try:
        policy = DoRobotPolicy(
            model_path=model_path,
            device=device,
            use_real_model=use_real_model
        )
        print("✅ 策略初始化成功")
    except Exception as e:
        print(f"❌ 策略初始化失败: {e}")
        print("🔄 使用简化模式")
        policy = None
    
    # Initialize data storage as global variables
    global latest_images, latest_joint
    latest_images = {}
    latest_joint = None
    inference_counter = 0
    
    # Send reset command to move to safe initial position
    print("🔄 Sending reset command to move to safe initial position...")
    reset_arrow = pa.array([1], type=pa.int32())  # Simple reset signal
    node.send_output("reset", reset_arrow)
    print("✅ Reset command sent")
    
    # Wait a moment for reset to complete
    time.sleep(1.0)
    
    for event in node:
        if event["type"] == "INPUT":
            if event["id"] == "tick":
                # 检查是否有足够的数据进行推理
                if latest_images and latest_joint is not None:
                    try:
                        # 执行推理
                        if policy is not None:
                            # 使用真正的ACT模型
                            action = policy.get_single_action(
                                images=latest_images,
                                joint_state=latest_joint
                            )
                            print(f"🎯 ACT模型推理结果: {action}")
                        else:
                            # 使用简化逻辑
                            action = generate_simple_action(latest_joint)
                            print(f"🎯 简化动作生成: {action}")
                        
                        # 发送动作到机器人
                        action_arrow = pa.array(action, type=pa.float32())
                        node.send_output("action", action_arrow)
                        
                        inference_counter += 1
                        if inference_counter % 10 == 0:
                            print(f"📊 已执行 {inference_counter} 次推理")
                            
                    except Exception as e:
                        print(f"❌ 推理失败: {e}")
                        # 发送零动作作为安全措施
                        zero_action = np.zeros(6, dtype=np.float32)
                        action_arrow = pa.array(zero_action, type=pa.float32())
                        node.send_output("action", action_arrow)
                else:
                    print("⚠️ 缺少数据进行推理")
                    
            elif event["id"] == "image_top":
                # 处理顶部摄像头图像
                image_data = event["value"].to_numpy()
                latest_images["image_top"] = image_data
                print(f"📷 收到顶部图像: {image_data.shape}")
                
            elif event["id"] == "image_wrist":
                # 处理手腕摄像头图像
                image_data = event["value"].to_numpy()
                latest_images["image_wrist"] = image_data
                print(f"📷 收到手腕图像: {image_data.shape}")
                
            elif event["id"] == "joint":
                # 处理关节状态
                joint_data = event["value"].to_numpy()
                latest_joint = joint_data
                print(f"🔧 收到关节状态: {joint_data}")
                
        elif event["type"] == "STOP":
            print("🛑 推理组件停止")
            break


def generate_simple_action(joint_state: np.ndarray) -> np.ndarray:
    """
    生成简化动作（用于测试）
    
    Args:
        joint_state: 当前关节状态
        
    Returns:
        动作数组
    """
    # 简单的抓取逻辑
    action = np.zeros(6, dtype=np.float32)
    
    # 基于当前状态生成相对动作
    # shoulder_pan: 左右摆动
    action[0] = np.random.uniform(-0.05, 0.05)
    
    # shoulder_lift: 上下移动
    if joint_state[1] > 30:  # 如果太高，下降
        action[1] = -0.02
    else:  # 否则上升
        action[1] = 0.02
    
    # elbow_flex: 弯曲肘部
    action[2] = np.random.uniform(-0.03, 0.03)
    
    # wrist_flex: 弯曲手腕
    action[3] = np.random.uniform(-0.02, 0.02)
    
    # wrist_roll: 旋转手腕
    action[4] = np.random.uniform(-0.01, 0.01)
    
    # gripper: 夹爪控制
    if np.random.random() > 0.7:  # 30%概率改变夹爪状态
        action[5] = np.random.uniform(-0.1, 0.1)
    
    return action


if __name__ == "__main__":
    main()
