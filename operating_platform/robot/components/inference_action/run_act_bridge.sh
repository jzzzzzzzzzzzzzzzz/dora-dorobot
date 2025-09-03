#!/bin/bash
"""
ACT模型推理桥接启动脚本
在dorobot环境中运行ACT模型推理组件
"""

# 激活dorobot环境
source /home/dora/miniconda3/etc/profile.d/conda.sh
conda activate dorobot

# 设置环境变量
export PYTHONPATH="/data/dora/DoRobot-Preview:$PYTHONPATH"
export MODEL_PATH="/data/dora/act_dorobot/pretrained_model"
export DEVICE="auto"
export USE_REAL_MODEL="true"
export MAX_RUNTIME="60"

# 运行ACT模型推理组件
python3 /data/dora/DoRobot-Preview/operating_platform/robot/components/inference_action/main_act_bridge.py
