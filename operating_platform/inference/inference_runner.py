"""
DoRobot Inference Runner for robot control.
"""

import time
import numpy as np
from typing import Dict, Any, Optional
from pathlib import Path

from .policy import DoRobotPolicy
from operating_platform.robot.robots.utils import make_robot_from_config
from operating_platform.robot.robots.configs import SO101RobotConfig


class InferenceRunner:
    """Runs inference for DoRobot robot control."""
    
    def __init__(self, model_path: str, robot_config: Optional[SO101RobotConfig] = None, 
                 device: str = None, fps: int = 15):
        """
        Initialize the inference runner.
        
        Args:
            model_path: Path to the trained model directory
            robot_config: Robot configuration (if None, uses default SO101 config)
            device: Device to run inference on ('npu', 'cuda', 'cpu'). If None, auto-select.
            fps: Target inference frequency
        """
        self.model_path = model_path
        self.fps = fps
        self.dt = 1.0 / fps
        
        # Auto-select device if not specified
        if device is None:
            from .utils import auto_select_device
            device = auto_select_device()
        
        self.device = device
        
        # Initialize policy
        self.policy = DoRobotPolicy(model_path, device)
        
        # Initialize robot
        if robot_config is None:
            robot_config = SO101RobotConfig()
        self.robot = make_robot_from_config(robot_config)
        
        # Connect to robot
        self.robot.connect()
        
        # Running state
        self.running = False
        
    def start(self):
        """Start inference loop."""
        self.running = True
        print(f"Starting inference at {self.fps} FPS...")
        
        try:
            while self.running:
                start_time = time.perf_counter()
                
                # Get observation from robot
                observation = self._get_observation()
                
                # Run inference
                action = self.policy.get_action(observation)
                
                # Apply action to robot
                self._apply_action(action)
                
                # Timing control
                elapsed = time.perf_counter() - start_time
                sleep_time = max(0, self.dt - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
        except KeyboardInterrupt:
            print("Inference stopped by user")
        except Exception as e:
            print(f"Error during inference: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop inference loop."""
        self.running = False
        if hasattr(self.robot, 'disconnect'):
            self.robot.disconnect()
        print("Inference stopped")
    
    def _get_observation(self) -> Dict[str, Any]:
        """Get observation from robot."""
        observation = {}
        
        # Get images from cameras
        if hasattr(self.robot, 'cameras') and self.robot.cameras:
            images = {}
            for cam_name, camera in self.robot.cameras.items():
                if hasattr(camera, 'read'):
                    try:
                        image = camera.read()
                        images[cam_name] = image
                    except Exception as e:
                        print(f"Error reading camera {cam_name}: {e}")
                        # Use zero image as fallback
                        images[cam_name] = np.zeros((240, 320, 3), dtype=np.uint8)
            observation['images'] = images
        
        # Get state from robot
        if hasattr(self.robot, 'get_state'):
            try:
                state = self.robot.get_state()
                observation['state'] = state
            except Exception as e:
                print(f"Error getting state: {e}")
                # Use zero state as fallback
                observation['state'] = np.zeros(6, dtype=np.float32)
        else:
            # Try to get state from different methods
            try:
                if hasattr(self.robot, 'main_leader'):
                    # Get joint angles from leader arm
                    joint_angles = self.robot.main_leader.get_joint_angles()
                    observation['state'] = np.array(joint_angles, dtype=np.float32)
                else:
                    # Use zero state as fallback
                    observation['state'] = np.zeros(6, dtype=np.float32)
            except Exception as e:
                print(f"Error getting joint angles: {e}")
                # Use zero state as fallback
                observation['state'] = np.zeros(6, dtype=np.float32)
        
        return observation
    
    def _apply_action(self, action: np.ndarray):
        """Apply action to robot."""
        try:
            if hasattr(self.robot, 'apply_action'):
                self.robot.apply_action(action)
            elif hasattr(self.robot, 'main_leader'):
                # Apply action to leader arm
                self.robot.main_leader.set_joint_angles(action)
            else:
                print("Warning: Robot does not have apply_action or set_joint_angles method")
        except Exception as e:
            print(f"Error applying action: {e}")
    
    def run_single_step(self) -> Dict[str, Any]:
        """
        Run a single inference step.
        
        Returns:
            Dictionary with observation, action, and timing info
        """
        start_time = time.perf_counter()
        
        # Get observation
        observation = self._get_observation()
        
        # Run inference
        action = self.policy.get_action(observation)
        
        # Apply action
        self._apply_action(action)
        
        elapsed = time.perf_counter() - start_time
        
        return {
            'observation': observation,
            'action': action,
            'inference_time': elapsed
        }


def run_inference(model_path: str, robot_config: Optional[SO101RobotConfig] = None,
                 device: str = "npu", fps: int = 15):
    """
    Convenience function to run inference.
    
    Args:
        model_path: Path to the trained model directory
        robot_config: Robot configuration
        device: Device to run inference on
        fps: Target inference frequency
    """
    runner = InferenceRunner(model_path, robot_config, device, fps)
    runner.start()
