#!/usr/bin/env python3
"""
DoRobot Inference Script

This script runs inference using a trained DoRobot model to control the robot.
"""

import argparse
import time
import numpy as np
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from operating_platform.inference import InferenceRunner
from operating_platform.robot.robots.configs import SO101RobotConfig


def main():
    """Main inference function."""
    parser = argparse.ArgumentParser(description="DoRobot Inference")
    parser.add_argument(
        "--model_path", 
        type=str, 
        default="/data/dora/act_dorobot/pretrained_model",
        help="Path to the trained model directory"
    )
    parser.add_argument(
        "--device", 
        type=str, 
        default="cpu",  # Use CPU for now, can be changed to "npu" or "cuda"
        help="Device to run inference on (cpu, npu, cuda)"
    )
    parser.add_argument(
        "--fps", 
        type=int, 
        default=15,
        help="Target inference frequency"
    )
    parser.add_argument(
        "--duration", 
        type=int, 
        default=60,
        help="Duration to run inference in seconds (0 for infinite)"
    )
    parser.add_argument(
        "--test_mode", 
        action="store_true",
        help="Run in test mode without connecting to robot"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("DoRobot Inference")
    print("=" * 60)
    print(f"Model path: {args.model_path}")
    print(f"Device: {args.device}")
    print(f"FPS: {args.fps}")
    print(f"Duration: {args.duration} seconds")
    print(f"Test mode: {args.test_mode}")
    print("=" * 60)
    
    if args.test_mode:
        # Test mode - just test the policy without robot connection
        test_inference_without_robot(args)
    else:
        # Real mode - connect to robot and run inference
        run_inference_with_robot(args)


def test_inference_without_robot(args):
    """Test inference without connecting to robot."""
    print("Running in test mode...")
    
    try:
        from operating_platform.inference.policy import DoRobotPolicy
        
        # Load policy
        policy = DoRobotPolicy(args.model_path, device=args.device)
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
        
        for i in range(10):  # Test 10 iterations
            action = policy.get_action(dummy_observation)
            elapsed = time.time() - start_time
            
            if i % 5 == 0:  # Print every 5th iteration
                print(f"  Step {i}: Action = {action}, Time = {elapsed:.3f}s")
            
            # Simulate timing
            time.sleep(1.0 / args.fps)
        
        print("✅ Test completed successfully")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


def run_inference_with_robot(args):
    """Run inference with robot connection."""
    print("Connecting to robot...")
    
    try:
        # Create robot configuration
        robot_config = SO101RobotConfig()
        
        # Create inference runner
        runner = InferenceRunner(
            model_path=args.model_path,
            robot_config=robot_config,
            device=args.device,
            fps=args.fps
        )
        
        print("✅ Robot connected successfully")
        print("Starting inference loop...")
        print("Press Ctrl+C to stop")
        
        # Run inference
        if args.duration > 0:
            # Run for specified duration
            start_time = time.time()
            while time.time() - start_time < args.duration:
                result = runner.run_single_step()
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


if __name__ == "__main__":
    main()


