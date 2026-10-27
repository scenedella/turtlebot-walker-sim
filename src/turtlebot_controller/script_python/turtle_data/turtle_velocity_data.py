#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class CmdVelSubscriber(Node):
    def __init__(self):
        super().__init__('cmd_vel_subscriber')
        
        # Create a subscriber to the 'cmd_vel' topic
        self.subscription = self.create_subscription(
            Twist,                # Message type
            'cmd_vel',            # Topic name
            self.cmd_vel_callback,# Callback function
            10                    # QoS profile for reliability
        )
        self.subscription  # Prevents unused variable warning

    def cmd_vel_callback(self, msg):
        # Print the incoming message with linear and angular velocities
        self.get_logger().info(
            f'Received cmd_vel data - Linear: x={msg.linear.x}, y={msg.linear.y}, z={msg.linear.z} | '
            f'Angular: x={msg.angular.x}, y={msg.angular.y}, z={msg.angular.z}'
        )

def main(args=None):
    rclpy.init(args=args)
    node = CmdVelSubscriber()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    
    # Shutdown the node
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
