#!/usr/bin/env python3
"""
DoRobot Simple Inference Script

A simplified version for testing robot inference without complex device handling.
"""

import argparse
import sys
import os
import time
import numpy as np

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from operating_platform.inference import DoRobotPolicy
from operating_platform.robot.robots.configs import SO101RobotConfig
from operating_platform.robot.robots.utils import make_robot_from_config


def main():
    """Main function for simple DoRobot inference."""
    parser = argparse.ArgumentParser(description="DoRobot Simple Inference")
    parser.add_argument(
        "--model_path", 
        type=str, 
        default="/data/dora/act_dorobot/pretrained_model",
        help="Path to the trained model directory"
    )
    parser.add_argument(
        "--device", 
        type=str, 
        default="cpu",  # Use CPU to avoid device mismatch
        help="Device to run inference on (cpu, cuda, npu)"
    )
    parser.add_argument(
        "--fps", 
        type=int, 
        default=10,  # Lower FPS for stability
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
    print("DoRobot Simple Inference")
    print("=" * 60)
    print(f"Model path: {args.model_path}")
    print(f"Device: {args.device}")
    print(f"FPS: {args.fps}")
    print(f"Duration: {args.duration} seconds")
    print("=" * 60)
    
    run_simple_inference(args)


def run_simple_inference(args):
    """Run simple inference with robot."""
    print("Connecting to robot...")
    
    try:
        # Create robot configuration
        robot_config = SO101RobotConfig()
        
        # Create robot
        robot = make_robot_from_config(robot_config)
        robot.connect()
        print("✅ Robot connected successfully")
        
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
                # Get observation
                observation = get_simple_observation(robot)
                
                # Run inference
                action = policy.get_action(observation)
                
                # Apply action
                apply_simple_action(robot, action)
                
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
                if step_count % 10 == 0:  # Only print error every 10 steps
                    print(f"Error in step {step_count}: {e}")
                time.sleep(1.0 / args.fps)
                
    except KeyboardInterrupt:
        print("\nInference stopped by user")
    except Exception as e:
        print(f"❌ Error during inference: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'robot' in locals():
            robot.disconnect()
        print("Inference completed")


def get_simple_observation(robot):
    """Get simple observation from robot."""
    observation = {}
    
    # Get images from cameras
    if hasattr(robot, 'cameras') and robot.cameras:
        images = {}
        for cam_name, camera in robot.cameras.items():
            try:
                # Try different methods to get image
                if hasattr(camera, 'read'):
                    image = camera.read()
                elif hasattr(camera, 'get_image'):
                    image = camera.get_image()
                elif hasattr(camera, 'capture'):
                    image = camera.capture()
                else:
                    # Use zero image as fallback
                    image = np.zeros((240, 320, 3), dtype=np.uint8)
                images[cam_name] = image
            except Exception as e:
                # Use zero image as fallback
                images[cam_name] = np.zeros((240, 320, 3), dtype=np.uint8)
        observation['images'] = images
    
    # Get robot state
    try:
        if hasattr(robot, 'main_leader'):
            # Try different methods to get joint angles
            if hasattr(robot.main_leader, 'get_joint_angles'):
                joint_angles = robot.main_leader.get_joint_angles()
            elif hasattr(robot.main_leader, 'get_angles'):
                joint_angles = robot.main_leader.get_angles()
            elif hasattr(robot.main_leader, 'get_state'):
                joint_angles = robot.main_leader.get_state()
            else:
                joint_angles = [0.0] * 6
            observation['state'] = np.array(joint_angles, dtype=np.float32)
        else:
            # Use zero state as fallback
            observation['state'] = np.zeros(6, dtype=np.float32)
    except Exception as e:
        # Use zero state as fallback
        observation['state'] = np.zeros(6, dtype=np.float32)
    
    return observation


def apply_simple_action(robot, action):
    """Apply simple action to robot."""
    try:
        if hasattr(robot, 'main_leader'):
            # Try different methods to apply action
            if hasattr(robot.main_leader, 'set_joint_angles'):
                robot.main_leader.set_joint_angles(action)
            elif hasattr(robot.main_leader, 'set_angles'):
                robot.main_leader.set_angles(action)
            elif hasattr(robot.main_leader, 'set_target'):
                robot.main_leader.set_target(action)
            # Don't print warning if no method found
        # Don't print warning if no leader arm found
    except Exception as e:
        pass  # Silently ignore errors


if __name__ == "__main__":
    main()
