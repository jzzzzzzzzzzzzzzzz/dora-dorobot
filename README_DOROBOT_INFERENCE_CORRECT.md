# DoRobot 推理功能完整使用指南

## 重要发现：推理系统需要Dora数据流

经过测试发现，DoRobot的推理系统**确实需要Dora数据流**作为中间层，就像录制系统一样。这是因为：

1. **硬件连接问题**：直接连接机器人会出现timeout错误
2. **数据流依赖**：DoRobot的机器人控制依赖于Dora数据流
3. **架构设计**：DoRobot设计为与Dora数据流配合工作

## 正确的推理流程（需要两个终端）

### 终端1：启动Dora数据流
```bash
# 激活环境
conda activate dr-robot-so101

# 进入机器人目录
cd /data/dora/DoRobot-Preview/operating_platform/robot/robots/so101_v1

# 启动Dora数据流（处理摄像头和机器人数据）
dora run dora_teleoperate_dataflow.yml
```

### 终端2：运行推理
```bash
# 激活环境
conda activate dorobot

# 运行推理命令
python dora_inference.py \
  --model_path=/data/dora/act_dorobot/pretrained_model \
  --device=cpu \
  --fps=10 \
  --duration=30
```

## 详细执行过程

### 1. Dora数据流的作用
- **摄像头管理**：处理摄像头数据流
- **机器人控制**：管理机器人串口通信
- **数据同步**：确保数据的时间同步
- **错误处理**：处理硬件连接问题

### 2. 推理系统的工作流程
```
Dora数据流 → Daemon → 推理策略 → 动作输出 → 机器人控制
```

1. **Dora数据流**：提供摄像头和机器人数据
2. **Daemon**：管理数据流和动作输出
3. **推理策略**：运行模型推理
4. **动作输出**：通过daemon发送到机器人

## 命令对比

### 录制流程（参考）
```bash
# 终端1
conda activate dr-robot-so101
cd /data/dora/DoRobot-Preview/operating_platform/robot/robots/so101_v1
dora run dora_teleoperate_dataflow.yml

# 终端2
conda activate dorobot
python operating_platform/core/main.py \
  --robot.type=so101 \
  --record.repo_id=jzzz/record_0901 \
  --record.single_task="Grab the cube" \
  --record.fps=30 \
  --record.num_episodes=3 \
  --record.episode_duration_s=20 \
  --record.inter_episode_sleep_s=5
```

### 推理流程（对应）
```bash
# 终端1
conda activate dr-robot-so101
cd /data/dora/DoRobot-Preview/operating_platform/robot/robots/so101_v1
dora run dora_teleoperate_dataflow.yml

# 终端2
conda activate dorobot
python dora_inference.py \
  --model_path=/data/dora/act_dorobot/pretrained_model \
  --device=cpu \
  --fps=10 \
  --duration=30
```

## 参数说明

### dora_inference.py 参数
```bash
--model_path    模型路径 (默认: /data/dora/act_dorobot/pretrained_model)
--device        设备类型 (cpu, cuda, npu) (默认: cpu)
--fps           推理频率 (默认: 10)
--duration      运行时长(秒) (默认: 30)
```

## 故障排除

### 1. Timeout错误
如果看到 `SO101 Image Received Timeout` 或 `SO101 Joint Received Timeout`：
- 确保Dora数据流正在运行
- 重新启动Dora数据流
- 检查USB连接

### 2. 机器人不动作
如果机器人静止不动：
- 确保两个终端都在运行
- 检查推理输出是否正常
- 验证动作是否正确发送

### 3. 环境问题
- 确保使用正确的conda环境
- 检查Python路径设置
- 验证模型文件存在

## 测试建议

### 1. 先测试Dora数据流
```bash
# 终端1
conda activate dr-robot-so101
cd /data/dora/DoRobot-Preview/operating_platform/robot/robots/so101_v1
dora run dora_teleoperate_dataflow.yml
```

### 2. 再测试推理
```bash
# 终端2
conda activate dorobot
python dora_inference.py --duration=10 --fps=5
```

### 3. 观察输出
- 检查是否有timeout错误
- 观察推理动作输出
- 确认机器人响应

## 性能优化

### 1. 推理频率
- 降低FPS可以减少系统负载
- 建议从5-10 FPS开始测试
- 根据硬件性能调整

### 2. 设备选择
- CPU：稳定，适合测试
- CUDA：快速，适合高性能
- NPU：Ascend专用，需要适配

### 3. 模型优化
- 使用半精度推理
- 优化模型结构
- 减少数据预处理时间

## 总结

DoRobot的推理系统需要：
1. **Dora数据流**：处理硬件连接
2. **Daemon**：管理数据流
3. **推理策略**：运行模型
4. **两个终端**：分别运行数据流和推理

这与录制系统的架构完全一致，确保了系统的稳定性和可靠性。


