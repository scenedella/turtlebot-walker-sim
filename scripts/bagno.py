#!/usr/bin/env python3
import os, sys

WORLD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'worlds', 'piano_sopra_riki.world')
H = 12 * 0.18            # quota del pavimento (2.16 m)
Z = H + 0.01

# lavandino: girato di 180 gradi, contro il muro in basso e alzato da terra
SINK_ALZA = 0.70         # metri da terra (0 = appoggiato a terra)
SINK = (8.0, 4.91, 3.1416)

# vasca: orizzontale, in alto a sinistra nella stanza
VASCA = (6.61, 6.27, 0.0)

# wc: nel riquadro in alto a destra, serbatoio contro il muro in alto
WC = (8.42, 6.30, 4.7124)      # prova 1.5708 se il serbatoio e dal lato sbagliato

bagno = [
    ('bagno_lavandino', 'BathroomSink', SINK[0], SINK[1], Z + SINK_ALZA, SINK[2]),
    ('bagno_vasca', 'Bathtub', VASCA[0], VASCA[1], Z, VASCA[2]),
    ('bagno_wc', 'Toilet', WC[0], WC[1], Z, WC[2]),
]

t = open(WORLD).read()
if 'bagno_vasca' in t:
    sys.exit('Bagno gia presente. Ripristina il .world dal backup e rilancia gli script in ordine.')

blocco = ''
for nome, modello, x, y, z, yaw in bagno:
    blocco += ('    <include>\n'
               '      <uri>model://%s</uri>\n'
               '      <name>%s</name>\n'
               '      <static>true</static>\n'
               '      <pose>%.3f %.3f %.3f 0 0 %.4f</pose>\n'
               '    </include>\n' % (modello, nome, x, y, z, yaw))

t = t.replace('  </world>', blocco + '  </world>')
open(WORLD, 'w').write(t)
print('Aggiunti %d elementi del bagno.' % len(bagno))

