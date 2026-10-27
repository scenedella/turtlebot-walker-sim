#!/usr/bin/env python3
import os, sys

WORLD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'worlds', 'piano_sopra_riki.world')
H = 12 * 0.18            # quota del pavimento (2.16 m), come in aggiungi_scale.py
Z = H + 0.01

YAW = 0.0                # prova 1.5708, 3.1416 o 4.7124 se la libreria risulta girata

librerie = [
    ('libreria_basso_sx', 3.53, 3.69, YAW),
]

t = open(WORLD).read()
if 'libreria_basso_sx' in t:
    sys.exit('Libreria gia presente. Ripristina il .world dal backup e rilancia gli script in ordine.')

blocco = ''
for nome, x, y, yaw in librerie:
    blocco += ('    <include>\n'
               '      <uri>model://BookshelfNew</uri>\n'
               '      <name>%s</name>\n'
               '      <static>true</static>\n'
               '      <pose>%.3f %.3f %.3f 0 0 %.4f</pose>\n'
               '    </include>\n' % (nome, x, y, Z, yaw))

t = t.replace('  </world>', blocco + '  </world>')
open(WORLD, 'w').write(t)
print('Aggiunte %d librerie.' % len(librerie))





