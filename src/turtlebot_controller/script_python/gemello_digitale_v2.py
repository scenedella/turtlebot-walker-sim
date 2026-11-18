#!/usr/bin/env python3
"""
Gemello digitale: il TurtleBot3 reale muove il robot in Gazebo.

Legge /odom del robot reale (ROS_DOMAIN_ID=30, CycloneDDS) e sposta il modello
nella simulazione Gazebo Classic con il comando `gz model`. Cosi' non serve
mettere in comunicazione il dominio 30 (robot reale) con il 77 (simulazione).

COME FUNZIONA
  L'odometria riparte da (0, 0) a ogni avvio del bringup e non conosce la mappa.
  Lo script la collega alla mappa con una trasformazione T (mappa <- odom), ricavata
  da una "posa di ancoraggio" nota: il punto della casa in cui hai messo il robot
  (X0, Y0) e il suo orientamento (YAW0_DEG). La posa mostrata in Gazebo e'
  T composta con la posa odometrica.

PRIMA DI AVVIARE
  1. Metti il robot reale nel punto (X0, Y0) della mappa, orientato come YAW0_DEG
     (0 = verso +x, cioe' a destra nella planimetria; 90 = verso +y, in alto).
  2. Avvia il bringup e aspetta "Calibration End" tenendo il robot FERMO.
  3. Avvia questo script (dominio 30, Cyclone, 'source /usr/share/gazebo/setup.sh').

COMANDI (scrivi e premi Invio nel terminale dello script)
  c            errore di chiusura: quanto la posa mostrata si discosta dall'ancora.
               Va usato quando il robot e' stato riportato FISICAMENTE sul punto di
               ancoraggio. Stampa e salva su CSV distanza, angolo e percorso fatto.
  r            riancora: il robot e' sul punto di ancoraggio, azzera lo scarto.
  p X Y GRADI  riancora in una posa diversa (es. 'p 6.2 3.0 90') e la usa come
               nuova ancora.
  h            aiuto          q   uscita

LIMITI
  La deriva dell'odometria del robot reale (slittamento, giroscopio) non puo'
  essere eliminata da questo script: il gemello mostra quello che il robot crede.
  Con 'c' la misuri, con 'r' la riazzeri ogni volta che passi da un punto noto.
"""
import argparse
import csv
import math
import os
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.utilities import remove_ros_args
from nav_msgs.msg import Odometry

# --- Parametri (si possono cambiare anche da riga di comando, vedi --help) ----
MODEL_NAME = "turtlebot3_burger"      # nome del robot nel pannello "Models" di Gazebo
X0, Y0 = 4.4, 3.3          # punto di partenza nella mappa piano_sopra_riki (m)
YAW0_DEG = 0.0             # orientamento iniziale nella mappa (gradi)
Z = 2.17                   # quota del pavimento rialzato in Gazebo (m)
RATE_HZ = 10.0             # massimo di aggiornamenti al secondo verso Gazebo
MIN_DIST = 0.01            # m: sotto questo spostamento non aggiorna
MIN_ANG = math.radians(1.0)
TIMEOUT_GZ = 3.0           # s: tempo massimo di un comando 'gz model'
TIMEOUT_ODOM = 2.0         # s: oltre questo senza /odom segnala un avviso
# ------------------------------------------------------------------------------

RISULTATI = os.path.join(os.environ.get("TURTLEBOT_WS", os.getcwd()), "risultati")


# ---------- Geometria nel piano (pose = (x, y, theta)) ------------------------
def normalizza(a):
    return math.atan2(math.sin(a), math.cos(a))


def comp(a, b):
    """Composizione di pose: 'b' espressa nel sistema di 'a'."""
    c, s = math.cos(a[2]), math.sin(a[2])
    return (a[0] + c * b[0] - s * b[1],
            a[1] + s * b[0] + c * b[1],
            normalizza(a[2] + b[2]))


def inversa(a):
    c, s = math.cos(a[2]), math.sin(a[2])
    return (-(c * a[0] + s * a[1]),
            -(-s * a[0] + c * a[1]),
            normalizza(-a[2]))


def yaw_da_quaternione(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                      1.0 - 2.0 * (q.y * q.y + q.z * q.z))


# ---------- Scrittura verso Gazebo in un thread a parte -----------------------
class ScrittoreGazebo(threading.Thread):
    """Invia a Gazebo solo l'ultima posa disponibile, senza bloccare ROS 2.

    Ogni chiamata a 'gz model' puo' richiedere decine o centinaia di millisecondi
    (molto di piu' se Gazebo e' lento): farla nel thread principale bloccava la
    ricezione di /odom e il simulato restava indietro. Qui le pose intermedie
    vengono scartate e si manda sempre la piu' recente.
    """

    def __init__(self, modello, z, rate_hz, log):
        super().__init__(daemon=True)
        self.modello = modello
        self.z = z
        self.periodo = 1.0 / rate_hz
        self.log = log
        self.lock = threading.Lock()
        self.evento = threading.Event()
        self.ultima = None          # ultima posa richiesta
        self.inviata = None         # ultima posa inviata con successo
        self.fermo = False
        self.errore_segnalato = False
        self.primo_invio = False

    def aggiorna(self, posa):
        with self.lock:
            self.ultima = posa
        self.evento.set()

    def ferma(self):
        self.fermo = True
        self.evento.set()

    def _da_inviare(self, posa):
        if self.inviata is None:
            return True
        dang = abs(normalizza(posa[2] - self.inviata[2]))
        return (math.hypot(posa[0] - self.inviata[0], posa[1] - self.inviata[1]) >= MIN_DIST
                or dang >= MIN_ANG)

    def run(self):
        while not self.fermo:
            self.evento.wait(0.5)
            self.evento.clear()
            if self.fermo:
                break
            with self.lock:
                posa = self.ultima
            if posa is None or not self._da_inviare(posa):
                continue
            t0 = time.monotonic()
            if self._invia(posa):
                self.inviata = posa
            else:
                time.sleep(1.0)     # riprova piu' tardi senza intasare
            resto = self.periodo - (time.monotonic() - t0)
            if resto > 0:
                time.sleep(resto)
            # se nel frattempo e' arrivata una posa nuova, riparte subito
            with self.lock:
                if self.ultima is not posa:
                    self.evento.set()

    def _invia(self, posa):
        x, y, yaw = posa
        comando = ["gz", "model", "-m", self.modello,
                   "-x", f"{x:.3f}", "-y", f"{y:.3f}", "-z", f"{self.z:.3f}",
                   "-R", "0", "-P", "0", "-Y", f"{yaw:.4f}"]
        try:
            esito = subprocess.run(comando, capture_output=True, text=True,
                                   timeout=TIMEOUT_GZ)
        except subprocess.TimeoutExpired:
            self._segnala("Gazebo non risponde (gz model in timeout): e' molto lento o bloccato.")
            return False
        except OSError as e:
            self._segnala(f"Impossibile eseguire 'gz': {e}")
            return False
        if esito.returncode != 0 or esito.stderr.strip():
            self._segnala(f"gz model ha dato errore (Gazebo e' aperto?): {esito.stderr.strip()}")
            return False
        if self.errore_segnalato:
            self.log.info("Gazebo risponde di nuovo.")
        self.errore_segnalato = False
        if not self.primo_invio:
            self.primo_invio = True
            self.log.info(f"Prima posa inviata a Gazebo: x={x:.2f} y={y:.2f} "
                          f"yaw={math.degrees(yaw):.0f} gradi (modello '{self.modello}').")
        return True

    def _segnala(self, testo):
        if not self.errore_segnalato:
            self.log.error(testo)
            self.errore_segnalato = True


# ---------- Nodo ROS 2 --------------------------------------------------------
class GemelloDigitale(Node):
    def __init__(self, a):
        super().__init__("gemello_digitale")
        self.lock = threading.Lock()
        self.ancora = (a.x0, a.y0, math.radians(a.yaw0))   # posa nota nella mappa
        self.T = None                  # trasformazione mappa <- odom
        self.odom = None               # ultima posa odometrica (x, y, yaw)
        self.prec = None               # posa odometrica precedente
        self.percorso = 0.0            # metri percorsi dall'ultimo ancoraggio
        self.t_odom = None
        self.avviso_odom = False

        self.scrittore = ScrittoreGazebo(a.model, a.z, a.rate, self.get_logger())
        self.scrittore.start()

        self.create_subscription(Odometry, "/odom", self.su_odom, qos_profile_sensor_data)
        self.create_timer(1.0, self.controlla_odom)
        self.get_logger().info(
            f"In attesa di /odom dal robot reale. Modello Gazebo: '{a.model}', ancora "
            f"({a.x0:.2f}, {a.y0:.2f}) a {a.yaw0:.0f} gradi. Scrivi 'h' per l'aiuto.")

    # --- odometria ---
    def su_odom(self, msg):
        p = msg.pose.pose.position
        posa = (p.x, p.y, yaw_da_quaternione(msg.pose.pose.orientation))
        with self.lock:
            if self.T is None:
                # il robot e' sull'ancora: la prima odometria viene ancorata li'
                self.T = comp(self.ancora, inversa(posa))
                self.get_logger().info("Ricevuta la prima /odom: il gemello e' attivo.")
            if self.prec is not None:
                self.percorso += math.hypot(posa[0] - self.prec[0], posa[1] - self.prec[1])
            self.prec = posa
            self.odom = posa
            self.t_odom = time.monotonic()
            self.avviso_odom = False
            sim = comp(self.T, posa)
        self.scrittore.aggiorna(sim)

    def controlla_odom(self):
        with self.lock:
            if self.t_odom is None:
                self.get_logger().warn(
                    "Nessuna /odom ancora: controlla bringup, ROS_DOMAIN_ID=30 e Cyclone.",
                    throttle_duration_sec=5.0)
            elif time.monotonic() - self.t_odom > TIMEOUT_ODOM and not self.avviso_odom:
                self.get_logger().warn("Non arriva piu' /odom dal robot reale: il gemello e' fermo.")
                self.avviso_odom = True

    # --- comandi da tastiera ---
    def posa_simulata(self):
        with self.lock:
            if self.T is None or self.odom is None:
                return None
            return comp(self.T, self.odom)

    def riancora(self, ancora):
        """Il robot e' fisicamente sulla posa 'ancora': ricalcola T da adesso."""
        with self.lock:
            if self.odom is None:
                print("Nessuna /odom ricevuta: non posso riancorare.")
                return
            self.ancora = ancora
            self.T = comp(ancora, inversa(self.odom))
            self.percorso = 0.0
            sim = comp(self.T, self.odom)
        self.scrittore.aggiorna(sim)
        print(f"Riancorato in ({ancora[0]:.2f}, {ancora[1]:.2f}) a {math.degrees(ancora[2]):.1f} gradi.")

    def errore_chiusura(self):
        sim = self.posa_simulata()
        if sim is None:
            print("Nessuna /odom ricevuta.")
            return
        with self.lock:
            anc, perc = self.ancora, self.percorso
        dist = math.hypot(sim[0] - anc[0], sim[1] - anc[1])
        dang = math.degrees(normalizza(sim[2] - anc[2]))
        print(f"Errore di chiusura: {dist * 100:.1f} cm e {dang:+.1f} gradi "
              f"dopo {perc:.2f} m di percorso (rispetto all'ancora).")
        os.makedirs(RISULTATI, exist_ok=True)
        nuovo = not os.path.exists(os.path.join(RISULTATI, "chiusura_gemello.csv"))
        with open(os.path.join(RISULTATI, "chiusura_gemello.csv"), "a", newline="") as f:
            w = csv.writer(f)
            if nuovo:
                w.writerow(["data_ora", "percorso_m", "errore_cm", "errore_gradi"])
            w.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        round(perc, 3), round(dist * 100, 2), round(dang, 2)])
        print(f"Salvato in {os.path.join(RISULTATI, 'chiusura_gemello.csv')}. "
              "Scrivi 'r' per riancorare.")


def modello_esiste(nome):
    """True/False se Gazebo conosce il modello, None se non si riesce a controllare.

    'gz model -m NOME -x ...' NON controlla che il modello esista (con un nome
    sbagliato non muove niente e non da errori), mentre 'gz model -m NOME -p'
    risponde 'Unable to get info on model' se il nome e' sbagliato.
    """
    try:
        r = subprocess.run(["gz", "model", "-m", nome, "-p"], capture_output=True,
                           text=True, timeout=10.0)
    except (subprocess.TimeoutExpired, OSError):
        return None
    testo = (r.stdout + r.stderr).lower()
    if r.returncode != 0 or "unable" in testo:
        return False
    return len(r.stdout.split()) >= 6


def scegli_modello(richiesto, log):
    esiste = modello_esiste(richiesto)
    if esiste is None:
        log.warn("Non riesco a controllare il modello in Gazebo (e' aperto? "
                 "'source /usr/share/gazebo/setup.sh' fatto?). Uso il nome indicato.")
        return richiesto
    if esiste:
        return richiesto
    log.error(f"Il modello '{richiesto}' non esiste in Gazebo. Controlla il nome con: "
              f"gz model -m NOME -p   (deve stampare 6 numeri). Poi rilancia con --model NOME.")
    return None


AIUTO = __doc__.split("COMANDI")[1].split("LIMITI")[0]


def ascolta_comandi(nodo, fermati):
    for riga in sys.stdin:
        parti = riga.strip().split()
        if not parti:
            continue
        cmd = parti[0].lower()
        if cmd == "q":
            fermati.set()
            return
        if cmd == "h":
            print("COMANDI" + AIUTO)
        elif cmd == "c":
            nodo.errore_chiusura()
        elif cmd == "r":
            with nodo.lock:
                anc = nodo.ancora
            nodo.riancora(anc)
        elif cmd == "p" and len(parti) == 4:
            try:
                x, y, g = (float(v) for v in parti[1:])
            except ValueError:
                print("Uso: p X Y GRADI (numeri), per esempio: p 6.2 3.0 90")
                continue
            nodo.riancora((x, y, math.radians(g)))
        else:
            print("Comando non riconosciuto: scrivi 'h' per l'aiuto.")


def main():
    ap = argparse.ArgumentParser(description="Gemello digitale: robot reale -> Gazebo")
    ap.add_argument("--model", default=MODEL_NAME, help="nome del modello in Gazebo")
    ap.add_argument("--x0", type=float, default=X0, help="x dell'ancora nella mappa (m)")
    ap.add_argument("--y0", type=float, default=Y0, help="y dell'ancora nella mappa (m)")
    ap.add_argument("--yaw0", type=float, default=YAW0_DEG, help="orientamento dell'ancora (gradi)")
    ap.add_argument("--z", type=float, default=Z, help="quota del pavimento in Gazebo (m)")
    ap.add_argument("--rate", type=float, default=RATE_HZ, help="aggiornamenti/s massimi verso Gazebo")
    args = ap.parse_args(remove_ros_args(args=sys.argv)[1:])

    if shutil.which("gz") is None:
        print("Comando 'gz' non trovato: fai prima 'source /usr/share/gazebo/setup.sh'.")
        return
    rclpy.init()
    nodo = GemelloDigitale(args)
    modello = scegli_modello(args.model, nodo.get_logger())
    if modello is None:
        nodo.destroy_node()
        rclpy.try_shutdown()
        return
    nodo.scrittore.modello = modello
    fermati = threading.Event()
    threading.Thread(target=ascolta_comandi, args=(nodo, fermati), daemon=True).start()
    try:
        while rclpy.ok() and not fermati.is_set():
            rclpy.spin_once(nodo, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        nodo.scrittore.ferma()
        nodo.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()

