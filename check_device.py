#!/usr/bin/env python3
"""Check available devices for DoRobot inference."""

import torch

def check_devices():
    """Check available devices."""
    print("=" * 50)
    print("Device Check for DoRobot")
    print("=" * 50)
    
    # Check PyTorch
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device count: {torch.cuda.device_count()}")
        print(f"Current CUDA device: {torch.cuda.current_device()}")
    
    # Check torch_npu
    try:
        import torch_npu
        print(f"torch_npu available: True")
        if hasattr(torch_npu, 'npu'):
            print(f"NPU available: {torch_npu.npu.is_available()}")
            if torch_npu.npu.is_available():
                print(f"NPU device count: {torch_npu.npu.device_count()}")
        else:
            print("torch_npu.npu not available")
    except ImportError:
        print("torch_npu not available")
    
    # Check MPS (Apple Silicon)
    print(f"MPS available: {torch.backends.mps.is_available()}")
    
    # Determine best device
    device = auto_select_device()
    print(f"Recommended device: {device}")
    print("=" * 50)

def auto_select_device():
    """Auto-select the best available device."""
    # Check NPU first (Ascend)
    try:
        import torch_npu
        if hasattr(torch_npu, 'npu') and torch_npu.npu.is_available():
            return "npu"
    except ImportError:
        pass
    
    # Check CUDA
    if torch.cuda.is_available():
        return "cuda"
    
    # Check MPS (Apple Silicon)
    if torch.backends.mps.is_available():
        return "mps"
    
    # Fallback to CPU
    return "cpu"

if __name__ == "__main__":
    check_devices()


