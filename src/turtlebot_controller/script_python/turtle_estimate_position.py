import subprocess

def publish_initial_pose():
    command = r'''ros2 topic pub -1 /initialpose geometry_msgs/msg/PoseWithCovarianceStamped "
header:
  stamp:
    sec: $(date +%s)
    nanosec: 0
  frame_id: 'map'
pose:
  pose:
    position:
      x: -2.0
      y: -0.5
      z: 0.0
    orientation:
      x: 0.0
      y: 0.0
      z: 0.0
      w: 1.0
  covariance: [0.25, 0.0, 0.0, 0.0, 0.0, 0.0,
               0.0, 0.25, 0.0, 0.0, 0.0, 0.0,
               0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
               0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
               0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
               0.0, 0.0, 0.0, 0.0, 0.0, 0.1]"
'''
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("Initial pose published successfully.")
            print("Output:", result.stdout)
        else:
            print("Failed to publish initial pose.")
            print("Error:", result.stderr)
    except Exception as e:
        print(f"Error running command: {e}")

def main():
  publish_initial_pose()