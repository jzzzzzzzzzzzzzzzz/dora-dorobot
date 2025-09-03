"""
DoRobot Policy implementation for ACT model inference.
"""

import torch
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional

from .utils.device import get_torch_device, is_half_precision_supported
from .utils.preprocessor import DoRobotPreprocessor
from .utils.postprocessor import DoRobotPostprocessor
from .model import ACTModelLoader, SimpleACTModel


class DoRobotPolicy:
    """DoRobot策略类，用于ACT模型推理"""
    
    def __init__(self, model_path: str, device: str = "auto", use_real_model: bool = True):
        """
        初始化策略
        
        Args:
            model_path: 模型路径
            device: 设备类型 ("auto", "cpu", "cuda", "npu")
            use_real_model: 是否使用真正的ACT模型
        """
        self.model_path = Path(model_path)
        self.device = get_torch_device(device)
        self.use_real_model = use_real_model
        
        # 检查半精度支持
        self.use_half_precision = is_half_precision_supported(device)
        
        # 初始化组件
        self._load_model()
        self._init_preprocessor()
        self._init_postprocessor()
        
        print(f"✅ DoRobot策略初始化完成，设备: {self.device}")
        if self.use_half_precision:
            print("✅ 启用半精度推理")
    
    def _load_model(self):
        """加载模型"""
        try:
            if self.use_real_model:
                # 使用真正的ACT模型
                loader = ACTModelLoader(str(self.model_path), str(self.device))
                self.model = loader.get_model()
                self.config = loader.config
                print("✅ 加载真正的ACT模型")
            else:
                # 使用简化模型进行测试
                self.model = SimpleACTModel()
                self.model = self.model.to(self.device)
                self.config = {"type": "simple_act"}
                print("✅ 加载简化ACT模型用于测试")
                
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            print("🔄 回退到简化模型")
            self.model = SimpleACTModel()
            self.model = self.model.to(self.device)
            self.config = {"type": "simple_act"}
            self.use_real_model = False
    
    def _init_preprocessor(self):
        """初始化预处理器"""
        self.preprocessor = DoRobotPreprocessor(
            device=self.device,
            use_half_precision=self.use_half_precision
        )
    
    def _init_postprocessor(self):
        """初始化后处理器"""
        self.postprocessor = DoRobotPostprocessor(
            model_path=self.model_path,
            device=self.device
        )
    
    def _should_use_half_precision(self) -> bool:
        """检查是否应该使用半精度"""
        return self.use_half_precision and self.device.type in ["cuda", "npu"]
    
    def predict(self, 
                images: Dict[str, np.ndarray],
                joint_state: np.ndarray,
                return_sequence: bool = False) -> np.ndarray:
        """
        执行推理预测
        
        Args:
            images: 图像字典 {"image_top": array, "image_wrist": array}
            joint_state: 关节状态数组 (6,)
            return_sequence: 是否返回动作序列
            
        Returns:
            动作数组 (6,) 或动作序列 (n_action_steps, 6)
        """
        with torch.no_grad():
            # 预处理输入
            processed_inputs = self.preprocessor.process(
                images=images,
                joint_state=joint_state
            )
            
            # 模型推理
            if self.use_real_model:
                # 真正的ACT模型推理
                actions = self.model(
                    images=processed_inputs["images"],
                    state=processed_inputs["state"]
                )  # (B, n_action_steps, 6)
                
                if return_sequence:
                    # 返回整个动作序列
                    actions = actions.squeeze(0)  # (n_action_steps, 6)
                else:
                    # 返回第一个动作
                    actions = actions[:, 0, :]  # (B, 6)
                    actions = actions.squeeze(0)  # (6,)
            else:
                # 简化模型推理
                if self.use_real_model:
                    # 模拟真实模型的输入格式
                    combined_input = torch.cat([
                        processed_inputs["state"],
                        processed_inputs["images"]["image_top"].flatten(1),
                        processed_inputs["images"]["image_wrist"].flatten(1)
                    ], dim=1)
                else:
                    # 简化输入
                    combined_input = processed_inputs["state"]
                
                actions = self.model(combined_input)  # (B, 6)
                actions = actions.squeeze(0)  # (6,)
            
            # 后处理输出
            processed_actions = self.postprocessor.process(actions)
            
            return processed_actions
    
    def get_action_sequence(self, 
                           images: Dict[str, np.ndarray],
                           joint_state: np.ndarray) -> np.ndarray:
        """
        获取动作序列
        
        Args:
            images: 图像字典
            joint_state: 关节状态
            
        Returns:
            动作序列 (n_action_steps, 6)
        """
        return self.predict(images, joint_state, return_sequence=True)
    
    def get_single_action(self, 
                         images: Dict[str, np.ndarray],
                         joint_state: np.ndarray) -> np.ndarray:
        """
        获取单个动作
        
        Args:
            images: 图像字典
            joint_state: 关节状态
            
        Returns:
            单个动作 (6,)
        """
        return self.predict(images, joint_state, return_sequence=False)
