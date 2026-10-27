import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from std_msgs.msg import Float64
import math
import time

class OdomPositionSubscriber(Node):
    def __init__(self):
        super().__init__('odom_position_subscriber')

        # Inizializza la variabile per la posizione precedente
        self.previous_position = None

        # Crea il publisher per pubblicare la distanza
        self.distance_publisher = self.create_publisher(Float64, '/distance_travelled', 10)

        # Crea un subscriber per ottenere la posizione
        self.subscription = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        # Variabili per il log
        self.publish_count = 0
        self.last_log_time = time.time()
        # Distanza
        self.distance = 0

    def odom_callback(self, msg):
        # Ottieni la posizione
        current_position = msg.pose.pose.position

        # Numero di chiamate tra un publish e il successivo
        self.publish_count += 1

        # Calcola la distanza percorsa sommando le distanze
        if self.previous_position is not None:
            self.distance += self.calculate_distance(self.previous_position, current_position)
        else:
            self.distance = 0.0

        # Ottieni il tempo attuale
        current_time = time.time()
        if current_time - self.last_log_time >= 0.95: # Tolleranza di 0.05 per sicurezza
            # Pubblica la distanza
            self.distance_publisher.publish(Float64(data=self.distance))
            # Log 
            self.get_logger().info(
                f'Distance travelled: {self.distance:.2f} meters | '
                f'Publishes in last second: {self.publish_count}'
            )
            # Reset counter e timestamp
            self.publish_count = 0
            self.last_log_time = current_time
            # Reset distanza
            self.distance = 0.0

        # Salvataggio della posizione precedente
        self.previous_position = current_position

    def calculate_distance(self, pos1, pos2):
        # Calcola la distanza Euclidea tra due punti
        return math.sqrt(
            (pos2.x - pos1.x) ** 2 + 
            (pos2.y - pos1.y) ** 2
        )

def main(args=None):
    rclpy.init(args=args)
    node = OdomPositionSubscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
