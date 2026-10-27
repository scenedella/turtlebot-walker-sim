#!/usr/bin/env python3
"""
Genera un mondo Gazebo (.world / SDF) a partire da una mappa ROS (.yaml + .pgm).
Ogni parete nera della mappa diventa un box 3D, con la stessa scala (resolution)
e la stessa origine (origin) del file .yaml, cosi' mappa Nav2 e mondo Gazebo coincidono.

Uso:
    python3 pgm_to_world.py MAPPA.yaml USCITA.world [--height 2.5] [--block 3]

--height  altezza delle pareti in metri (default 2.5)
--block   raggruppa i pixel in blocchi NxN (default 3): meno box = Gazebo piu' leggero
"""
import argparse
import os
import numpy as np


def read_yaml(path):
    """Parser minimale per il yaml delle mappe (nessuna dipendenza esterna)."""
    cfg = {}
    with open(path) as f:
        for line in f:
            line = line.split('#')[0].strip()
            if ':' not in line:
                continue
            k, v = line.split(':', 1)
            cfg[k.strip()] = v.strip()
    return {
        'image': cfg['image'],
        'resolution': float(cfg['resolution']),
        'origin': [float(x) for x in cfg['origin'].strip('[]').split(',')],
        'negate': int(cfg.get('negate', 0)),
        'occupied_thresh': float(cfg.get('occupied_thresh', 0.65)),
    }


def read_pgm(path):
    """Legge un PGM binario (P5) o ASCII (P2). Restituisce array 2D uint8/uint16."""
    with open(path, 'rb') as f:
        data = f.read()
    tokens, i = [], 0
    while len(tokens) < 4:
        while data[i:i + 1].isspace():
            i += 1
        if data[i:i + 1] == b'#':
            while data[i:i + 1] != b'\n':
                i += 1
            continue
        j = i
        while not data[j:j + 1].isspace():
            j += 1
        tokens.append(data[i:j])
        i = j
    magic, w, h, maxv = tokens[0], int(tokens[1]), int(tokens[2]), int(tokens[3])
    if magic == b'P5':
        i += 1  # un solo whitespace dopo maxval
        dtype = np.uint8 if maxv < 256 else '>u2'
        arr = np.frombuffer(data, dtype=dtype, count=w * h, offset=i)
    elif magic == b'P2':
        arr = np.array(data[i:].split(), dtype=np.int32)[: w * h]
    else:
        raise ValueError('Formato PGM non supportato: %r' % magic)
    return arr.reshape(h, w), maxv


def occupied_mask(img, maxv, negate, occ_thresh):
    v = img.astype(float) / maxv
    p = v if negate else (1.0 - v)          # probabilita' di occupazione (come map_server)
    return p > occ_thresh


def merge_rectangles(mask):
    """Unisce le celle occupate in rettangoli (run orizzontali uguali su righe consecutive)."""
    rects, active = [], {}
    for r in range(mask.shape[0] + 1):
        runs = set()
        if r < mask.shape[0]:
            row = np.concatenate(([0], mask[r].astype(np.int8), [0]))
            d = np.diff(row)
            starts, ends = np.where(d == 1)[0], np.where(d == -1)[0]
            runs = set(zip(starts.tolist(), ends.tolist()))
        for run in list(active):
            if run not in runs:                    # il run non continua: chiudo il rettangolo
                rects.append((run[0], run[1], active.pop(run), r))
        for run in runs:
            active.setdefault(run, r)
    return rects  # (col0, col1, row0, row1) esclusi i secondi estremi


def build_sdf(rects, res, origin, height, block, img_h_cells):
    ox, oy = origin[0], origin[1]
    boxes = []
    for n, (c0, c1, r0, r1) in enumerate(rects):
        cs = res * block
        sx, sy = (c1 - c0) * cs, (r1 - r0) * cs
        cx = ox + (c0 + c1) / 2.0 * cs
        cy = oy + (img_h_cells - (r0 + r1) / 2.0) * cs   # riga 0 dell'immagine = bordo alto
        boxes.append(
            f'''      <collision name="w{n}"><pose>{cx:.4f} {cy:.4f} {height/2:.3f} 0 0 0</pose>
        <geometry><box><size>{sx:.4f} {sy:.4f} {height}</size></box></geometry></collision>
      <visual name="w{n}"><pose>{cx:.4f} {cy:.4f} {height/2:.3f} 0 0 0</pose>
        <geometry><box><size>{sx:.4f} {sy:.4f} {height}</size></box></geometry>
        <material><ambient>0.8 0.8 0.75 1</ambient><diffuse>0.8 0.8 0.75 1</diffuse></material></visual>''')
    return f'''<?xml version="1.0" ?>
<sdf version="1.6">
  <world name="casa">
    <include><uri>model://sun</uri></include>
    <include><uri>model://ground_plane</uri></include>
    <physics type="ode">
      <real_time_update_rate>1000.0</real_time_update_rate>
      <max_step_size>0.001</max_step_size>
    </physics>
    <gravity>0 0 -9.8</gravity>
    <model name="pareti_casa">
      <static>true</static>
      <link name="link">
{chr(10).join(boxes)}
      </link>
    </model>
  </world>
</sdf>
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('yaml')
    ap.add_argument('output')
    ap.add_argument('--height', type=float, default=2.5)
    ap.add_argument('--block', type=int, default=3)
    a = ap.parse_args()

    cfg = read_yaml(a.yaml)
    img_path = os.path.join(os.path.dirname(os.path.abspath(a.yaml)), cfg['image'])
    img, maxv = read_pgm(img_path)
    H, W = img.shape
    mask = occupied_mask(img, maxv, cfg['negate'], cfg['occupied_thresh'])

    b = a.block
    Hb, Wb = H // b, W // b                      # ritaglio ai multipli del blocco
    blocks = mask[:Hb * b, :Wb * b].reshape(Hb, b, Wb, b).any(axis=(1, 3))

    rects = merge_rectangles(blocks)
    sdf = build_sdf(rects, cfg['resolution'], cfg['origin'], a.height, b, H / b)
    with open(a.output, 'w') as f:
        f.write(sdf)
    print(f'Mappa {W}x{H} px, resolution {cfg["resolution"]} m/px, origin {cfg["origin"]}')
    print(f'Dimensioni: {W*cfg["resolution"]:.2f} m x {H*cfg["resolution"]:.2f} m')
    print(f'Generati {len(rects)} box -> {a.output}')


if __name__ == '__main__':
    main()
