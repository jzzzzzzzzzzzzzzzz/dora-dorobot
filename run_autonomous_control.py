#!/usr/bin/env python3
"""
DoRobot Autonomous Control Script
This script runs the autonomous dataflow in dr-robot-so101 environment.
The inference is handled by the inference_action node within the dataflow.
"""

import subprocess
import time
import signal
import sys
import os
from pathlib import Path

def run_dora_dataflow():
    """Run the Dora dataflow in dr-robot-so101 environment."""
    print("Starting DoRobot Autonomous Dataflow...")
    print("This will run the complete autonomous control system")
    print("including inference within the dataflow.")
    
    # Activate dr-robot-so101 environment and run dora
    cmd = [
        "conda", "run", "-n", "dr-robot-so101",
        "dora", "run", 
        "/data/dora/DoRobot-Preview/operating_platform/robot/robots/so101_v1/dora_autonomous_dataflow.yml"
    ]
    
    try:
        process = subprocess.Popen(cmd)
        print("Autonomous dataflow started successfully!")
        return process
    except Exception as e:
        print(f"Error starting autonomous dataflow: {e}")
        return None

def main():
    """Main function to run autonomous control."""
    print("=" * 60)
    print("DoRobot Autonomous Control")
    print("=" * 60)
    print("This script will start the autonomous dataflow which includes:")
    print("1. Camera capture (top and wrist)")
    print("2. Joint state reading")
    print("3. Inference model (within dataflow)")
    print("4. Action execution on follower arm")
    print("=" * 60)
    
    dora_process = None
    
    try:
        # Start autonomous dataflow
        dora_process = run_dora_dataflow()
        if dora_process is None:
            print("Failed to start autonomous dataflow")
            return
        
        print("Autonomous control system is running!")
        print("The robot should now be performing autonomous actions.")
        print("Press Ctrl+C to stop")
        
        # Wait for the process to finish
        dora_process.wait()
            
    except KeyboardInterrupt:
        print("\nStopping autonomous control...")
    except Exception as e:
        print(f"Error during execution: {e}")
    finally:
        # Clean up process
        if dora_process:
            print("Terminating autonomous dataflow...")
            dora_process.terminate()
            dora_process.wait()
        
        print("Autonomous control stopped")

if __name__ == "__main__":
    main()
