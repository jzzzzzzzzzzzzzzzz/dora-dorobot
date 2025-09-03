# DoRobot 远程测试指南

## 🎯 测试目标
在远程开发板 (HwHiAiUser@192.168.3.137) 上测试DoRobot的推理功能，排除本地环境问题，验证真实的抓取效果。

## 📦 打包和部署

### 1. 执行打包脚本
```bash
chmod +x package_for_remote_test.sh
./package_for_remote_test.sh
```

### 2. 自动部署
脚本会自动：
- 打包项目文件
- 发送到远程服务器
- 在远程服务器上解压
- 清理临时文件

## 🔧 远程环境准备

### 1. 登录远程服务器
```bash
ssh HwHiAiUser@192.168.3.137
```

### 2. 检查项目部署
```bash
cd /home/HwHiAiUser/DoRobot-Preview/DoRobot-Preview
ls -la
```

### 3. 检查环境依赖
```bash
# 检查conda环境
conda env list

# 激活Dora环境
conda activate dr-robot-so101

# 检查Dora
dora --version
```

### 4. 检查硬件设备
```bash
# 检查机器人设备
ls -la /dev/ttyACM*

# 检查设备权限
sudo chmod 666 /dev/ttyACM*
```

## 🧪 测试执行

### 1. 基础功能测试
```bash
# 进入项目目录
cd /home/HwHiAiUser/DoRobot-Preview/DoRobot-Preview

# 激活环境
conda activate dr-robot-so101

# 运行30秒测试
timeout 30 dora run operating_platform/robot/robots/so101_v1/dora_working_autonomous_dataflow.yml
```

### 2. 长时间测试
```bash
# 运行60秒测试
timeout 60 dora run operating_platform/robot/robots/so101_v1/dora_working_autonomous_dataflow.yml
```

### 3. 调试模式测试
```bash
# 使用调试脚本
./run_autonomous_control_timeout.sh
```

## 📊 测试观察要点

### 1. 动作幅度
- ✅ 观察机械臂动作是否精细（±0.01°级别）
- ✅ 检查是否有大幅跳跃动作
- ✅ 验证动作是否符合LeRobot标准

### 2. 抓取效果
- ✅ 观察夹爪动作是否精确（-0.02幅度）
- ✅ 检查抓取策略是否合理
- ✅ 验证是否能成功抓取目标物体

### 3. 系统稳定性
- ✅ 检查是否有错误信息
- ✅ 观察系统是否稳定运行
- ✅ 验证安全保护机制是否生效

### 4. 推理质量
- ✅ 观察推理速度
- ✅ 检查动作生成是否合理
- ✅ 验证视觉信息处理是否正确

## 🔍 问题诊断

### 1. 设备连接问题
```bash
# 检查设备状态
ls -la /dev/ttyACM*
dmesg | grep ttyACM

# 重新设置权限
sudo chmod 666 /dev/ttyACM*
```

### 2. 环境依赖问题
```bash
# 检查Python环境
python --version
pip list | grep dora

# 重新安装依赖
conda install -c conda-forge dora
```

### 3. 网络连接问题
```bash
# 检查网络连接
ping 192.168.3.137
ssh HwHiAiUser@192.168.3.137 "echo 'Connection OK'"
```

## 📈 测试结果记录

### 测试环境信息
- **远程服务器**: HwHiAiUser@192.168.3.137
- **项目路径**: /home/HwHiAiUser/DoRobot-Preview/DoRobot-Preview
- **测试时间**: [记录测试时间]
- **测试版本**: [记录当前版本]

### 测试结果
| 测试项目 | 结果 | 备注 |
|---------|------|------|
| 动作幅度 | ✅/❌ | 是否符合LeRobot标准 |
| 抓取效果 | ✅/❌ | 是否能成功抓取 |
| 系统稳定性 | ✅/❌ | 是否稳定运行 |
| 推理质量 | ✅/❌ | 推理是否合理 |

### 问题记录
- [记录发现的问题]
- [记录解决方案]
- [记录改进建议]

## 🎉 成功标准

测试成功的标准：
1. ✅ 机械臂动作精细，符合LeRobot标准
2. ✅ 能够成功执行抓取动作
3. ✅ 系统稳定运行，无错误
4. ✅ 推理质量良好，动作合理

## 📞 联系信息

如有问题，请联系：
- 远程服务器管理员
- DoRobot开发团队
