"""
简化的推理动作组件
不依赖operating_platform模块，直接在dr-robot-so101环境中运行
"""

import os
import sys
import time
import numpy as np
import pyarrow as pa
from dora import Node


def generate_autonomous_action(joint_state: np.ndarray) -> np.ndarray:
    """
    生成自主抓取动作
    
    Args:
        joint_state: 当前关节状态
        
    Returns:
        动作数组
    """
    # 基于当前状态生成相对动作
    action = np.zeros(6, dtype=np.float32)
    
    # shoulder_pan: 左右摆动寻找目标
    action[0] = np.random.uniform(-0.03, 0.03)
    
    # shoulder_lift: 上下移动
    if joint_state[1] > 35:  # 如果太高，下降
        action[1] = -0.02
    elif joint_state[1] < 20:  # 如果太低，上升
        action[1] = 0.02
    else:
        action[1] = np.random.uniform(-0.01, 0.01)
    
    # elbow_flex: 弯曲肘部
    if joint_state[2] > 25:  # 如果太直，弯曲
        action[2] = -0.02
    elif joint_state[2] < 15:  # 如果太弯，伸直
        action[2] = 0.02
    else:
        action[2] = np.random.uniform(-0.01, 0.01)
    
    # wrist_flex: 弯曲手腕
    action[3] = np.random.uniform(-0.01, 0.01)
    
    # wrist_roll: 旋转手腕
    action[4] = np.random.uniform(-0.005, 0.005)
    
    # gripper: 夹爪控制
    if np.random.random() > 0.8:  # 20%概率改变夹爪状态
        if joint_state[5] > 1.0:  # 如果夹爪打开，关闭
            action[5] = -0.05
        else:  # 如果夹爪关闭，打开
            action[5] = 0.05
    
    return action


def main():
    """主函数"""
    node = Node()
    
    print("🤖 启动简化推理组件")
    print("🎯 使用内置自主抓取逻辑")
    
    # Initialize data storage as global variables
    global latest_images, latest_joint
    latest_images = {}
    latest_joint = None
    inference_counter = 0
    
    # 设置自动断开时间（30秒）
    start_time = time.time()
    max_runtime = 30  # 30秒后自动停止
    
    # Send reset command to move to safe initial position
    print("🔄 Sending reset command to move to safe initial position...")
    reset_arrow = pa.array([1], type=pa.int32())  # Simple reset signal
    node.send_output("reset", reset_arrow)
    print("✅ Reset command sent")
    
    # Wait a moment for reset to complete
    time.sleep(1.0)
    
    for event in node:
        # 检查是否超时
        if time.time() - start_time > max_runtime:
            print(f"⏰ 运行时间达到 {max_runtime} 秒，自动停止")
            break
            
        if event["type"] == "INPUT":
            if event["id"] == "tick":
                # 检查是否有足够的数据进行推理
                if latest_joint is not None:
                    try:
                        # 执行自主抓取推理
                        action = generate_autonomous_action(latest_joint)
                        print(f"🎯 自主抓取动作: {action}")
                        
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
                    print("⚠️ 缺少关节数据进行推理")
                    # 发送零动作
                    zero_action = np.zeros(6, dtype=np.float32)
                    action_arrow = pa.array(zero_action, type=pa.float32())
                    node.send_output("action", action_arrow)
                    
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
    
    print(f"🏁 推理组件结束，总运行时间: {time.time() - start_time:.1f} 秒")


if __name__ == "__main__":
    main()
