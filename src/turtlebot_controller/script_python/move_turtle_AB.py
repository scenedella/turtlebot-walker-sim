import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from std_msgs.msg import Float32, Bool  # Per pubblicare il tempo di percorrenza
import time
from lifecycle_msgs.srv import GetState
# File esterni 
from script_python.turtle_estimate_position import publish_initial_pose
from script_python.patient_button_control import button

class GoalNavigation(Node): 
    def __init__(self):
        super().__init__('goal_navigation')
        
        # Crea un ActionClient per inviare la destinazione
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        # Crea un publisher per pubblicare lo stato di avanzamento
        self.move_status_publisher = self.create_publisher(Bool, '/move_status', 10)
        
        # Flag per controllare se stiamo andando alla destinazione o tornando a casa
        self.at_destination = False

        # home 
        self.home_x = -2.0
        self.home_y = -0.5
        self.home_theta = 0.0

    def send_goal(self, x, y, theta):
        # Inizializzazione
        goal_msg = NavigateToPose.Goal() 
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        
        # Imposta la posizione
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.orientation.z = theta  # Orientamento z per semplicità

        self.get_logger().info(f'Valuto posizione richiesta...\n'
                               f'x = {x}\n'
                               f'y = {y}\n'
                               f'theta = {theta}')

        # Invia il goal
        self._action_client.wait_for_server()
        self._send_goal_future = self._action_client.send_goal_async(goal_msg)
        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        
        if not goal_handle.accepted:
            self.get_logger().info('Goal rifiutato')
            return

        # Inizio del tragitto - publish 
        self.get_logger().info('Goal accettato')
        msg = Bool()
        msg.data = True
        self.move_status_publisher.publish(msg)

        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result().result

        if not self.at_destination:

            # Fine del tragitto - publish 
            self.get_logger().info(f'Arrivato alla destinazione!')

            msg = Bool()
            msg.data = False
            self.move_status_publisher.publish(msg)

            # Imposta il flag per indicare che il prossimo obiettivo sarà la casa
            self.at_destination = True
            # Simula il paziente che decide quando dire al robot di tornare a casa
            button(self.at_destination)
            #time.sleep(5)
            # Manda il robot a casa
            self.send_goal(self.home_x, self.home_y, self.home_theta)
        else:
            # Fine del tragitto - publish 
            self.get_logger().info(f'Arrivato a casa!')
            msg = Bool()
            msg.data = False
            self.move_status_publisher.publish(msg)

            rclpy.shutdown()

def wait_for_nav2(timeout=60):
    node = rclpy.create_node("wait_for_nav2_helper")
    client = node.create_client(GetState, "/bt_navigator/get_state")
    start = time.time()
    ready = False
    while time.time() - start < timeout:
        if client.wait_for_service(timeout_sec=1.0):
            future = client.call_async(GetState.Request())
            rclpy.spin_until_future_complete(node, future, timeout_sec=2.0)
            if future.result() is not None and future.result().current_state.label == "active":
                ready = True
                break
        time.sleep(1)
    node.destroy_node()
    return ready

def main():
    rclpy.init()

    # Metodo richiamato dal file turtle_estimate_position.py 
    # Stima la posizione iniziale su Rviz per evitare di farlo manualmente
    publish_initial_pose()
    
    wait_for_nav2()

    navigator = GoalNavigation()

    # Imposta le coordinate della destinazione
    x_goal = 3.5
    y_goal = 2.5
    theta_goal = 0.0

    navigator.send_goal(x_goal, y_goal, theta_goal)
    rclpy.spin(navigator)

if __name__ == '__main__':
    main()
