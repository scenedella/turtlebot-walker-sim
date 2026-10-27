#!/usr/bin/env python3
import os, sys

WORLD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'worlds', 'piano_sopra_riki.world')
H = 12 * 0.18            # quota del pavimento (2.16 m), come in aggiungi_scale.py
Z = H + 0.01

YAW = 4.7124             # scrivanie in orizzontale; prova 0.0 se risultano girate

scrivanie = [
    ('scrivania_basso_sx', 1.92, 3.30, YAW),
    ('scrivania_basso_dx', 7.65, 4.20, YAW),
]

t = open(WORLD).read()
if 'scrivania_basso_sx' in t:
    sys.exit('Scrivanie gia presenti. Ripristina il .world dal backup e rilancia gli script in ordine.')

blocco = ''
for nome, x, y, yaw in scrivanie:
    blocco += ('    <include>\n'
               '      <uri>model://OfficeDesk</uri>\n'
               '      <name>%s</name>\n'
               '      <static>true</static>\n'
               '      <pose>%.3f %.3f %.3f 0 0 %.4f</pose>\n'
               '    </include>\n' % (nome, x, y, Z, yaw))

t = t.replace('  </world>', blocco + '  </world>')
open(WORLD, 'w').write(t)
print('Aggiunte %d scrivanie.' % len(scrivanie))








