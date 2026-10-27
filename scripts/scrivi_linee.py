#!/usr/bin/env python3
import sys, os, re, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from linee_config import LINEE, H, LARGH, lunghezza


def blocco(nome, pts):
    out = ('    <model name="%s">\n      <static>true</static>\n'
           '      <link name="link">\n' % nome)
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        lung = math.hypot(x1 - x0, y1 - y0) + LARGH     # piccola sovrapposizione tra i pezzi
        yaw = math.atan2(y1 - y0, x1 - x0)
        out += ('        <visual name="v%d">\n'
                '          <pose>%.4f %.4f %.4f 0 0 %.4f</pose>\n'
                '          <geometry><box><size>%.4f %.4f 0.004</size></box></geometry>\n'
                '          <material><ambient>1 1 0 1</ambient><diffuse>1 1 0 1</diffuse>'
                '<emissive>1 1 0 1</emissive></material>\n'
                '        </visual>\n'
                % (i, (x0 + x1) / 2, (y0 + y1) / 2, H + 0.002, yaw, lung, LARGH))
    out += '      </link>\n    </model>\n'
    return out


def main():
    if sys.argv[1] == 'elenco':
        for k, pts in LINEE.items():
            tipo = 'dritta' if len(pts) == 2 else 'curva/spezzata'
            print('  %s) %s, lunga %.2f m, da (%.2f, %.2f) a (%.2f, %.2f)'
                  % (k, tipo, lunghezza(pts), pts[0][0], pts[0][1], pts[-1][0], pts[-1][1]))
        return

    world, ws, scelta = sys.argv[2], sys.argv[3], sys.argv[4].strip()
    if scelta not in LINEE and scelta not in ('t', 'n'):
        sys.exit('Scelta della linea non valida.')

    t = open(world).read()
    t = re.sub(r'\s*<model name="linea_gialla[^"]*">.*?</model>\n', '\n', t, flags=re.S)
    if scelta == 'n':
        print('Nessuna linea nel mondo.')
    elif scelta == 't':
        t = t.replace('  </world>',
                      ''.join(blocco('linea_gialla_' + k, p) for k, p in LINEE.items()) + '  </world>')
        print('Tutte le linee scritte nel mondo.')
    else:
        t = t.replace('  </world>', blocco('linea_gialla', LINEE[scelta]) + '  </world>')
        print('Linea %s scritta nel mondo.' % scelta)
    open(world, 'w').write(t)
    open(os.path.join(ws, 'linea_attiva.txt'), 'w').write(scelta)


main()

