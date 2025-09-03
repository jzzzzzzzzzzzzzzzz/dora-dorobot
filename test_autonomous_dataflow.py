#!/usr/bin/env python3
"""
Test script for DoRobot Autonomous Dataflow
"""

import subprocess
import time
import signal
import sys

def main():
    """Test the autonomous dataflow."""
    print("=" * 60)
    print("Testing DoRobot Autonomous Dataflow")
    print("=" * 60)
    
    # Start the autonomous dataflow
    print("Starting autonomous dataflow...")
    try:
        process = subprocess.Popen([
            "dora", "run", 
            "operating_platform/robot/robots/so101_v1/dora_autonomous_dataflow.yml"
        ])
        
        print("Dataflow started successfully!")
        print("Press Ctrl+C to stop")
        
        # Wait for the process
        process.wait()
        
    except KeyboardInterrupt:
        print("\nStopping dataflow...")
        process.terminate()
        process.wait()
        print("Dataflow stopped")
    except Exception as e:
        print(f"Error running dataflow: {e}")
        if 'process' in locals():
            process.terminate()
        sys.exit(1)

if __name__ == "__main__":
    main()


