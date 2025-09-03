"""
Device utilities for DoRobot inference.
"""

import torch
import logging
from typing import Optional


def auto_select_device() -> str:
    """
    Auto-select the best available device for DoRobot inference.
    
    Returns:
        str: Device name ('npu', 'cuda', 'mps', 'cpu')
    """
    # Check NPU first (Ascend)
    try:
        import torch_npu
        if hasattr(torch_npu, 'npu') and torch_npu.npu.is_available():
            logging.info("NPU backend detected, using npu.")
            return "npu"
    except ImportError:
        pass
    
    # Check CUDA
    if torch.cuda.is_available():
        logging.info("CUDA backend detected, using cuda.")
        return "cuda"
    
    # Check MPS (Apple Silicon)
    if torch.backends.mps.is_available():
        logging.info("Metal backend detected, using mps.")
        return "mps"
    
    # Fallback to CPU
    logging.warning("No accelerated backend detected. Using default cpu, this will be slow.")
    return "cpu"


def get_torch_device(device_name: Optional[str] = None) -> torch.device:
    """
    Get PyTorch device object.
    
    Args:
        device_name: Device name ('npu', 'cuda', 'mps', 'cpu'). If None, auto-select.
        
    Returns:
        torch.device: PyTorch device object
    """
    if device_name is None:
        device_name = auto_select_device()
    
    if device_name == "npu":
        try:
            import torch_npu
            return torch.device("npu")
        except ImportError:
            logging.warning("torch_npu not available, falling back to cpu")
            return torch.device("cpu")
    elif device_name == "cuda":
        return torch.device("cuda")
    elif device_name == "mps":
        return torch.device("mps")
    else:
        return torch.device("cpu")


def to_device(tensor_or_module, device_name: Optional[str] = None):
    """
    Move tensor or module to specified device.
    
    Args:
        tensor_or_module: PyTorch tensor or module
        device_name: Device name. If None, auto-select.
        
    Returns:
        Tensor or module moved to device
    """
    device = get_torch_device(device_name)
    return tensor_or_module.to(device)


def is_half_precision_supported(device_name: Optional[str] = None) -> bool:
    """
    Check if half precision (FP16) is supported on the device.
    
    Args:
        device_name: Device name. If None, auto-select.
        
    Returns:
        bool: True if half precision is supported
    """
    if device_name is None:
        device_name = auto_select_device()
    
    if device_name == "npu":
        return True  # NPU typically supports FP16
    elif device_name == "cuda":
        return True  # CUDA supports FP16
    elif device_name == "mps":
        return True  # MPS supports FP16
    else:
        return False  # CPU doesn't benefit from FP16


