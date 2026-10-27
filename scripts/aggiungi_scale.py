#!/usr/bin/env python3
import re, os, sys, shutil

WORLD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'worlds', 'piano_sopra_riki.world')

# area delle scale (metri)
X0, X1 = 5.40, 8.85
Y0, Y1 = 6.85, 7.60
STECCHE = ['w1', 'w2', 'w3', 'w4', 'w5', 'w6', 'w7', 'w8', 'w9',
           'w12', 'w15', 'w18']   # muri da togliere (w14 e w17 restano)
DIREZIONE = 1        # +1 scende verso +x, -1 verso -x
N_GRADINI = 12
ALZATA = 0.18
H = N_GRADINI * ALZATA   # quota del piano sopraelevato
ALTEZZA_MURO = 2.5

# zona del quadrato e degli ultimi scalini
QX0, QX1 = 4.65, X0      # da x 4.65 a 5.40
QY0 = 6.10               # inizio degli ultimi scalini

t = open(WORLD).read()
if 'scale_piano' in t:
    sys.exit('Scale gia presenti. Ripristina il .world dal backup e rilancia lo script.')
shutil.copy(WORLD, WORLD + '.backup')

# limiti della casa dai muri esistenti
minx = miny = 1e9
maxx = maxy = -1e9
for x, y, sx, sy in re.findall(
        r'<collision name="w\d+"><pose>([-\d.]+) ([-\d.]+) [-\d.]+ 0 0 0</pose>\s*'
        r'<geometry><box><size>([-\d.]+) ([-\d.]+) ', t):
    x, y, sx, sy = map(float, (x, y, sx, sy))
    minx, maxx = min(minx, x - sx / 2), max(maxx, x + sx / 2)
    miny, maxy = min(miny, y - sy / 2), max(maxy, y + sy / 2)

# 1. toglie le stecche
for n in STECCHE:
    t = re.sub(r'<collision name="%s">.*?</collision>\s*' % n, '', t, flags=re.S)
    t = re.sub(r'<visual name="%s">.*?</visual>\s*' % n, '', t, flags=re.S)

# 2. alza i muri sulla lastra
t = t.replace('<model name="pareti_casa">\n      <static>true</static>',
              '<model name="pareti_casa">\n      <static>true</static>\n'
              '      <pose>0 0 %.3f 0 0 0</pose>' % H, 1)


def box(nome, x0, x1, y0, y1, z0, z1, col, vis, rgb):
    cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
    s = ('<pose>%.4f %.4f %.4f 0 0 0</pose><geometry><box><size>%.4f %.4f %.4f'
         '</size></box></geometry>' % (cx, cy, cz, sx, sy, sz))
    out = ''
    if col:
        out += '<collision name="c_%s">%s</collision>\n' % (nome, s)
    if vis:
        out += ('<visual name="v_%s">%s<material><ambient>%s 1</ambient>'
                '<diffuse>%s 1</diffuse></material></visual>\n' % (nome, s, rgb, rgb))
    return out


PAV = '0.6 0.55 0.5'
MURO = '0.8 0.8 0.75'
pezzi = ''

# lastra: sinistra spezzata per scavare quadrato e scalini
pezzi += box('lastra_sx_a', minx, QX0, miny, maxy, 0, H, True, True, PAV)
pezzi += box('lastra_sx_b', QX0, QX1, miny, QY0, 0, H, True, True, PAV)
pezzi += box('lastra_sx_c', QX0, QX1, Y1, maxy, 0, H, True, True, PAV)
pezzi += box('lastra_dx', X1, maxx, miny, maxy, 0, H, True, True, PAV)
pezzi += box('lastra_sotto', X0, X1, miny, Y0, 0, H, True, True, PAV)
pezzi += box('lastra_sopra', X0, X1, Y1, maxy, 0, H, True, True, PAV)

# quadrato piano (-18 cm) e due scalini per salire (solo visivi)
pezzi += box('quadrato', QX0, QX1, 6.85, Y1, 0, H - ALZATA, False, True, '0.40 0.40 0.40')
pezzi += box('scalino_1', QX0, QX1, 6.475, 6.85, 0, H - 0.12, False, True, '0.42 0.42 0.42')
pezzi += box('scalino_2', QX0, QX1, QY0, 6.475, 0, H - 0.06, False, True, '0.45 0.45 0.45')

# gradini della scala principale (solo visivi)
larg = (X1 - X0) / N_GRADINI
for k in range(N_GRADINI - 1):
    if DIREZIONE == 1:
        a, b = X0 + k * larg, X0 + (k + 1) * larg
    else:
        a, b = X1 - (k + 1) * larg, X1 - k * larg
    quota = H - (k + 1) * ALZATA
    grigio = 0.35 + 0.04 * (k % 2)
    pezzi += box('g%d' % k, a, b, Y0, Y1, 0, quota, False, True,
                 '%.2f %.2f %.2f' % (grigio, grigio, grigio))

# parapetti invisibili (solo collisione)
pezzi += box('parapetto', X0, X1, Y0, Y1, H, H + 0.6, True, False, '0 0 0')
pezzi += box('parapetto_q', QX0, QX1, QY0, Y1, H, H + 0.6, True, False, '0 0 0')

# muri laterali
pezzi += box('muro_sx', 4.50, 4.65, 6.10, 7.60, H, H + ALTEZZA_MURO, True, True, MURO)
pezzi += box('muro_dx', 5.40, 5.70, 6.10, 6.70, H, H + ALTEZZA_MURO, True, True, MURO)

# w12: da 5.40 in poi resta muro
pezzi += box('w12_resto', 5.40, 9.30, 6.70, 6.85, H, H + ALTEZZA_MURO, True, True, MURO)
# w12_sx: nessun muro visibile, solo collisione invisibile per la mappa di Nav2
pezzi += box('p_w12_sx', 4.65, 4.80, 6.70, 6.85, H, H + 0.6, True, False, '0 0 0')

modello = ('    <model name="scale_piano">\n      <static>true</static>\n      <link name="link">\n'
           + pezzi + '      </link>\n    </model>\n')
t = t.replace('  </world>', modello + '  </world>')
open(WORLD, 'w').write(t)
print('Fatto. Piano a quota %.2f m. Il robot deve nascere a z = %.2f' % (H, H + 0.01))

