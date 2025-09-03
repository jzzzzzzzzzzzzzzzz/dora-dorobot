#!/usr/bin/env python3
"""
DoRobot Inference CLI - Similar to LeRobot's interface

Usage:
  1. Terminal 1: dora run dora_teleoperate_dataflow.yml
  2. Terminal 2: python -m operating_platform.inference.cli_dorobot --policy.path=/path/to/model --robot.type=so101 --fps=10
"""

import argparse
import sys
import os
import time
import numpy as np
import torch

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from operating_platform.inference import DoRobotPolicy
from operating_platform.core.daemon import Daemon
from operating_platform.robot.robots.configs import SO101RobotConfig


def parse_nested_args(args):
    """Parse nested arguments like policy.path."""
    parsed = {}
    for arg, value in vars(args).items():
        if '.' in arg:
            # Handle nested arguments like policy.path
            parts = arg.split('.')
            current = parsed
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        else:
            parsed[arg] = value
    return parsed


def main():
    """Main function for DoRobot inference CLI."""
    parser = argparse.ArgumentParser(description="DoRobot Inference CLI")
    
    # Policy arguments
    parser.add_argument(
        "--policy.path", 
        type=str, 
        default="/data/dora/act_dorobot/pretrained_model",
        help="Path to the trained model directory"
    )
    parser.add_argument(
        "--policy.device", 
        type=str, 
        default=None,
        help="Device to run inference on (cpu, cuda, npu). If None, auto-select."
    )
    
    # Robot arguments
    parser.add_argument(
        "--robot.type", 
        type=str, 
        default="so101",
        help="Robot type (so101)"
    )
    parser.add_argument(
        "--robot.cameras", 
        type=str, 
        default=None,
        help="Camera configuration (not used in current implementation)"
    )
    
    # Inference arguments
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
    parser.add_argument(
        "--display_data", 
        action="store_true",
        help="Display data during inference"
    )
    
    args = parser.parse_args()
    parsed_args = parse_nested_args(args)
    
    print("=" * 60)
    print("DoRobot Inference CLI")
    print("=" * 60)
    print(f"Policy path: {parsed_args['policy']['path']}")
    print(f"Policy device: {parsed_args['policy']['device']}")
    print(f"Robot type: {parsed_args['robot']['type']}")
    print(f"FPS: {parsed_args['fps']}")
    print(f"Duration: {parsed_args['duration']} seconds")
    print("=" * 60)
    print("⚠️  IMPORTANT: Make sure Dora dataflow is running first!")
    print("   Terminal 1: dora run dora_teleoperate_dataflow.yml")
    print("   Terminal 2: python -m operating_platform.inference.cli_dorobot --policy.path=/path/to/model")
    print("=" * 60)
    
    run_inference(parsed_args)


def run_inference(args):
    """Run inference using the parsed arguments."""
    print("Starting DoRobot daemon...")
    
    try:
        # Create robot config based on type
        if args['robot']['type'] == 'so101':
            robot_config = SO101RobotConfig()
        else:
            raise ValueError(f"Unsupported robot type: {args['robot']['type']}")
        
        # Create daemon
        daemon = Daemon(fps=args['fps'])
        daemon.start(robot_config)
        print("✅ Daemon started successfully")
        
        # Load policy
        policy = DoRobotPolicy(args['policy']['path'], device=args['policy']['device'])
        print("✅ Policy loaded successfully")
        
        print("Starting inference loop...")
        print("Press Ctrl+C to stop")
        
        # Run inference loop
        start_time = time.time()
        step_count = 0
        
        while time.time() - start_time < args['duration']:
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
                
                # Display data if requested
                if args['display_data'] and step_count % 5 == 0:
                    print(f"Step {step_count}:")
                    print(f"  State shape: {observation['state'].shape}")
                    print(f"  Images: {list(observation['images'].keys())}")
                    print(f"  Action: {action}")
                
                # Print progress
                if step_count % 5 == 0:
                    elapsed = time.time() - start_time
                    print(f"Step {step_count}: Action = {action}, Time = {elapsed:.1f}s")
                
                # Timing control
                step_elapsed = time.time() - step_start
                sleep_time = max(0, 1.0 / args['fps'] - step_elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                if step_count % 10 == 0:
                    print(f"Error in step {step_count}: {e}")
                time.sleep(1.0 / args['fps'])
                
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


