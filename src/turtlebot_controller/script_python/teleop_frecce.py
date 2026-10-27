#!/usr/bin/env python3
import os, sys, csv, math, time, select, termios, tty
from datetime import datetime

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def _trova_ws():
    """Cartella radice del progetto: variabile TURTLEBOT_WS, oppure risale dalla cartella corrente."""
    env = os.environ.get('TURTLEBOT_WS')
    if env and os.path.isfile(os.path.join(env, 'scripts', 'linee_config.py')):
        return env
    qui = os.path.dirname(os.path.abspath(__file__))
    cand = os.path.abspath(os.path.join(qui, '..', '..', '..'))
    if os.path.isfile(os.path.join(cand, 'scripts', 'linee_config.py')):
        return cand
    d = os.getcwd()
    while True:
        if os.path.isfile(os.path.join(d, 'scripts', 'linee_config.py')):
            return d
        if os.path.dirname(d) == d:
            break
        d = os.path.dirname(d)
    for c in ('~/turtlebot-walker-sim', '~/turtlebot_workspace'):
        c = os.path.expanduser(c)
        if os.path.isfile(os.path.join(c, 'scripts', 'linee_config.py')):
            return c
    raise SystemExit('Cartella del progetto non trovata: lancia il comando da dentro la cartella '
                     'del progetto oppure imposta TURTLEBOT_WS=/percorso/del/progetto')


WS = _trova_ws()
sys.path.insert(0, os.path.join(WS, 'scripts'))
from linee_config import LINEE

LIN = 0.15
ANG = 0.25
TIMEOUT = 0.7
RAMPA_LIN = 0.02
RAMPA_ANG = 0.02

# Se /odom parte da (0,0) invece che dalla posizione di spawn, metti qui la posizione di partenza
ODOM_OFFSET_X = 0.0
ODOM_OFFSET_Y = 0.0

LARGH_ZONA = 0.25    # distanza massima dalla linea per "vederla" (m)
MIN_LUNG = 0.5       # percorso minimo per salvare il grafico (m)
SOGLIA_CM = 8.0      # range accettabile: da -8 a +8 cm
CARTELLA = os.path.join(WS, 'risultati')
ATTIVA = os.path.join(WS, 'linea_attiva.txt')

ISTRUZIONI = """
Controllo robot con le frecce (tieni premuto per muoverti):
  freccia SU/GIU    avanti/indietro
  freccia SX/DX     ruota
  SPAZIO            stop
  q                 esci
Quando passi su una linea gialla attiva, il grafico viene creato alla fine.
"""


def leggi_tasto(timeout=0.02):
    if select.select([sys.stdin], [], [], timeout)[0]:
        c = sys.stdin.read(1)
        if c == '\x1b':
            c += sys.stdin.read(2)
        return c
    return None


def verso(attuale, target, passo):
    if target > attuale:
        return min(attuale + passo, target)
    return max(attuale - passo, target)


def prepara(pts):
    cum = [0.0]
    for i in range(len(pts) - 1):
        cum.append(cum[-1] + math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]))
    return cum


def proietta(px, py, pts, cum):
    """Ritorna (distanza lungo la linea, scostamento con segno, s grezzo) sul segmento piu vicino."""
    best = None
    for i in range(len(pts) - 1):
        ax, ay = pts[i]
        bx, by = pts[i + 1]
        vx, vy = bx - ax, by - ay
        seg = math.hypot(vx, vy)
        u = ((px - ax) * vx + (py - ay) * vy) / (seg * seg)
        uc = max(0.0, min(1.0, u))
        qx, qy = ax + uc * vx, ay + uc * vy
        d = math.hypot(px - qx, py - qy)
        if best is None or d < best[0]:
            cross = (vx * (py - ay) - vy * (px - ax)) / seg     # + = a sinistra
            best = (d, cum[i] + uc * seg, math.copysign(d, cross), cum[i] + u * seg)
    return best[1], best[2], best[3]


def salva(campioni, nome_linea, lung_linea):
    os.makedirs(CARTELLA, exist_ok=True)
    nome = datetime.now().strftime('%Y%m%d_%H%M%S') + '_linea' + nome_linea
    s = [c[0] for c in campioni]
    e = [c[1] * 100.0 for c in campioni]
    with open(os.path.join(CARTELLA, nome + '.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['distanza_m', 'scostamento_cm', 'tempo_s'])
        for c in campioni:
            w.writerow([round(c[0], 4), round(c[1] * 100, 3), round(c[2], 3)])
    media = sum(abs(v) for v in e) / len(e)
    mx = max(abs(v) for v in e)
    rmse = math.sqrt(sum(v * v for v in e) / len(e))
    copertura = abs(s[-1] - s[0]) / lung_linea * 100
    buono = mx <= SOGLIA_CM

    plt.figure(figsize=(9, 4))
    plt.plot(s, e, color='tab:blue', label='percorso del robot')
    plt.axhline(0, color='gold', linewidth=3, label='linea gialla %s' % nome_linea)
    plt.axhline(SOGLIA_CM, color='red', linewidth=1.5, label='limite +/- %.0f cm' % SOGLIA_CM)
    plt.axhline(-SOGLIA_CM, color='red', linewidth=1.5)
    plt.xlabel('Distanza lungo la linea (m)')
    plt.ylabel('Scostamento (cm)')
    plt.title('Linea %s - medio %.1f cm, max %.1f cm, RMSE %.1f cm (copertura %.0f%%)'
              % (nome_linea, media, mx, rmse, copertura))
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    p = os.path.join(CARTELLA, nome + '.png')
    plt.savefig(p, dpi=120)
    plt.close()
    return p, buono


def main():
    scelta = open(ATTIVA).read().strip() if os.path.exists(ATTIVA) else 'n'
    if scelta == 't':
        ids = list(LINEE.keys())
    elif scelta in LINEE:
        ids = [scelta]
    else:
        ids = []

    linee = {}
    for k in ids:
        pts = LINEE[k]
        cum = prepara(pts)
        linee[k] = {'pts': pts, 'cum': cum, 'L': cum[-1],
                    'reg': False, 'camp': [], 't0': 0.0, 'fuori': 0}
    if ids:
        print('Linee attive: ' + ', '.join(ids))
    else:
        print('Nessuna linea attiva: il robot si muove senza registrare.')

    rclpy.init()
    node = rclpy.create_node('teleop_frecce')
    pub = node.create_publisher(Twist, '/cmd_vel', 10)
    pos = {'x': None, 'y': None}

    def odom_cb(m):
        pos['x'] = m.pose.pose.position.x + ODOM_OFFSET_X
        pos['y'] = m.pose.pose.position.y + ODOM_OFFSET_Y

    node.create_subscription(Odometry, '/odom', odom_cb, 10)

    vecchie = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())
    msg = Twist()
    ultimo = time.time()
    cmd_lin = 0.0
    cmd_ang = 0.0
    print(ISTRUZIONI)
    try:
        while rclpy.ok():
            tasto = leggi_tasto()
            rclpy.spin_once(node, timeout_sec=0.0)
            if tasto is not None:
                ultimo = time.time()
            if tasto == '\x1b[A':
                msg.linear.x, msg.angular.z = LIN, 0.0
            elif tasto == '\x1b[B':
                msg.linear.x, msg.angular.z = -LIN, 0.0
            elif tasto == '\x1b[D':
                msg.linear.x, msg.angular.z = 0.0, ANG
            elif tasto == '\x1b[C':
                msg.linear.x, msg.angular.z = 0.0, -ANG
            elif tasto == ' ':
                msg.linear.x, msg.angular.z = 0.0, 0.0
            elif tasto == 'q':
                break
            elif tasto is None and time.time() - ultimo > TIMEOUT:
                msg.linear.x, msg.angular.z = 0.0, 0.0

            cmd_lin = verso(cmd_lin, msg.linear.x, RAMPA_LIN)
            cmd_ang = verso(cmd_ang, msg.angular.z, RAMPA_ANG)
            out = Twist()
            out.linear.x = cmd_lin
            out.angular.z = cmd_ang
            pub.publish(out)

            if pos['x'] is None:
                continue

            for k, d in linee.items():
                s, err, s_raw = proietta(pos['x'], pos['y'], d['pts'], d['cum'])
                dentro = abs(err) <= LARGH_ZONA and -0.05 <= s_raw <= d['L'] + 0.05

                if dentro:
                    d['fuori'] = 0
                    if not d['reg']:
                        d['reg'] = True
                        d['camp'] = []
                        d['t0'] = time.time()
                        print('Linea %s rilevata: registro...' % k)
                    d['camp'].append((s, err, time.time() - d['t0']))
                elif d['reg']:
                    d['fuori'] += 1
                    if d['fuori'] < 25:      # circa mezzo secondo di tolleranza
                        continue
                    d['reg'] = False
                    c = d['camp']
                    lung = abs(c[-1][0] - c[0][0]) if c else 0.0
                    if len(c) >= 10 and lung >= MIN_LUNG:
                        p, buono = salva(c, k, d['L'])
                        print('Fine linea %s. Grafico salvato in: %s' % (k, p))
                        if buono:
                            print('Hai fatto un buon lavoro!')
                        else:
                            print('Devi migliorare.')
                    else:
                        print('Linea %s scartata: %d campioni, %.2f m percorsi, '
                              'ultimo punto s=%.2f err=%.1f cm'
                              % (k, len(c), lung, s, err * 100))
                    d['camp'] = []
    finally:
        pub.publish(Twist())
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, vecchie)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

