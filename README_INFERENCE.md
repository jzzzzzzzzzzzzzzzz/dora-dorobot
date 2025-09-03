# DoRobot 推理功能使用指南

## 概述

DoRobot现在具备了完整的推理功能，可以加载训练好的模型并进行机器人控制。推理系统包括：

- **数据预处理**：图像和状态数据的归一化处理
- **模型推理**：ACT模型的前向推理
- **数据后处理**：动作输出的反归一化
- **机器人控制**：与SO101机器人的集成

## 功能特性

### 1. 模型支持
- 支持ACT (Action Chunking Transformer) 模型
- 兼容DoRobot训练的数据格式
- 支持320x240分辨率的图像输入
- 支持6维状态和动作空间

### 2. 设备支持
- CPU推理
- CUDA GPU推理
- NPU推理（Ascend开发板）

### 3. 数据格式
- **输入图像**：`image_top` 和 `image_wrist` (240, 320, 3)
- **输入状态**：6维关节角度
- **输出动作**：6维关节目标位置

## 使用方法

### 1. 基本测试

测试推理功能（不连接机器人）：
```bash
# 激活环境
conda activate dorobot

# 运行测试
python run_inference.py --test_mode --duration 10
```

### 2. 真实机器人控制

连接真实机器人进行控制：
```bash
# 确保机器人已连接
python run_inference.py --device cpu --fps 15 --duration 60
```

### 3. 参数说明

```bash
python run_inference.py [参数]

参数说明：
--model_path    模型路径 (默认: /data/dora/act_dorobot/pretrained_model)
--device        设备类型 (cpu, cuda, npu) (默认: cpu)
--fps           推理频率 (默认: 15)
--duration      运行时长(秒) (0表示无限运行) (默认: 60)
--test_mode     测试模式，不连接机器人
```

## 文件结构

```
operating_platform/inference/
├── __init__.py              # 模块初始化
├── policy.py                # 策略类
├── inference_runner.py      # 推理运行器
├── model.py                 # ACT模型实现
└── utils/
    ├── __init__.py
    ├── preprocessor.py      # 数据预处理器
    └── postprocessor.py     # 数据后处理器
```

## 核心组件

### 1. DoRobotPolicy
主要的推理策略类，整合了预处理、模型推理和后处理。

```python
from operating_platform.inference import DoRobotPolicy

# 创建策略
policy = DoRobotPolicy(model_path="/path/to/model", device="cpu")

# 推理
observation = {
    'images': {
        'image_top': image_top,
        'image_wrist': image_wrist
    },
    'state': robot_state
}
action = policy.get_action(observation)
```

### 2. InferenceRunner
推理运行器，管理机器人连接和推理循环。

```python
from operating_platform.inference import InferenceRunner

# 创建运行器
runner = InferenceRunner(
    model_path="/path/to/model",
    robot_config=robot_config,
    device="cpu",
    fps=15
)

# 运行推理
runner.start()
```

### 3. 数据预处理器
处理输入数据的归一化和格式转换。

### 4. 数据后处理器
处理模型输出的反归一化和格式转换。

## 模型加载

### 1. 模型文件要求
模型目录应包含：
- `config.json`：模型配置文件
- `model.safetensors`：模型权重文件

### 2. 配置文件格式
```json
{
    "type": "act",
    "input_features": {
        "observation.state": {"type": "STATE", "shape": [6]},
        "observation.images.image_top": {"type": "VISUAL", "shape": [3, 240, 320]},
        "observation.images.image_wrist": {"type": "VISUAL", "shape": [3, 240, 320]}
    },
    "output_features": {
        "action": {"type": "ACTION", "shape": [6]}
    }
}
```

## 故障排除

### 1. 模型加载失败
- 检查模型路径是否正确
- 确认模型文件存在且完整
- 检查PyTorch版本兼容性

### 2. 归一化参数缺失
- 当前使用默认归一化参数
- 可以手动设置归一化参数
- 建议从训练数据中计算归一化参数

### 3. 机器人连接失败
- 检查USB连接
- 确认设备权限
- 检查机器人固件版本

### 4. 推理性能问题
- 降低推理频率（--fps参数）
- 使用更快的设备（GPU/NPU）
- 优化图像预处理

## 扩展功能

### 1. 自定义模型
可以继承`ACTModel`类实现自定义模型：

```python
from operating_platform.inference.model import ACTModel

class CustomModel(ACTModel):
    def __init__(self, config):
        super().__init__(config)
        # 添加自定义层
        
    def forward(self, inputs):
        # 自定义前向传播
        pass
```

### 2. 自定义预处理器
继承`DoRobotPreprocessor`类：

```python
from operating_platform.inference.utils.preprocessor import DoRobotPreprocessor

class CustomPreprocessor(DoRobotPreprocessor):
    def preprocess_images(self, images):
        # 自定义图像预处理
        pass
```

### 3. 多机器人支持
可以扩展支持其他机器人类型：

```python
# 在InferenceRunner中添加其他机器人配置
robot_config = OtherRobotConfig()
```

## 性能优化

### 1. 推理速度优化
- 使用GPU/NPU加速
- 批量处理多个观测
- 优化模型结构

### 2. 内存优化
- 使用混合精度训练
- 优化数据加载
- 减少不必要的内存拷贝

### 3. 实时性优化
- 异步数据预处理
- 流水线处理
- 缓存机制

## 注意事项

1. **安全性**：确保机器人处于安全状态
2. **数据格式**：确保输入数据格式与训练时一致
3. **设备兼容性**：注意不同设备的兼容性
4. **实时性**：推理延迟可能影响控制效果

## 未来改进

1. **模型权重加载**：支持加载实际的训练权重
2. **归一化参数**：从训练数据中自动提取归一化参数
3. **多模态支持**：支持音频、深度图等更多模态
4. **分布式推理**：支持多GPU/多机器推理
5. **模型压缩**：支持模型量化和压缩


