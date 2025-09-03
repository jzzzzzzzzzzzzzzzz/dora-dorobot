# DoRobot 推理功能完整指南

## 概述

DoRobot现在具备了完整的推理功能，支持自动设备检测和适配，可以在不同硬件环境下运行（CPU、CUDA、NPU）。推理系统完全独立于LeRobot，使用DoRobot自己的数据格式和模型。

## 功能特性

### 1. 自动设备检测
- **NPU (Ascend)**：自动检测torch_npu并优先使用
- **CUDA (NVIDIA)**：检测CUDA可用性
- **MPS (Apple Silicon)**：支持Apple M系列芯片
- **CPU**：作为后备选项

### 2. 半精度支持
- 自动检测设备是否支持FP16
- 在支持的设备上自动启用半精度推理
- 提升推理速度和减少内存使用

### 3. 数据格式兼容
- 支持DoRobot训练的数据格式
- 320x240分辨率图像输入
- 6维状态和动作空间

## 使用方法

### 1. 基本测试（推荐先运行）

```bash
# 激活环境
conda activate dorobot

# 测试推理功能（不连接机器人）
python -m operating_platform.inference.cli --test_mode --policy.path=/data/dora/act_dorobot/pretrained_model --inference.duration=10
```

### 2. 真实机器人推理

```bash
# 基本推理（自动检测设备）
python -m operating_platform.inference.cli --robot.type=so101 --robot.port=/dev/ttyACM1 --policy.path=/data/dora/act_dorobot/pretrained_model

# 指定设备推理
python -m operating_platform.inference.cli --robot.type=so101 --robot.port=/dev/ttyACM1 --policy.path=/data/dora/act_dorobot/pretrained_model --policy.device=cuda

# 自定义摄像头设置
python -m operating_platform.inference.cli --robot.type=so101 --robot.port=/dev/ttyACM1 --policy.path=/data/dora/act_dorobot/pretrained_model --robot.cameras="{image_top: {width: 320, height: 240, fps: 15}, image_wrist: {width: 320, height: 240, fps: 15}}"

# 指定推理频率和时长
python -m operating_platform.inference.cli --robot.type=so101 --robot.port=/dev/ttyACM1 --policy.path=/data/dora/act_dorobot/pretrained_model --inference.fps=10 --inference.duration=60
```

### 3. 参数说明

```bash
python -m operating_platform.inference.cli [参数]

# 策略参数
--policy.path         模型路径 (默认: /data/dora/act_dorobot/pretrained_model)
--policy.device       设备类型 (npu, cuda, cpu, auto) (默认: auto)

# 机器人参数
--robot.type          机器人类型 (so101)
--robot.port          串口端口 (默认: /dev/ttyACM1)
--robot.id            机器人ID (默认: dorobot_arm)
--robot.cameras       摄像头配置 (YAML格式)

# 推理参数
--inference.fps       推理频率 (默认: 15)
--inference.duration  运行时长(秒) (0表示无限运行) (默认: 0)

# 其他参数
--test_mode           测试模式，不连接机器人
--display_data        显示摄像头数据
```

## 与LeRobot命令对比

### LeRobot命令（参考）
```bash
python -m lerobot.record \
  --robot.type=so101_follower \
  --robot.port=/dev/ttyACM1 \
  --robot.id=my_awesome_follower_arm \
  --robot.cameras="{ front: {type: opencv, index_or_path: 0, width: 320, height: 240, fps: 25}, wrist: {type: opencv, index_or_path: 2, width: 320, height: 240, fps: 25}}" \
  --teleop.type=so101_leader \
  --teleop.port=/dev/ttyACM0 \
  --teleop.id=my_awesome_leader_arm \
  --display_data=false \
  --dataset.push_to_hub=False \
  --dataset.repo_id=${HF_USER}/eval_record_0902_9 \
  --dataset.num_episodes=5 \
  --dataset.single_task="Grab the cube" \
  --policy.path=/home/HwHiAiUser/act_dorobot_010000/pretrained_model/
```

### DoRobot命令（对应）
```bash
python -m operating_platform.inference.cli \
  --robot.type=so101 \
  --robot.port=/dev/ttyACM1 \
  --robot.id=dorobot_arm \
  --robot.cameras="{image_top: {width: 320, height: 240, fps: 25}, image_wrist: {width: 320, height: 240, fps: 25}}" \
  --policy.path=/data/dora/act_dorobot/pretrained_model \
  --inference.fps=25 \
  --display_data=false
```

## 环境适配

### 1. 本地NVIDIA环境
```bash
# 自动检测到CUDA
✅ Using half precision (FP16) on cuda
```

### 2. Ascend开发板环境
```bash
# 自动检测到NPU
✅ Using half precision (FP16) on npu
```

### 3. CPU环境
```bash
# 自动回退到CPU
⚠️ No accelerated backend detected. Using default cpu, this will be slow.
```

## 文件结构

```
operating_platform/inference/
├── __init__.py              # 模块初始化
├── cli.py                   # 命令行接口（类似LeRobot）
├── policy.py                # 策略类
├── inference_runner.py      # 推理运行器
├── model.py                 # ACT模型实现
└── utils/
    ├── __init__.py
    ├── device.py            # 设备检测和适配
    ├── preprocessor.py      # 数据预处理器
    └── postprocessor.py     # 数据后处理器
```

## 核心组件

### 1. 设备检测 (`device.py`)
```python
from operating_platform.inference.utils import auto_select_device, get_torch_device

# 自动检测最佳设备
device = auto_select_device()  # 返回 'npu', 'cuda', 'mps', 或 'cpu'

# 获取PyTorch设备对象
torch_device = get_torch_device(device)
```

### 2. 策略类 (`policy.py`)
```python
from operating_platform.inference import DoRobotPolicy

# 创建策略（自动设备检测）
policy = DoRobotPolicy(model_path="/path/to/model")

# 推理
action = policy.get_action(observation)
```

### 3. 推理运行器 (`inference_runner.py`)
```python
from operating_platform.inference import InferenceRunner

# 创建运行器
runner = InferenceRunner(
    model_path="/path/to/model",
    robot_config=robot_config,
    device=None,  # 自动检测
    fps=15
)

# 运行推理
runner.start()
```

## 故障排除

### 1. 设备检测问题
```bash
# 检查可用设备
python check_device.py
```

### 2. 模型加载失败
- 确认模型路径正确
- 检查模型文件完整性
- 验证PyTorch版本兼容性

### 3. 数据类型错误
- 系统会自动处理设备间数据类型转换
- 半精度模型会自动转换输入数据类型

### 4. 机器人连接失败
- 检查USB连接
- 确认设备权限
- 验证机器人固件版本

## 性能优化

### 1. 推理速度
- 使用GPU/NPU加速
- 启用半精度推理
- 优化推理频率

### 2. 内存使用
- 半精度减少内存占用
- 及时释放不需要的张量
- 使用梯度检查点（如果需要）

### 3. 实时性
- 调整推理频率
- 优化数据预处理
- 使用异步处理

## 扩展功能

### 1. 自定义模型
```python
from operating_platform.inference.model import ACTModel

class CustomModel(ACTModel):
    def __init__(self, config):
        super().__init__(config)
        # 添加自定义层
```

### 2. 自定义预处理器
```python
from operating_platform.inference.utils.preprocessor import DoRobotPreprocessor

class CustomPreprocessor(DoRobotPreprocessor):
    def preprocess_images(self, images):
        # 自定义图像预处理
        pass
```

### 3. 多机器人支持
```python
# 可以扩展支持其他机器人类型
robot_config = OtherRobotConfig()
```

## 注意事项

1. **安全性**：确保机器人处于安全状态
2. **数据格式**：确保输入数据格式与训练时一致
3. **设备兼容性**：注意不同设备的兼容性
4. **实时性**：推理延迟可能影响控制效果
5. **环境隔离**：DoRobot推理完全独立于LeRobot

## 未来改进

1. **模型权重加载**：支持加载实际的训练权重
2. **归一化参数**：从训练数据中自动提取归一化参数
3. **多模态支持**：支持音频、深度图等更多模态
4. **分布式推理**：支持多GPU/多机器推理
5. **模型压缩**：支持模型量化和压缩

## 总结

DoRobot现在具备了完整的推理功能，包括：

- ✅ 自动设备检测和适配
- ✅ 半精度推理支持
- ✅ 类似LeRobot的命令行接口
- ✅ 完整的错误处理和故障排除
- ✅ 详细的文档和使用指南

现在你可以使用DoRobot自己的推理系统，完全独立于LeRobot，同时保持与DoRobot数据收集系统的兼容性！


