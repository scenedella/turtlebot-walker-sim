#!/usr/bin/env python3
"""
Gemello digitale (versione semplice): il TurtleBot3 reale muove il robot in Gazebo.

Legge /odom del robot reale (ROS_DOMAIN_ID=30, CycloneDDS) e sposta il modello
nella simulazione Gazebo Classic con il comando `gz model`. Cosi' non serve
mettere in comunicazione il dominio 30 (robot reale) con il 77 (simulazione).

Prima di avviare il bringup sul robot reale, metti il robot nel punto della casa
che corrisponde a (X0, Y0) della mappa, orientato come YAW0_DEG: l'odometria
parte da zero all'avvio del bringup.
"""
import math
import shutil
import subprocess

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from nav_msgs.msg import Odometry

# --- Parametri da adattare ---------------------------------------------------
MODEL_NAME = "turtlebot3_burger"      # nome del robot nel pannello "Models" di Gazebo
X0, Y0 = 4.4, 3.3          # punto di partenza nella mappa (m)
YAW0_DEG = 0.0             # orientamento iniziale nella mappa (gradi)
Z = 2.17                   # quota del pavimento rialzato in Gazebo (m)
RATE_HZ = 5.0              # aggiornamenti al secondo verso Gazebo
MIN_DIST = 0.01            # m: sotto questo spostamento non aggiorna
MIN_ANG = math.radians(1.0)
# -----------------------------------------------------------------------------


def yaw_da_quaternione(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                      1.0 - 2.0 * (q.y * q.y + q.z * q.z))


class GemelloDigitale(Node):
    def __init__(self):
        super().__init__("gemello_digitale")
        self.yaw0 = math.radians(YAW0_DEG)
        self.ultima_odom = None
        self.ultima_inviata = None
        self.errore_segnalato = False

        self.create_subscription(Odometry, "/odom", self.su_odom,
                                 qos_profile_sensor_data)
        self.create_timer(1.0 / RATE_HZ, self.aggiorna_gazebo)
        self.create_timer(5.0, self.controlla_odom)
        self.get_logger().info(
            f"In attesa di /odom dal robot reale. Modello Gazebo: '{MODEL_NAME}', "
            f"partenza ({X0:.2f}, {Y0:.2f}) a {YAW0_DEG:.0f} gradi.")

    def su_odom(self, msg):
        if self.ultima_odom is None:
            self.get_logger().info("Ricevuta la prima /odom: il gemello e' attivo.")
        self.ultima_odom = msg

    def controlla_odom(self):
        if self.ultima_odom is None:
            self.get_logger().warn(
                "Nessuna /odom ancora: controlla bringup, ROS_DOMAIN_ID=30 e Cyclone.")

    def aggiorna_gazebo(self):
        if self.ultima_odom is None:
            return
        p = self.ultima_odom.pose.pose.position
        yaw = yaw_da_quaternione(self.ultima_odom.pose.pose.orientation)

        # Dall'odometria (parte da 0,0) alle coordinate della mappa
        c, s = math.cos(self.yaw0), math.sin(self.yaw0)
        xs = X0 + c * p.x - s * p.y
        ys = Y0 + s * p.x + c * p.y
        yaws = math.atan2(math.sin(self.yaw0 + yaw), math.cos(self.yaw0 + yaw))

        if self.ultima_inviata is not None:
            px, py, pyaw = self.ultima_inviata
            dang = abs(math.atan2(math.sin(yaws - pyaw), math.cos(yaws - pyaw)))
            if math.hypot(xs - px, ys - py) < MIN_DIST and dang < MIN_ANG:
                return

        comando = ["gz", "model", "-w", "casa", "-m", MODEL_NAME,
                   "-x", f"{xs:.3f}", "-y", f"{ys:.3f}", "-z", f"{Z:.3f}",
                   "-R", "0", "-P", "0", "-Y", f"{yaws:.4f}"]
        try:
            esito = subprocess.run(comando, capture_output=True, text=True, timeout=2.0)
        except subprocess.TimeoutExpired:
            self.get_logger().warn("Gazebo non risponde (gz model in timeout).")
            return

        if esito.returncode != 0 or esito.stderr.strip():
            if not self.errore_segnalato:
                self.get_logger().error(
                    "gz model ha dato errore (Gazebo e' aperto? il nome del modello "
                    f"e' giusto?): {esito.stderr.strip()}")
                self.errore_segnalato = True
            return

        self.errore_segnalato = False
        self.ultima_inviata = (xs, ys, yaws)


def main():
    if shutil.which("gz") is None:
        print("Comando 'gz' non trovato: fai prima 'source /usr/share/gazebo/setup.sh'.")
        return
    rclpy.init()
    nodo = GemelloDigitale()
    try:
        rclpy.spin(nodo)
    except KeyboardInterrupt:
        pass
    finally:
        nodo.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()

