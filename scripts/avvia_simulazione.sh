#!/bin/bash
# Script interattivo per avviare la simulazione TurtleBot con qualsiasi mappa presente nel progetto.
set -e

WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export TURTLEBOT_WS="$WS"
MAPS_DIR="$WS/maps"
WORLDS_DIR="$WS/worlds"
PIDS=()

cleanup() {
    echo ""
    echo "Chiusura in corso..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    sleep 1
    pkill -9 -f gzserver 2>/dev/null || true
    pkill -9 -f gzclient 2>/dev/null || true
    pkill -9 -f "rviz2" 2>/dev/null || true
    echo "Tutto chiuso."
}
trap cleanup EXIT INT TERM

echo "=== TurtleBot - Avvio simulazione ==="
echo ""

# --- 1. Selezione mappa ---
mapfile -t YAML_FILES < <(find "$MAPS_DIR" -maxdepth 2 -name "*.yaml" 2>/dev/null | sort)
if [ ${#YAML_FILES[@]} -eq 0 ]; then
    echo "Nessuna mappa trovata in $MAPS_DIR"
    exit 1
fi

echo "Mappe disponibili:"
for i in "${!YAML_FILES[@]}"; do
    echo "  $((i+1))) $(basename "${YAML_FILES[$i]}")"
done
read -rp "Scegli una mappa [1-${#YAML_FILES[@]}]: " map_choice
YAML_FILE="${YAML_FILES[$((map_choice-1))]}"
MAP_NAME=$(basename "$YAML_FILE" .yaml)

if [ -z "$YAML_FILE" ]; then
    echo "Scelta non valida."
    exit 1
fi
echo "Mappa selezionata: $MAP_NAME"
echo ""

# --- 2. Genera il mondo Gazebo se non esiste ---
WORLD_FILE="$WORLDS_DIR/${MAP_NAME}.world"
mkdir -p "$WORLDS_DIR"
if [ ! -f "$WORLD_FILE" ]; then
    echo "Mondo Gazebo non trovato per questa mappa, lo genero ora..."
    python3 "$MAPS_DIR/pgm_to_world.py" "$YAML_FILE" "$WORLD_FILE" --height 2.5
    echo ""
else
    echo "Mondo Gazebo trovato: $WORLD_FILE"
    echo ""
fi

# --- 2b. Selezione linea gialla (solo per piano_sopra_riki) ---
SPAWN_Z=0.01
if [ "$MAP_NAME" == "piano_sopra_riki" ]; then
    SPAWN_Z=2.17
    if [ -f "$WS/scripts/linee_config.py" ]; then
        echo "Linee gialle disponibili:"
        python3 "$WS/scripts/scrivi_linee.py" elenco
        echo "  t) Tutte e tre"
        echo "  n) Nessuna"
        read -rp "Scegli la linea da far apparire: " LINE_CHOICE
        python3 "$WS/scripts/scrivi_linee.py" scrivi "$WORLD_FILE" "$WS" "$LINE_CHOICE"
        echo ""
    fi
fi

# --- 3. Selezione modalità ---
# Tutte le modalità avviano Nav2 (navigazione autonoma completa).
# Cambia solo l'interfaccia grafica usata per osservare la simulazione.
echo "Modalità disponibili (in tutte la navigazione Nav2 è attiva):"
echo "  1) Solo terminale (nessuna grafica - il più leggero, consigliato con RAM limitata)"
echo "  2) RViz (vista 2D dall'alto, Gazebo senza finestra)"
echo "  3) Gazebo (vista 3D della casa, senza RViz)"
echo "  4) Completo (Gazebo 3D + RViz 2D insieme - richiede più risorse)"
read -rp "Scegli una modalità [1-4]: " mode
echo ""

# --- 4. Posizione di partenza del robot ---
read -rp "Coordinata X di partenza del robot [default 2.0]: " START_X
read -rp "Coordinata Y di partenza del robot [default 2.0]: " START_Y
START_X=${START_X:-2.0}
START_Y=${START_Y:-2.0}

# Controllo (non bloccante) che il punto sia in area libera sulla mappa
python3 - "$YAML_FILE" "$START_X" "$START_Y" "$MAPS_DIR" << 'PYEOF' || true
import sys
yaml_path, x, y, maps_dir = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
sys.path.insert(0, maps_dir)
import pgm_to_world as g
import os
cfg = g.read_yaml(yaml_path)
img_path = os.path.join(os.path.dirname(os.path.abspath(yaml_path)), cfg['image'])
img, maxv = g.read_pgm(img_path)
H, W = img.shape
res, ox, oy = cfg['resolution'], cfg['origin'][0], cfg['origin'][1]
col = int((x - ox) / res)
row = int(H - (y - oy) / res)
if 0 <= row < H and 0 <= col < W:
    occ = g.occupied_mask(img, maxv, cfg['negate'], cfg['occupied_thresh'])
    if occ[row, col]:
        print(f"ATTENZIONE: il punto ({x},{y}) sembra cadere su un ostacolo/muro sulla mappa.")
    else:
        print(f"Punto di partenza ({x},{y}) verificato: area libera.")
else:
    print(f"ATTENZIONE: il punto ({x},{y}) è fuori dai confini della mappa.")
PYEOF
echo ""

# --- 5. Avvio in base alla modalità ---
source /opt/ros/humble/setup.bash
export GAZEBO_MODEL_PATH=$WS/models:${GAZEBO_MODEL_PATH:+$GAZEBO_MODEL_PATH:}/opt/ros/humble/share/turtlebot3_gazebo/models:$HOME/.gazebo/models
source "$WS/install/setup.bash" 2>/dev/null || echo "Nota: workspace non ancora compilato (colcon build)."

case $mode in
  1|2)
    echo "Avvio Gazebo (senza finestra)..."
    gzserver "$WORLD_FILE" -s libgazebo_ros_init.so -s libgazebo_ros_factory.so &
    PIDS+=($!)
    echo "Attendo che Gazebo sia pronto..."
    for i in $(seq 1 30); do
        if ros2 service list 2>/dev/null | grep -q spawn_entity; then break; fi
        sleep 2
    done
    ;;
  3|4)
    echo "Avvio Gazebo (con finestra)..."
    gazebo "$WORLD_FILE" -s libgazebo_ros_init.so -s libgazebo_ros_factory.so -s libgazebo_ros_state.so &
    PIDS+=($!)
    echo "Attendo che Gazebo sia pronto (può volerci un minuto)..."
    for i in $(seq 1 120); do
        if ros2 service list 2>/dev/null | grep -q spawn_entity; then break; fi
        sleep 2
    done
    ;;
esac

echo "Creo il robot nella posizione di partenza..."
ros2 run gazebo_ros spawn_entity.py -entity turtlebot3_waffle \
    -file /opt/ros/humble/share/turtlebot3_gazebo/models/turtlebot3_waffle/model.sdf \
    -x "$START_X" -y "$START_Y" -z "$SPAWN_Z" -timeout 120
echo ""

USE_RVIZ="False"
if [ "$mode" == "2" ] || [ "$mode" == "4" ]; then
    USE_RVIZ="True"
fi
echo "Avvio Nav2 (RViz: $USE_RVIZ)..."
echo "Premi Ctrl+C per terminare tutto."
ros2 launch nav2_bringup tb3_simulation_launch.py \
    use_simulator:=False use_rviz:="$USE_RVIZ" \
    map:="$YAML_FILE"

