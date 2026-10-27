import math


def s_curva(x0, x1, yc, amp, n=24):
    """Curva a S: un periodo completo di seno tra x0 e x1."""
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append((x0 + (x1 - x0) * t, yc + amp * math.sin(2 * math.pi * t)))
    return pts


# Ogni linea e una lista di punti (x, y) in metri, nel mondo di Gazebo.
# Due punti = linea dritta, piu punti = linea spezzata/curva.
LINEE = {
    '1': [(1.8, 2.27), (4.2, 2.27)],            # stanza in basso a sinistra (dritta)
    '2': [(6.7, 2.9), (8.5, 3.6)],              # stanza a destra (diagonale)
    '3': s_curva(1.4, 3.8, 4.9, 0.35),          # stanza in alto a sinistra (S)
}
H = 12 * 0.18             # quota del pavimento
LARGH = 0.05              # larghezza della striscia (m)


def lunghezza(pts):
    return sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
               for i in range(len(pts) - 1))

