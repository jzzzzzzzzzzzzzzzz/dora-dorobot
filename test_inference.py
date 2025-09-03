#!/usr/bin/env python3
"""
Simple test script for DoRobot inference.
"""

import numpy as np
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import torch
        print("✅ PyTorch available")
        print(f"   Version: {torch.__version__}")
        print(f"   CUDA available: {torch.cuda.is_available()}")
    except ImportError:
        print("❌ PyTorch not available")
        return False
    
    try:
        from operating_platform.inference.policy import DoRobotPolicy
        print("✅ DoRobotPolicy imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import DoRobotPolicy: {e}")
        return False


def test_model_files():
    """Test if model files exist."""
    print("Testing model files...")
    
    model_path = "/data/dora/act_dorobot/pretrained_model"
    required_files = ["config.json", "model.safetensors"]
    
    for file_name in required_files:
        file_path = os.path.join(model_path, file_name)
        if os.path.exists(file_path):
            print(f"✅ {file_name} exists")
        else:
            print(f"❌ {file_name} not found at {file_path}")
            return False
    
    return True


def test_dataset_files():
    """Test if dataset files exist."""
    print("Testing dataset files...")
    
    dataset_path = "/data/dora/act_dorobot_dataset/record_0902"
    required_files = ["meta/info.json", "data/chunk-000/episode_000000.parquet"]
    
    for file_name in required_files:
        file_path = os.path.join(dataset_path, file_name)
        if os.path.exists(file_path):
            print(f"✅ {file_name} exists")
        else:
            print(f"❌ {file_name} not found at {file_path}")
            return False
    
    return True


def test_config_loading():
    """Test if model config can be loaded."""
    print("Testing config loading...")
    
    import json
    
    try:
        config_path = "/data/dora/act_dorobot/pretrained_model/config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print("✅ Config loaded successfully")
        print(f"   Model type: {config.get('type', 'unknown')}")
        print(f"   Input features: {list(config.get('input_features', {}).keys())}")
        print(f"   Output features: {list(config.get('output_features', {}).keys())}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return False


def test_policy_loading():
    """Test if policy can be loaded."""
    print("Testing policy loading...")
    
    try:
        from operating_platform.inference.policy import DoRobotPolicy
        model_path = "/data/dora/act_dorobot/pretrained_model"
        policy = DoRobotPolicy(model_path, device="cpu")
        print("✅ Policy loaded successfully")
        return policy
    except Exception as e:
        print(f"❌ Failed to load policy: {e}")
        return None


def test_inference_with_dummy_data(policy):
    """Test inference with dummy data."""
    print("Testing inference with dummy data...")
    
    # Create dummy observation
    dummy_observation = {
        'images': {
            'image_top': np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8),
            'image_wrist': np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
        },
        'state': np.random.randn(6).astype(np.float32)
    }
    
    try:
        action = policy.get_action(dummy_observation)
        print(f"✅ Inference successful, action shape: {action.shape}")
        print(f"   Action values: {action}")
        return True
    except Exception as e:
        print(f"❌ Inference failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 50)
    print("DoRobot Inference Test")
    print("=" * 50)
    
    # Test 1: Check imports
    imports_ok = test_imports()
    
    # Test 2: Check model files
    model_files_ok = test_model_files()
    
    # Test 3: Check dataset files
    dataset_files_ok = test_dataset_files()
    
    # Test 4: Check config loading
    config_ok = test_config_loading()
    
    # Test 5: Test policy loading and inference (if imports are ok)
    inference_ok = False
    if imports_ok:
        policy = test_policy_loading()
        if policy is not None:
            inference_ok = test_inference_with_dummy_data(policy)
    
    print("=" * 50)
    print("Test Summary:")
    print(f"  Imports: {'✅' if imports_ok else '❌'}")
    print(f"  Model files: {'✅' if model_files_ok else '❌'}")
    print(f"  Dataset files: {'✅' if dataset_files_ok else '❌'}")
    print(f"  Config loading: {'✅' if config_ok else '❌'}")
    print(f"  Inference: {'✅' if inference_ok else '❌'}")
    print("=" * 50)


if __name__ == "__main__":
    main()
