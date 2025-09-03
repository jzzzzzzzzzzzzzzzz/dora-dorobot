"""
DoRobot Postprocessor for ACT model inference.
"""

import torch
import numpy as np
from pathlib import Path
from typing import Union


class DoRobotPostprocessor:
    """DoRobot后处理器，用于ACT模型输出后处理"""
    
    def __init__(self, model_path: Path, device: torch.device):
        """
        初始化后处理器
        
        Args:
            model_path: 模型路径
            device: PyTorch设备
        """
        self.model_path = model_path
        self.device = device
        
        # 动作反标准化参数（基于LeRobot标准优化）
        self.action_mean = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self.action_std = np.array([0.05, 0.05, 0.05, 0.02, 0.02, 0.05])  # 更精细的控制
        
        print(f"✅ 后处理器初始化完成，设备: {self.device}")
    
    def process(self, actions: torch.Tensor) -> np.ndarray:
        """
        后处理动作输出
        
        Args:
            actions: 模型输出的动作张量
            
        Returns:
            处理后的动作数组
        """
        # 确保是CPU张量
        if actions.device != torch.device("cpu"):
            actions = actions.cpu()
        
        # 转换为numpy数组
        if isinstance(actions, torch.Tensor):
            actions = actions.detach().numpy()
        
        # 确保是2D数组
        if actions.ndim == 1:
            actions = actions.reshape(1, -1)
        
        # 反标准化动作
        denormalized_actions = actions * self.action_std + self.action_mean
        
        # 如果是单个动作，返回1D数组
        if denormalized_actions.shape[0] == 1:
            return denormalized_actions[0]
        
        return denormalized_actions
