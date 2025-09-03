## 0. Environment

ascend cann 补丁 

--TODO--


pip3 install torchvision==0.20.1

https://www.hiascend.com/document/detail/zh/Pytorch/710/configandinstg/instg/insg_0010.html

## 1. Start 

get this project

```sh
git cloen https://github.com/jzzzzzzzzzzzzzzzz/dora-dorobot.git
cd dora-dorobot
```

### 1.1. Initital DoRobot enviroment

creat conda env

```sh
conda create --name op python==3.11
```

activate conda env

```sh
conda activate op
```

install this project

```sh
pip install -e .
```

**install pytorch, according to your platform**

如果是ascend 则是torch—npu 

```sh
# ROCM 6.1 (Linux only)
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/rocm6.1
# ROCM 6.2.4 (Linux only)
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/rocm6.2.4
# CUDA 11.8
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu118
# CUDA 12.4
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
# CUDA 12.6
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu126
# CPU only
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cpu
```

install libportaudio2

```
sudo apt install libportaudio2
```

### 1.2. Initital SO101 enviroment

Open a new terminal and switch to the DoRobot-Preview project directory.

creat conda env

```sh
conda create --name dr-robot-so101 python==3.10
```

activate conda env

```sh
conda activate dr-robot-so101
```

install robot enviroment

```sh
cd operating_platform/robot/robots/so101_v1
pip install -e .
```

---------------打补丁-----------------

TODO

参考
diff --git a/lerobot/common/datasets/utils.py b/lerobot/common/datasets/utils.py
index 9d8a54db..ba57b37b 100644
--- a/lerobot/common/datasets/utils.py
+++ b/lerobot/common/datasets/utils.py
@@ -755,7 +755,7 @@ def validate_feature_numpy_array(
         actual_shape = value.shape
 
         if actual_dtype != np.dtype(expected_dtype):
-            error_message += f"The feature '{name}' of dtype '{actual_dtype}' is not of the expected dtype '{expected_dtype}'.\n"
+            # error_message += f"The feature '{name}' of dtype '{actual_dtype}' is not of the expected dtype '{expected_dtype}'.\n"
 
         if actual_shape != expected_shape:
             error_message += f"The feature '{name}' of shape '{actual_shape}' does not have the expected shape '{expected_shape}'.\n"
diff --git a/lerobot/common/policies/act/modeling_act.py b/lerobot/common/policies/act/modeling_act.py
index 72d4df03..98fbd4c5 100644
--- a/lerobot/common/policies/act/modeling_act.py
+++ b/lerobot/common/policies/act/modeling_act.py
@@ -72,6 +72,7 @@ class ACTPolicy(PreTrainedPolicy):
         )
 
         self.model = ACT(config)
+        self.model = self.model.half()
 
         if config.temporal_ensemble_coeff is not None:
             self.temporal_ensembler = ACTTemporalEnsembler(config.temporal_ensemble_coeff, config.chunk_size)
@@ -337,10 +338,12 @@ class ACT(nn.Module):
                 weights=config.pretrained_backbone_weights,
                 norm_layer=FrozenBatchNorm2d,
             )
+            backbone_model = backbone_model.half()
             # Note: The assumption here is that we are using a ResNet model (and hence layer4 is the final
             # feature map).
             # Note: The forward method of this returns a dict: {"feature_map": output}.
             self.backbone = IntermediateLayerGetter(backbone_model, return_layers={"layer4": "feature_map"})
+            self.backbone = self.backbone.half()
 
         # Transformer (acts as VAE decoder when training with the variational objective).
         self.encoder = ACTEncoder(config)
@@ -488,7 +491,7 @@ class ACT(nn.Module):
 
             # For a list of images, the H and W may vary but H*W is constant.
             for img in batch["observation.images"]:
-                cam_features = self.backbone(img)["feature_map"]
+                cam_features = self.backbone(img.half())["feature_map"]
                 cam_pos_embed = self.encoder_cam_feat_pos_embed(cam_features).to(dtype=cam_features.dtype)
                 cam_features = self.encoder_img_feat_input_proj(cam_features)
 
diff --git a/lerobot/common/policies/pretrained.py b/lerobot/common/policies/pretrained.py
index da4ef157..026aafc9 100644
--- a/lerobot/common/policies/pretrained.py
+++ b/lerobot/common/policies/pretrained.py
@@ -132,6 +132,7 @@ class PreTrainedPolicy(nn.Module, HubMixin, abc.ABC):
 
         policy.to(config.device)
         policy.eval()
+        policy = policy.half()
         return policy
 
     @classmethod
diff --git a/lerobot/common/utils/utils.py b/lerobot/common/utils/utils.py
index 563a7b81..55fb7ed1 100644
--- a/lerobot/common/utils/utils.py
+++ b/lerobot/common/utils/utils.py
@@ -24,6 +24,7 @@ from pathlib import Path
 
 import numpy as np
 import torch
+import torch_npu
 
 
 def none_or_int(value):
@@ -46,9 +47,13 @@ def auto_select_torch_device() -> torch.device:
     elif torch.backends.mps.is_available():
         logging.info("Metal backend detected, using cuda.")
         return torch.device("mps")
+    elif torch_npu.npu.is_available():
+        logging.info("Metal backend detected, using npu.")
+        return torch.device("npu")
     else:
         logging.warning("No accelerated backend detected. Using default cpu, this will be slow.")
         return torch.device("cpu")
+        
 
 

--------------------------------------

### 1.3. Calibrate SO101 Arm

calibrate leader arm

```
cd operating_platform/robot/components/arm_normal_so101_v1/
dora run dora_calibrate_leader.yml
```

calibrate follower arm

```
cd operating_platform/robot/components/arm_normal_so101_v1/
dora run dora_calibrate_follower.yml
```

## 2. Teleoperate SO101 Arm

```
cd operating_platform/robot/components/arm_normal_so101_v1/
dora run dora_teleoperate_arm.yml
```

## 3. Record Data

You need to unplug all camera and robotic arm data interfaces first, then plug in the head camera.

```
ls /dev/video*
```

you can see:

```
/dev/video0 /dev/video1
```

If you see other indices, please make sure that all other cameras have been disconnected from the computer. If you are unable to remove them, please modify the camera index in the YAML file. 

then plug in the head camera.

```
ls /dev/video*
```

you can see:

```
/dev/video0 /dev/video1 /dev/video2 /dev/video3
```

now, you finish camera connect.

Next, connect the robotic arm by first plugging in the leader arm's USB interface.

```
ls /dev/ttyACM*
```

you can see:

```
/dev/ttyACM0
```

Then plugging in the follower arm's USB interface.

```
ls /dev/ttyACM*
```

you can see:

```
/dev/ttyACM0 /dev/ttyACM1
```

run dora data flow 

```
cd operating_platform/robot/robots/so101_v1
conda activate dr-robot-so101
dora run dora_teleoperate_dataflow.yml
```

Open a new terminal, then:

```
bash scripts/run_so101_cli.sh
```

You can modify the task name and task description by adjusting the parameters within the run_so101_cli.sh file.


# Acknowledgment
 - LeRobot 🤗: [https://github.com/huggingface/lerobot](https://github.com/huggingface/lerobot)
