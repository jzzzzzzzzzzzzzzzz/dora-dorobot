#!/usr/bin/env python3
"""
Simple DoRobot Inference Test - CPU Only
"""

import sys
import os
import time
import numpy as np
import torch

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from operating_platform.inference import DoRobotPolicy
from operating_platform.core.daemon import Daemon
from operating_platform.robot.robots.configs import SO101RobotConfig


def main():
    """Simple inference test with CPU only."""
    print("=" * 60)
    print("Simple DoRobot Inference Test - CPU Only")
    print("=" * 60)
    
    model_path = "/data/dora/act_dorobot/pretrained_model"
    print(f"Model path: {model_path}")
    print("Device: cpu (forced)")
    print("=" * 60)
    
    try:
        # Create robot config
        robot_config = SO101RobotConfig()
        
        # Create daemon
        daemon = Daemon(fps=5)
        daemon.start(robot_config)
        print("✅ Daemon started successfully")
        
        # Load policy with CPU device
        policy = DoRobotPolicy(model_path, device="cpu")
        print("✅ Policy loaded successfully")
        
        print("Starting inference loop...")
        print("Press Ctrl+C to stop")
        
        # Run inference loop
        start_time = time.time()
        step_count = 0
        
        while time.time() - start_time < 10:  # 10 seconds
            step_start = time.time()
            step_count += 1
            
            try:
                # Update daemon to get latest observation
                daemon.update()
                
                # Get observation from daemon
                observation = daemon.get_observation()
                
                if observation is None:
                    print("Warning: No observation available, using dummy data")
                    observation = {
                        'images': {
                            'image_top': np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8),
                            'image_wrist': np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
                        },
                        'state': np.random.randn(6).astype(np.float32)
                    }
                
                # Run inference
                action = policy.get_action(observation)
                
                # Send action through daemon
                daemon.set_pre_action({"action": action})
                
                # Print progress
                if step_count % 5 == 0:
                    elapsed = time.time() - start_time
                    print(f"Step {step_count}: Action = {action}, Time = {elapsed:.1f}s")
                
                # Timing control
                step_elapsed = time.time() - step_start
                sleep_time = max(0, 1.0 / 5 - step_elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                print(f"Error in step {step_count}: {e}")
                time.sleep(1.0 / 5)
                
    except KeyboardInterrupt:
        print("\nInference stopped by user")
    except Exception as e:
        print(f"❌ Error during inference: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'daemon' in locals():
            daemon.stop()
        print("Inference completed")


if __name__ == "__main__":
    main()


