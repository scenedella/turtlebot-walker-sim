#!/usr/bin/env python3
import os, sys

WORLD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'worlds', 'piano_sopra_riki.world')
H = 12 * 0.18            # quota del pavimento (2.16 m), come in aggiungi_scale.py
Z = H + 0.01

YAW_ORIZZ = 3.1416       # letto "orizzontale" (basso a sinistra), ruotato di 180 gradi
YAW_MATR = 4.7124        # matrimoniale (alto a sinistra), ruotato di 180 gradi
YAW_VERT = 1.5708        # letti camera in basso a destra, invariato

letti = [
    ('letto_basso_sx',   4.35, 1.20, YAW_ORIZZ),
    ('letto_alto_sx_1',  2.09, 6.50, YAW_MATR),
    ('letto_alto_sx_2',  2.81, 6.50, YAW_MATR),
    ('letto_basso_dx_1', 6.76, 1.75, YAW_VERT),
    ('letto_basso_dx_2', 8.27, 1.75, YAW_VERT),
]

t = open(WORLD).read()
if 'letto_basso_sx' in t:
    sys.exit('Letti gia presenti. Ripristina il .world dal backup, rilancia aggiungi_scale.py e poi questo script.')

blocco = ''
for nome, x, y, yaw in letti:
    blocco += ('    <include>\n'
               '      <uri>model://NormalBed</uri>\n'
               '      <name>%s</name>\n'
               '      <static>true</static>\n'
               '      <pose>%.3f %.3f %.3f 0 0 %.4f</pose>\n'
               '    </include>\n' % (nome, x, y, Z, yaw))

t = t.replace('  </world>', blocco + '  </world>')
open(WORLD, 'w').write(t)
print('Aggiunti %d letti.' % len(letti))



