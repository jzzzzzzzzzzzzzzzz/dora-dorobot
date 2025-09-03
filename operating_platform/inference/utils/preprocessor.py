"""
DoRobot Preprocessor for ACT model inference.
"""

import torch
import numpy as np
import torchvision.transforms as transforms
from typing import Dict, Any, Optional


class DoRobotPreprocessor:
    """DoRobot预处理器，用于ACT模型输入预处理"""
    
    def __init__(self, device: torch.device = None, use_half_precision: bool = False):
        """
        初始化预处理器
        
        Args:
            device: PyTorch设备
            use_half_precision: 是否使用半精度
        """
        self.device = device if device is not None else torch.device("cpu")
        self.use_half_precision = use_half_precision
        
        # 图像预处理变换
        self.image_transforms = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],  # ImageNet标准化
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        # 状态标准化参数（从训练数据中估计）
        self.state_mean = np.array([0.0, 25.0, 20.0, 1.0, 0.0, 1.5])
        self.state_std = np.array([1.0, 5.0, 5.0, 1.0, 1.0, 0.5])
        
        print(f"✅ 预处理器初始化完成，设备: {self.device}")
    
    def process(self, 
                images: Dict[str, np.ndarray],
                joint_state: np.ndarray) -> Dict[str, Any]:
        """
        预处理输入数据
        
        Args:
            images: 图像字典 {"image_top": array, "image_wrist": array}
            joint_state: 关节状态数组 (6,)
            
        Returns:
            处理后的输入字典
        """
        processed_images = {}
        
        # 处理图像
        for image_name, image in images.items():
            if image is not None:
                processed_image = self._process_image(image)
                processed_images[image_name] = processed_image
            else:
                # 如果图像为空，创建零张量
                processed_images[image_name] = torch.zeros(
                    1, 3, 240, 320, 
                    device=self.device,
                    dtype=torch.float16 if self.use_half_precision else torch.float32
                )
        
        # 处理关节状态
        processed_state = self._process_state(joint_state)
        
        return {
            "images": processed_images,
            "state": processed_state
        }
    
    def _process_image(self, image: np.ndarray) -> torch.Tensor:
        """
        处理图像
        
        Args:
            image: 输入图像 (H, W, C) 或 (C, H, W)
            
        Returns:
            处理后的图像张量 (1, C, H, W)
        """
        # 确保图像格式正确
        if image.dtype != np.uint8:
            image = (image * 255).astype(np.uint8)
        
        # 确保图像尺寸正确 (240, 320, 3)
        if image.shape != (240, 320, 3):
            # 调整图像尺寸
            from PIL import Image
            pil_image = Image.fromarray(image)
            pil_image = pil_image.resize((320, 240))
            image = np.array(pil_image)
        
        # 应用变换
        tensor_image = self.image_transforms(image)  # (C, H, W)
        
        # 添加batch维度
        tensor_image = tensor_image.unsqueeze(0)  # (1, C, H, W)
        
        # 移动到设备
        tensor_image = tensor_image.to(self.device)
        
        # 应用半精度
        if self.use_half_precision:
            tensor_image = tensor_image.half()
        
        return tensor_image
    
    def _process_state(self, state: np.ndarray) -> torch.Tensor:
        """
        处理关节状态
        
        Args:
            state: 关节状态数组 (6,)
            
        Returns:
            处理后的状态张量 (1, 6)
        """
        # 确保状态是numpy数组
        if not isinstance(state, np.ndarray):
            state = np.array(state)
        
        # 标准化状态
        normalized_state = (state - self.state_mean) / self.state_std
        
        # 转换为张量
        tensor_state = torch.from_numpy(normalized_state).float()
        
        # 添加batch维度
        tensor_state = tensor_state.unsqueeze(0)  # (1, 6)
        
        # 移动到设备
        tensor_state = tensor_state.to(self.device)
        
        # 应用半精度
        if self.use_half_precision:
            tensor_state = tensor_state.half()
        
        return tensor_state
