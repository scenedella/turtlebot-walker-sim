# libreria Python di ROS 2 per la gestione dei nodi.
import rclpy 
# Node è la classe base per definire un nodo ROS 2
from rclpy.node import Node 
# geometry_msgs.msg è una libreria che invia messaggi su topic
# PoseStamped è un messaggio che contiene informazioni sulla posizione e orientamento (pose) del robot.
from geometry_msgs.msg import PoseStamped 
# NavigateToPose è un’azione fornita dal pacchetto di navigazione nav2_msgs per indicare la navigazione verso una destinazione.
from nav2_msgs.action import NavigateToPose
# ActionClient è la classe per creare un client di azioni, che permette di inviare e monitorare azioni asincrone (come "Naviga verso questa posizione").
from rclpy.action import ActionClient

# definizione del nodo
class GoalNavigation(Node): 
    
    # costruttore
    def __init__(self):
        # nome del nodo
        super().__init__('goal_navigation')
        
        # Crea un ActionClient per inviare la destinazione
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
    
    # metodo: serve per mandare la posizione che vogliamo raggiungere
    def send_goal(self, x, y, theta):

        # Inizializzazione
        # Inizializza l'oggetto
        goal_msg = NavigateToPose.Goal() 
        # Specifichiamo che le coordinate sono assolute rispetto alla mappa.
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        
        # Imposta la posizione
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.orientation.z = theta  # Convertire theta in quaternion sarebbe più preciso
        
        # Invia il goal
        self._action_client.wait_for_server()
        self._send_goal_future = self._action_client.send_goal_async(goal_msg)
        self._send_goal_future.add_done_callback(self.goal_response_callback)
    
    # metodo che parte dopo la risposta del server (riga 42)
    def goal_response_callback(self, future):
        goal_handle = future.result()
        
        if not goal_handle.accepted:
            self.get_logger().info('Goal rifiutato')
            return

        self.get_logger().info('Goal accettato') # riesce a raggiungere la posizione
        self._get_result_future = goal_handle.get_result_async() # fa partire il robot e aspetta il completamento
        self._get_result_future.add_done_callback(self.get_result_callback)

    # metodo che parte dopo la risposta del server (riga 54)
    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info('Arrivato alla destinazione!')
        rclpy.shutdown()


def main():
    rclpy.init()
    
    navigator = GoalNavigation()
    
    # Imposta le coordinate della destinazione (in metri rispetto al frame della mappa)
    x = -2.0 # X della destinazione
    y = 1.0  # Y della destinazione
    theta = 0.0  # Orientamento del robot (in radianti)

    navigator.send_goal(x, y, theta)
    
    # Mantiene il nodo in esecuzione per ascoltare eventuali risposte o aggiornamenti dal server.
    rclpy.spin(navigator) 


if __name__ == '__main__':
    main()
