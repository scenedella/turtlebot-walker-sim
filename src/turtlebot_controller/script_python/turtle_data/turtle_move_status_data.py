import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from rclpy.time import Time

class MoveStatusSubscriber(Node):
    def __init__(self):
        super().__init__('move_status_subscriber')
        self.subscription = self.create_subscription(
            Bool,
            '/move_status',
            self.listener_callback,
            10
        )
        self.start_time = None  # Time when the robot starts

    def listener_callback(self, msg):
        current_time = self.get_clock().now()

        if msg.data:  # True: Robot started
            self.get_logger().info("-----------------------------------------------------------")
            self.get_logger().info("Robot started.")
            self.start_time = current_time  # Record the start time

        else:  # False: Robot arrived
            if self.start_time:
                elapsed_time = current_time - self.start_time
                elapsed_seconds = elapsed_time.nanoseconds / 1e9  # Convert nanoseconds to seconds
                self.get_logger().info(f"Robot arrived. Time taken: {elapsed_seconds:.2f} seconds.")
                self.get_logger().info("-----------------------------------------------------------")
                self.start_time = None  # Reset the start time for the next journey
            else:
                self.get_logger().warn("Robot arrival detected without a start signal.")

def main(args=None):
    rclpy.init(args=args)
    move_status_subscriber = MoveStatusSubscriber()

    try:
        rclpy.spin(move_status_subscriber)
    except KeyboardInterrupt:
        pass
    finally:
        move_status_subscriber.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
