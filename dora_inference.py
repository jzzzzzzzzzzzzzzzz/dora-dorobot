#!/usr/bin/env python3
"""
DoRobot Inference Script with Dora Dataflow

This script requires Dora dataflow to be running first, similar to the recording process.
Usage:
  1. Terminal 1: dora run dora_teleoperate_dataflow.yml
  2. Terminal 2: python dora_inference.py
"""

import argparse
import sys
import os
import time
import numpy as np
import threading

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from operating_platform.inference import DoRobotPolicy
from operating_platform.core.daemon import Daemon
from operating_platform.robot.robots.configs import SO101RobotConfig


def main():
    """Main function for DoRobot inference with Dora dataflow."""
    parser = argparse.ArgumentParser(description="DoRobot Inference with Dora Dataflow")
    parser.add_argument(
        "--model_path", 
        type=str, 
        default="/data/dora/act_dorobot/pretrained_model",
        help="Path to the trained model directory"
    )
    parser.add_argument(
        "--device", 
        type=str, 
        default="cpu",
        help="Device to run inference on (cpu, cuda, npu)"
    )
    parser.add_argument(
        "--fps", 
        type=int, 
        default=10,
        help="Target inference frequency"
    )
    parser.add_argument(
        "--duration", 
        type=int, 
        default=30,
        help="Duration to run inference in seconds"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("DoRobot Inference with Dora Dataflow")
    print("=" * 60)
    print(f"Model path: {args.model_path}")
    print(f"Device: {args.device}")
    print(f"FPS: {args.fps}")
    print(f"Duration: {args.duration} seconds")
    print("=" * 60)
    print("⚠️  IMPORTANT: Make sure Dora dataflow is running first!")
    print("   Terminal 1: dora run dora_teleoperate_dataflow.yml")
    print("   Terminal 2: python dora_inference.py")
    print("=" * 60)
    
    run_inference_with_dora(args)


def run_inference_with_dora(args):
    """Run inference using Dora dataflow and daemon."""
    print("Starting DoRobot daemon...")
    
    try:
        # Create robot config
        robot_config = SO101RobotConfig()
        
        # Create daemon
        daemon = Daemon(fps=args.fps)
        daemon.start(robot_config)
        print("✅ Daemon started successfully")
        
        # Load policy
        policy = DoRobotPolicy(args.model_path, device=args.device)
        print("✅ Policy loaded successfully")
        
        print("Starting inference loop...")
        print("Press Ctrl+C to stop")
        
        # Run inference loop
        start_time = time.time()
        step_count = 0
        
        while time.time() - start_time < args.duration:
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
                sleep_time = max(0, 1.0 / args.fps - step_elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                if step_count % 10 == 0:
                    print(f"Error in step {step_count}: {e}")
                time.sleep(1.0 / args.fps)
                
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
