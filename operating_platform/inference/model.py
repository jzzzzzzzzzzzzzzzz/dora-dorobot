"""
ACT (Action Chunking Transformer) 模型实现
用于机器人自主抓取任务
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision.models import resnet18, ResNet18_Weights
from typing import Dict, Any, Optional
import json
from pathlib import Path


class ACTModel(nn.Module):
    """真正的ACT模型实现"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        
        # 模型参数
        self.dim_model = config.get("dim_model", 512)
        self.n_heads = config.get("n_heads", 8)
        self.dim_feedforward = config.get("dim_feedforward", 3200)
        self.n_encoder_layers = config.get("n_encoder_layers", 4)
        self.n_decoder_layers = config.get("n_decoder_layers", 1)
        self.dropout = config.get("dropout", 0.1)
        self.chunk_size = config.get("chunk_size", 100)
        self.n_action_steps = config.get("n_action_steps", 100)
        self.latent_dim = config.get("latent_dim", 32)
        self.use_vae = config.get("use_vae", True)
        
        # 视觉编码器
        self.vision_backbone = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
        # 移除最后的分类层
        self.vision_backbone = nn.Sequential(*list(self.vision_backbone.children())[:-1])
        
        # 视觉特征投影
        self.vision_projection = nn.Linear(512, self.dim_model)
        
        # 状态编码器
        self.state_encoder = nn.Linear(6, self.dim_model)
        
        # Transformer编码器
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=self.dim_model,
            nhead=self.n_heads,
            dim_feedforward=self.dim_feedforward,
            dropout=self.dropout,
            activation="relu",
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer, 
            num_layers=self.n_encoder_layers
        )
        
        # Transformer解码器
        decoder_layer = nn.TransformerDecoderLayer(
            d_model=self.dim_model,
            nhead=self.n_heads,
            dim_feedforward=self.dim_feedforward,
            dropout=self.dropout,
            activation="relu",
            batch_first=True
        )
        self.transformer_decoder = nn.TransformerDecoder(
            decoder_layer,
            num_layers=self.n_decoder_layers
        )
        
        # VAE组件（如果启用）
        if self.use_vae:
            self.vae_encoder = nn.Sequential(
                nn.Linear(self.dim_model, self.dim_feedforward),
                nn.ReLU(),
                nn.Linear(self.dim_feedforward, self.latent_dim * 2)  # mu和logvar
            )
            self.vae_decoder = nn.Sequential(
                nn.Linear(self.latent_dim, self.dim_feedforward),
                nn.ReLU(),
                nn.Linear(self.dim_feedforward, self.dim_model)
            )
        
        # 动作输出层
        self.action_head = nn.Linear(self.dim_model, 6)
        
        # 位置编码
        self.pos_encoding = nn.Parameter(torch.randn(1, 1000, self.dim_model))
        
    def encode_vision(self, images: Dict[str, torch.Tensor]) -> torch.Tensor:
        """编码视觉输入"""
        visual_features = []
        
        for image_name, image in images.items():
            # 确保图像格式正确 (B, C, H, W)
            if image.dim() == 3:
                image = image.unsqueeze(0)  # 添加batch维度
            
            # 通过视觉backbone
            features = self.vision_backbone(image)  # (B, 512, H, W)
            features = F.adaptive_avg_pool2d(features, (1, 1))  # (B, 512, 1, 1)
            features = features.squeeze(-1).squeeze(-1)  # (B, 512)
            
            # 投影到模型维度
            features = self.vision_projection(features)  # (B, dim_model)
            visual_features.append(features)
        
        # 合并所有视觉特征
        if visual_features:
            return torch.stack(visual_features, dim=1)  # (B, num_images, dim_model)
        else:
            return torch.zeros(1, 1, self.dim_model, device=images[list(images.keys())[0]].device)
    
    def encode_state(self, state: torch.Tensor) -> torch.Tensor:
        """编码状态输入"""
        return self.state_encoder(state)  # (B, dim_model)
    
    def reparameterize(self, mu: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
        """VAE重参数化"""
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std
    
    def forward(self, 
                images: Dict[str, torch.Tensor],
                state: torch.Tensor,
                action_query: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        前向传播
        
        Args:
            images: 图像字典 {"image_top": tensor, "image_wrist": tensor}
            state: 关节状态 (B, 6)
            action_query: 动作查询序列 (B, n_action_steps, dim_model)
        
        Returns:
            动作输出 (B, n_action_steps, 6)
        """
        batch_size = state.shape[0]
        
        # 编码视觉特征
        visual_features = self.encode_vision(images)  # (B, num_images, dim_model)
        
        # 编码状态特征
        state_features = self.encode_state(state)  # (B, dim_model)
        state_features = state_features.unsqueeze(1)  # (B, 1, dim_model)
        
        # 合并视觉和状态特征
        encoder_input = torch.cat([visual_features, state_features], dim=1)  # (B, num_images+1, dim_model)
        
        # 添加位置编码
        seq_len = encoder_input.shape[1]
        pos_encoding = self.pos_encoding[:, :seq_len, :]
        encoder_input = encoder_input + pos_encoding
        
        # Transformer编码
        encoded_features = self.transformer_encoder(encoder_input)  # (B, num_images+1, dim_model)
        
        # VAE编码（如果启用）
        if self.use_vae:
            vae_output = self.vae_encoder(encoded_features.mean(dim=1))  # (B, latent_dim * 2)
            mu, logvar = vae_output.chunk(2, dim=-1)
            latent = self.reparameterize(mu, logvar)  # (B, latent_dim)
            encoded_features = self.vae_decoder(latent).unsqueeze(1)  # (B, 1, dim_model)
        
        # 准备动作查询序列
        if action_query is None:
            action_query = torch.zeros(batch_size, self.n_action_steps, self.dim_model, 
                                     device=state.device)
        
        # Transformer解码
        decoded_features = self.transformer_decoder(action_query, encoded_features)  # (B, n_action_steps, dim_model)
        
        # 输出动作
        actions = self.action_head(decoded_features)  # (B, n_action_steps, 6)
        
        return actions


class ACTModelLoader:
    """ACT模型加载器"""
    
    def __init__(self, model_path: str, device: str = "auto"):
        self.model_path = Path(model_path)
        self.device = self._get_device(device)
        self.model = None
        self.config = None
        
    def _get_device(self, device: str) -> torch.device:
        """获取设备"""
        if device == "auto":
            if torch.cuda.is_available():
                return torch.device("cuda")
            elif hasattr(torch, 'npu') and torch.npu.is_available():
                return torch.device("npu")
            else:
                return torch.device("cpu")
        else:
            return torch.device(device)
    
    def load_model(self) -> ACTModel:
        """加载模型"""
        # 加载配置
        config_path = self.model_path / "config.json"
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # 创建模型
        self.model = ACTModel(self.config)
        
        # 加载权重
        weights_path = self.model_path / "model.safetensors"
        if weights_path.exists():
            from safetensors.torch import load_file
            state_dict = load_file(str(weights_path))
            self.model.load_state_dict(state_dict)
        else:
            # 尝试加载PyTorch格式
            weights_path = self.model_path / "model.pth"
            if weights_path.exists():
                state_dict = torch.load(weights_path, map_location=self.device)
                self.model.load_state_dict(state_dict)
            else:
                print("⚠️ 警告: 未找到模型权重文件，使用随机初始化的模型")
        
        # 移动到设备
        self.model = self.model.to(self.device)
        self.model.eval()
        
        print(f"✅ ACT模型加载成功，设备: {self.device}")
        return self.model
    
    def get_model(self) -> ACTModel:
        """获取模型实例"""
        if self.model is None:
            return self.load_model()
        return self.model


# 为了兼容性，保留SimpleACTModel
class SimpleACTModel(nn.Module):
    """简化的ACT模型，用于测试"""
    
    def __init__(self, input_dim=6, output_dim=6, hidden_dim=128):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, output_dim)
        
    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x
