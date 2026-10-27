#!/usr/bin/env python3
import os, sys

WORLD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'worlds', 'piano_sopra_riki.world')
H = 12 * 0.18            # quota del pavimento (2.16 m)
Z = H + 0.01

YAW = 3.1416             # girati di 180 gradi; prova 0.0 / 1.5708 / 4.7124 se serve

armadi = [
    # camera in basso a sinistra (riquadri 1, 2 e 3)
    ('armadio_1', 1.30, 0.80, YAW),
    ('armadio_2', 2.00, 0.80, YAW),
('armadio_3', 2.70, 0.80, YAW),
    # camera in alto a sinistra (riquadri 4, 5, 6, 7)
    ('armadio_4', 1.60, 4.00, YAW),
    ('armadio_5', 2.30, 4.00, YAW),
    ('armadio_6', 3.00, 4.00, YAW),
('armadio_7', 3.70, 4.00, YAW),
]

t = open(WORLD).read()
if 'armadio_1' in t:
    sys.exit('Armadi gia presenti. Ripristina il .world dal backup e rilancia gli script in ordine.')

blocco = ''
for nome, x, y, yaw in armadi:
    blocco += ('    <include>\n'
               '      <uri>model://MetalCabinet</uri>\n'
               '      <name>%s</name>\n'
               '      <static>true</static>\n'
               '      <pose>%.3f %.3f %.3f 0 0 %.4f</pose>\n'
               '    </include>\n' % (nome, x, y, Z, yaw))

t = t.replace('  </world>', blocco + '  </world>')
open(WORLD, 'w').write(t)
print('Aggiunti %d armadi.' % len(armadi))





