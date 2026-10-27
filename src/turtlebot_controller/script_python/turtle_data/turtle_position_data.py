import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
import math

class OdomSubscriber(Node):
    def __init__(self):
        super().__init__('odom_subscriber')
        self.subscription = self.create_subscription(
            Odometry,
            '/odom',
            self.listener_callback,
            10
        )

    def listener_callback(self, msg):
        # Extract the current position from the message
        current_position = msg.pose.pose.position
        x = current_position.x
        y = current_position.y

        # Extract orientation (quaternion)
        orientation = msg.pose.pose.orientation
        # Convert quaternion to theta angle (rotation around Z-axis)
        theta_z = 2 * math.atan2(orientation.z, orientation.w)  # In radians

        # Print the position and orientation
        self.get_logger().info(f"Position -> x: {x:.2f}, y: {y:.2f}, θ: {theta_z:.2f} rad")

def main(args=None):
    rclpy.init(args=args)
    odom_subscriber = OdomSubscriber()

    try:
        rclpy.spin(odom_subscriber)
    except KeyboardInterrupt:
        pass
    finally:
        odom_subscriber.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
