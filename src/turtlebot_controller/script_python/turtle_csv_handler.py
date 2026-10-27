import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64, Float32, Bool
from nav_msgs.msg import Odometry
from datetime import datetime
import pandas as pd
import math
import time
import os

class DataLoggerNode(Node):
    def __init__(self):
        super().__init__('data_logger_node')
        
        # Inizializza i subscriber
        self.cmd_vel_subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )
        
        self.odom_subscription = self.create_subscription(
            Odometry, 
            '/odom',
            self.odom_callback,
            10
        )

        self.distance_subscription = self.create_subscription(
            Float64, 
            '/distance_travelled',
            self.distance_callback,
            10
        )

        self.move_status_subscription = self.create_subscription(
            Bool, 
            '/move_status',
            self.move_status_callback,
            10
        )

        # Variabili per memorizzare i dati
        self.vel_lin = 0.0
        self.vel_ang = 0.0
        self.pos_x = 0.0
        self.pos_y = 0.0
        self.theta = 0.0
        self.distance = 0.0

        # Se il robot si sta muovendo o no
        self.move_status = None
        
        # Lista per memorizzare i dati (sarà usata per il DataFrame: pandas)
        self.data = []

        # flag, per sapere se il tragitto è verso l'obiettivo o verso casa
        self.back_home = False

        # Imposta un timer per il logging periodico
        self.create_timer(1.0, self.check_data)  # Esegue check_data ogni 1 secondo
    
    def cmd_vel_callback(self, msg): 
        """Callback per il topic /cmd_vel"""
        self.vel_lin = msg.linear.x
        self.vel_ang = msg.angular.z

    def odom_callback(self, msg):
        """Callback per il topic /odom"""
        self.pos_x = msg.pose.pose.position.x
        self.pos_y = msg.pose.pose.position.y
        orientation = msg.pose.pose.orientation
        # Converti il quaternione in angolo theta (rotazione attorno all'asse Z)
        self.theta = 2 * math.atan2(orientation.z, orientation.w)

    def distance_callback(self, msg):
        """Callback per il topic /distance"""
        self.distance = msg.data

    def move_status_callback(self, msg):
        """Callback per il topic /move_status"""
        self.move_status = msg.data

    def get_actual_time_format(self):
        current_time = self.get_clock().now().to_msg()
        # Converti l'oggetto tempo ROS2 in un timestamp in secondi
        current_time_sec = current_time.sec + current_time.nanosec * 1e-9

        # Converti il timestamp in un oggetto datetime
        time_only = datetime.fromtimestamp(current_time_sec)

        return time_only.strftime("%H:%M:%S")

    def check_data(self):
        """Log dei dati nel DataFrame"""

        # Visualizza man mano i dati
        #self.get_logger().info(f"Dati: {self.vel_lin}, {self.vel_ang} , {self.pos_x}, {self.pos_y}, {self.theta}, {self.distance}")

        if self.move_status:
            # Formatta solo l'ora, minuto e secondo
            formatted_time = self.get_actual_time_format()

            self.data.append([
                formatted_time,
                self.pos_x, self.pos_y, self.theta, 
                self.distance, self.vel_lin, self.vel_ang
            ])

            self.get_logger().info("Dati registrati.")
        elif self.move_status is not None: 
            self.save_to_csv() # Salva i dati nel csv
            # Va nella direzione opposta
            self.back_home = not self.back_home
            self.move_status = None
            self.data = []
            
    def save_to_csv(self):
        """Salva i dati nel file CSV usando pandas con nome basato sulla data e numero progressivo a tre cifre."""
        # Ottieni la data corrente nel formato YYYYMMDD
        date_str = datetime.now().strftime('%Y%m%d')
        # Percorso della cartella dove salvare i file
        ws = os.environ.get('TURTLEBOT_WS')
        if not ws:
            try:
                from ament_index_python.packages import get_package_prefix
                # <ws>/install/turtlebot_controller -> <ws>
                ws = os.path.dirname(os.path.dirname(get_package_prefix('turtlebot_controller')))
            except Exception:
                ws = os.getcwd()
        folder_path = os.path.join(ws, 'src', 'turtlebot_controller', 'robot_data_csv')
        os.makedirs(folder_path, exist_ok=True)
        
        # Trova l'ultimo numero di file con quel prefisso (YYYYMMDD) nella cartella
        existing_files = [f for f in os.listdir(folder_path) if f.startswith(date_str)]
        file_number = str(len(existing_files) // 2 + 1).zfill(3)

        # Crea il nome del file usando il numero progressivo a tre cifre
        file_name = f"{date_str}_{file_number}_{'home' if self.back_home else 'goal'}.csv"
        file_path = os.path.join(folder_path, file_name)
        
        # Salva il DataFrame nel file CSV
        df = pd.DataFrame(self.data, columns=['time', 'pos_x', 'pos_y', 'theta', 'distance', 'vel_lin', 'vel_ang'])
        df.to_csv(file_path, index=False)
        
        # Log del salvataggio
        self.get_logger().info("-----------------------------------")
        self.get_logger().info(f"Dati salvati in {file_name}.")
        self.get_logger().info("-----------------------------------")

def main(args=None):
    rclpy.init(args=args)
    # Nodo
    data_logger_node = DataLoggerNode()
    # Il nodo continua a runnare
    rclpy.spin(data_logger_node)
    data_logger_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
