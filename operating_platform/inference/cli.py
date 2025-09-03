#!/usr/bin/env python3
"""
DoRobot Inference Command Line Interface

This script provides a command-line interface similar to LeRobot's record command
for running inference with DoRobot trained models.
"""

import argparse
import sys
import os
import time
import numpy as np
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from operating_platform.inference import DoRobotPolicy, InferenceRunner
from operating_platform.robot.robots.configs import SO101RobotConfig
from operating_platform.robot.robots.utils import make_robot_from_config


def main():
    """Main function for DoRobot inference CLI."""
    parser = argparse.ArgumentParser(
        description="DoRobot Inference - Run inference with trained models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test mode (no robot connection)
  python -m operating_platform.inference.cli --test_mode --policy.path=/path/to/model

  # Real robot inference
  python -m operating_platform.inference.cli --robot.type=so101 --robot.port=/dev/ttyACM1 --policy.path=/path/to/model

  # Inference with custom camera settings
  python -m operating_platform.inference.cli --robot.type=so101 --robot.cameras="{image_top: {width: 320, height: 240, fps: 15}}" --policy.path=/path/to/model
        """
    )
    
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
        help="Device to run inference on (npu, cuda, cpu). If None, auto-select."
    )
    
    # Robot arguments
    parser.add_argument(
        "--robot.type",
        type=str,
        default="so101",
        help="Robot type (so101)"
    )
    parser.add_argument(
        "--robot.port",
        type=str,
        default="/dev/ttyACM1",
        help="Robot serial port"
    )
    parser.add_argument(
        "--robot.id",
        type=str,
        default="dorobot_arm",
        help="Robot ID"
    )
    parser.add_argument(
        "--robot.cameras",
        type=str,
        default=None,
        help="Camera configuration in YAML format"
    )
    
    # Inference arguments
    parser.add_argument(
        "--inference.fps",
        type=int,
        default=15,
        help="Target inference frequency"
    )
    parser.add_argument(
        "--inference.duration",
        type=int,
        default=0,
        help="Duration to run inference in seconds (0 for infinite)"
    )
    
    # Test mode
    parser.add_argument(
        "--test_mode",
        action="store_true",
        help="Run in test mode without connecting to robot"
    )
    
    # Display arguments
    parser.add_argument(
        "--display_data",
        action="store_true",
        default=False,
        help="Display camera data during inference"
    )
    
    args = parser.parse_args()
    
    # Print configuration
    print("=" * 60)
    print("DoRobot Inference")
    print("=" * 60)
    print(f"Policy path: {getattr(args, 'policy.path', 'Not set')}")
    print(f"Policy device: {getattr(args, 'policy.device', 'auto-select')}")
    print(f"Robot type: {getattr(args, 'robot.type', 'Not set')}")
    print(f"Robot port: {getattr(args, 'robot.port', 'Not set')}")
    print(f"Robot ID: {getattr(args, 'robot.id', 'Not set')}")
    print(f"Inference FPS: {getattr(args, 'inference.fps', 'Not set')}")
    print(f"Duration: {getattr(args, 'inference.duration', 'Not set')} seconds")
    print(f"Test mode: {args.test_mode}")
    print(f"Display data: {args.display_data}")
    print("=" * 60)
    
    if args.test_mode:
        run_test_mode(args)
    else:
        run_real_inference(args)


def run_test_mode(args):
    """Run inference in test mode."""
    print("Running in test mode...")
    
    try:
        # Load policy
        policy_path = getattr(args, 'policy.path', '/data/dora/act_dorobot/pretrained_model')
        policy_device = getattr(args, 'policy.device', None)
        policy = DoRobotPolicy(policy_path, device=policy_device)
        print("✅ Policy loaded successfully")
        
        # Test with dummy data
        dummy_observation = {
            'images': {
                'image_top': np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8),
                'image_wrist': np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
            },
            'state': np.random.randn(6).astype(np.float32)
        }
        
        print("Testing inference with dummy data...")
        start_time = time.time()
        
        fps = getattr(args, 'inference.fps', 15)
        duration = getattr(args, 'inference.duration', 0)
        num_steps = 10 if duration == 0 else duration * fps
        for i in range(int(num_steps)):
            action = policy.get_action(dummy_observation)
            elapsed = time.time() - start_time
            
            if i % 5 == 0:  # Print every 5th iteration
                print(f"  Step {i}: Action = {action}, Time = {elapsed:.3f}s")
            
            # Simulate timing
            time.sleep(1.0 / fps)
        
        print("✅ Test completed successfully")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


def run_real_inference(args):
    """Run inference with real robot."""
    print("Connecting to robot...")
    
    try:
        # Create robot configuration
        robot_config = create_robot_config(args)
        
        # Get parameters
        policy_path = getattr(args, 'policy.path', '/data/dora/act_dorobot/pretrained_model')
        policy_device = getattr(args, 'policy.device', None)
        fps = getattr(args, 'inference.fps', 15)
        
        # Create inference runner
        runner = InferenceRunner(
            model_path=policy_path,
            robot_config=robot_config,
            device=policy_device,
            fps=fps
        )
        
        print("✅ Robot connected successfully")
        print("Starting inference loop...")
        print("Press Ctrl+C to stop")
        
        # Run inference
        duration = getattr(args, 'inference.duration', 0)
        if duration > 0:
            # Run for specified duration
            start_time = time.time()
            while time.time() - start_time < duration:
                result = runner.run_single_step()
                if args.display_data:
                    print(f"Action: {result['action']}, Time: {result['inference_time']:.3f}s")
        else:
            # Run indefinitely
            runner.start()
            
    except KeyboardInterrupt:
        print("\nInference stopped by user")
    except Exception as e:
        print(f"❌ Error during inference: {e}")
        import traceback
        traceback.print_exc()


def create_robot_config(args):
    """Create robot configuration from arguments."""
    # Parse camera configuration if provided
    cameras_config = None
    cameras_arg = getattr(args, 'robot.cameras', None)
    if cameras_arg:
        try:
            import yaml
            cameras_config = yaml.safe_load(cameras_arg)
        except Exception as e:
            print(f"Warning: Could not parse camera config: {e}")
    
    # Create robot config
    robot_config = SO101RobotConfig()
    
    # Update camera settings if provided
    if cameras_config:
        for cam_name, cam_config in cameras_config.items():
            if cam_name in robot_config.cameras:
                for key, value in cam_config.items():
                    if hasattr(robot_config.cameras[cam_name], key):
                        setattr(robot_config.cameras[cam_name], key, value)
    
    return robot_config


if __name__ == "__main__":
    main()
