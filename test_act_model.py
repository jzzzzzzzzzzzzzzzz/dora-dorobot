#!/usr/bin/env python3
"""
测试真正的ACT模型推理
"""

import os
import sys
import numpy as np
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from operating_platform.inference.policy import DoRobotPolicy


def test_act_model():
    """测试ACT模型推理"""
    print("🧪 开始测试ACT模型推理")
    
    # 模型路径
    model_path = "/data/dora/act_dorobot/pretrained_model"
    
    # 测试数据
    test_images = {
        "image_top": np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8),
        "image_wrist": np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
    }
    
    test_joint_state = np.array([0.0, 25.0, 20.0, 1.0, 0.0, 1.5], dtype=np.float32)
    
    print(f"📁 模型路径: {model_path}")
    print(f"📷 测试图像形状: {test_images['image_top'].shape}")
    print(f"🔧 测试关节状态: {test_joint_state}")
    
    try:
        # 初始化策略（使用真实模型）
        print("🔄 初始化策略...")
        policy = DoRobotPolicy(
            model_path=model_path,
            device="auto",
            use_real_model=True
        )
        print("✅ 策略初始化成功")
        
        # 执行推理
        print("🔄 执行推理...")
        action = policy.get_single_action(
            images=test_images,
            joint_state=test_joint_state
        )
        
        print(f"🎯 推理结果: {action}")
        print(f"📊 动作形状: {action.shape}")
        print(f"📊 动作范围: [{action.min():.4f}, {action.max():.4f}]")
        
        # 测试动作序列
        print("🔄 测试动作序列...")
        action_sequence = policy.get_action_sequence(
            images=test_images,
            joint_state=test_joint_state
        )
        
        print(f"🎯 动作序列形状: {action_sequence.shape}")
        print(f"📊 序列长度: {action_sequence.shape[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simple_model():
    """测试简化模型"""
    print("\n🧪 开始测试简化模型")
    
    try:
        # 初始化策略（使用简化模型）
        policy = DoRobotPolicy(
            model_path="/data/dora/act_dorobot/pretrained_model",
            device="auto",
            use_real_model=False
        )
        print("✅ 简化模型初始化成功")
        
        # 测试数据
        test_images = {
            "image_top": np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8),
            "image_wrist": np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
        }
        test_joint_state = np.array([0.0, 25.0, 20.0, 1.0, 0.0, 1.5], dtype=np.float32)
        
        # 执行推理
        action = policy.get_single_action(
            images=test_images,
            joint_state=test_joint_state
        )
        
        print(f"🎯 简化模型推理结果: {action}")
        return True
        
    except Exception as e:
        print(f"❌ 简化模型测试失败: {e}")
        return False


if __name__ == "__main__":
    print("🚀 ACT模型测试开始")
    print("=" * 50)
    
    # 测试真实模型
    real_model_success = test_act_model()
    
    # 测试简化模型
    simple_model_success = test_simple_model()
    
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print(f"  真实ACT模型: {'✅ 成功' if real_model_success else '❌ 失败'}")
    print(f"  简化模型: {'✅ 成功' if simple_model_success else '❌ 失败'}")
    
    if real_model_success and simple_model_success:
        print("🎉 所有测试通过！")
    else:
        print("⚠️ 部分测试失败，请检查错误信息")

