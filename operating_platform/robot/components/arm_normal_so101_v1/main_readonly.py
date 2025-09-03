"""TODO: Add docstring."""

import os
import time

import numpy as np
import pyarrow as pa
import draccus
from dora import Node
from pathlib import Path

from motors.feetech import FeetechMotorsBus, OperatingMode
from motors import Motor, MotorCalibration, MotorNormMode


GET_DEVICE_FROM = os.getenv("GET_DEVICE_FROM", "PORT") # SN or INDEX
PORT = os.getenv("PORT")
ARM_NAME = os.getenv("ARM_NAME", "SO101-Arm")
CALIBRATION_DIR = os.getenv("CALIBRATION_DIR", "./.calibration/")
USE_DEGRESS = os.getenv("USE_DEGRESS", "True")
ARM_ROLE = os.getenv("ARM_ROLE", "follower")
READ_ONLY = os.getenv("READ_ONLY", "False")


def env_to_bool(env_value: str, default: bool = True) -> bool:
    """将环境变量字符串转换为布尔值"""
    if env_value is None:
        return default
    
    true_values = {'True', 'true', '1', 'yes', 'on', 't', 'y'}
    false_values = {'False', 'false', '0', 'no', 'off', 'f', 'n'}
    
    value_lower = env_value.strip().lower()
    
    if value_lower in true_values:
        return True
    elif value_lower in false_values:
        return False
    else:
        raise ValueError(f"无效的布尔值: {env_value}")
    
def configure_follower(bus: FeetechMotorsBus) -> None:
    with bus.torque_disabled():
        bus.configure_motors()
        for motor in bus.motors:
            bus.write("Operating_Mode", motor, OperatingMode.POSITION.value)
            # Set P_Coefficient to lower value to avoid shakiness (Default is 32)
            bus.write("P_Coefficient", motor, 16)
            # Set I_Coefficient and D_Coefficient to default value 0 and 32
            bus.write("I_Coefficient", motor, 0)
            bus.write("D_Coefficient", motor, 32)

def configure_leader(bus: FeetechMotorsBus) -> None:
    bus.disable_torque()
    bus.configure_motors()
    for motor in bus.motors:
        bus.write("Operating_Mode", motor, OperatingMode.POSITION.value)


def main():
    node = Node()

    use_degrees = env_to_bool(USE_DEGRESS)
    read_only = env_to_bool(READ_ONLY)
    calibration_dir = Path(CALIBRATION_DIR).resolve()
    calibration_fpath = calibration_dir / f"{ARM_NAME}.json"
    name = ARM_NAME

    try:
        with open(calibration_fpath) as f, draccus.config_type("json"):
            arm_calibration = draccus.load(dict[str, MotorCalibration], f)
    except FileNotFoundError:
        raise FileNotFoundError(f"校准文件路径不存在: {calibration_fpath}")
    except IsADirectoryError:
        raise ValueError(f"路径是目录而不是文件: {calibration_fpath}")

    norm_mode_body = MotorNormMode.DEGREES if use_degrees else MotorNormMode.RANGE_M100_100

    arm_bus = FeetechMotorsBus(
        port=PORT,
        motors={
            "shoulder_pan": Motor(1, "sts3215", norm_mode_body),
            "shoulder_lift": Motor(2, "sts3215", norm_mode_body),
            "elbow_flex": Motor(3, "sts3215", norm_mode_body),
            "wrist_flex": Motor(4, "sts3215", norm_mode_body),
            "wrist_roll": Motor(5, "sts3215", norm_mode_body),
            "gripper": Motor(6, "sts3215", MotorNormMode.RANGE_0_100),
        },
        calibration=arm_calibration,
    )

    arm_bus.connect()

    if ARM_ROLE == "follower":
        configure_follower(arm_bus)
    elif ARM_ROLE == "leader":
        configure_leader(arm_bus)

    # Define safe initial position (contracted state)
    safe_initial_position = {
        "shoulder_pan": 0.0,      # Center position
        "shoulder_lift": 30.0,    # Elevated position (safe height)
        "elbow_flex": 20.0,       # Moderate bend
        "wrist_flex": 1.0,        # Slight bend
        "wrist_roll": 0.0,        # No roll
        "gripper": 1.5,           # Partially closed
    }

    # Move to safe initial position on startup (only if not in read-only mode)
    if not read_only:
        print("🔄 Moving to safe initial position...")
        try:
            arm_bus.sync_write("Goal_Position", safe_initial_position)
            print(f"✅ Sent initial position to motors: {safe_initial_position}")
            
            # Wait for movement to complete
            time.sleep(3.0)
            print("✅ Initial position reached")
        except Exception as e:
            print(f"⚠️ Warning: Could not set initial position: {e}")
    else:
        print("📖 Read-only mode - not moving to initial position")

    for event in node:
        if event["type"] == "INPUT":
            if event["id"] == "action_joint" and not read_only:
                position = event["value"].to_numpy()
                print(f"🤖 Received action_joint: {position}")

                # Get current joint positions
                present_pos = arm_bus.sync_read("Present_Position")
                current_positions = [val for _motor, val in present_pos.items()]
                print(f"📊 Current positions: {current_positions}")

                # Define safety limits for each joint to prevent hitting the table
                # These limits are based on typical SO101 robot joint ranges
                safety_limits = {
                    "shoulder_pan": (-1.0, 1.0),      # Pan left/right
                    "shoulder_lift": (20.0, 35.0),    # Lift up/down (keep above table)
                    "elbow_flex": (15.0, 25.0),       # Elbow bend (safe range)
                    "wrist_flex": (0.5, 2.0),         # Wrist bend (safe range)
                    "wrist_roll": (-0.5, 0.5),        # Wrist roll (limited)
                    "gripper": (1.0, 2.0),            # Gripper (keep closed)
                }

                # Calculate new goal positions as relative movements with safety limits
                goal_pos = {}
                for i, (key, motor) in enumerate(arm_bus.motors.items()):
                    if i < len(position):
                        # Calculate target position
                        target_pos = current_positions[i] + position[i]
                        
                        # Apply safety limits
                        min_limit, max_limit = safety_limits[key]
                        safe_target = max(min_limit, min(max_limit, target_pos))
                        
                        goal_pos[key] = safe_target
                        print(f"🎯 {key}: {current_positions[i]} + {position[i]} = {target_pos} -> {safe_target}")
                    else:
                        goal_pos[key] = current_positions[i]

                arm_bus.sync_write("Goal_Position", goal_pos)
                print(f"✅ Sent safe goal positions to motors: {goal_pos}")

            elif event["id"] == "reset" and not read_only:
                # Reset to safe initial position
                print("🔄 Reset command received - moving to safe initial position...")
                try:
                    arm_bus.sync_write("Goal_Position", safe_initial_position)
                    print(f"✅ Reset to initial position: {safe_initial_position}")
                except Exception as e:
                    print(f"❌ Error during reset: {e}")

            elif event["id"] == "get_joint":
                joint_value = []
                present_pos = arm_bus.sync_read("Present_Position")
                joint_value = [val for _motor, val in present_pos.items()]

                node.send_output("joint", pa.array(joint_value, type=pa.float32()))

        elif event["type"] == "STOP":
            break


if __name__ == "__main__":
    main()
