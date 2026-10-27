# TurtleBot Walker Sim

Simulazione in **ROS 2 Humble + Nav2 + Gazebo** di un TurtleBot3 (Waffle) usato come
deambulatore per la riabilitazione: il robot naviga in autonomia in una planimetria
domestica (piano sopraelevato, scale, mobili) e si può anche guidare a mano con le frecce
seguendo una linea gialla di riferimento, misurando di quanto ci si scosta.

Progetto di tesi magistrale in Ingegneria dell'Automazione Industriale
(Università degli Studi di Brescia, corso di Meccatronica, prof. Alberto Borboni).

## Contenuto

| Cartella | Cosa contiene |
|---|---|
| `scripts/` | `avvia_simulazione.sh` (menu di avvio), generatori di linee/mobili/scale, `linee_config.py` (definizione delle linee gialle) |
| `maps/` | Mappe (`.pgm` + `.yaml`) e `pgm_to_world.py` (da mappa a mondo Gazebo) |
| `worlds/` | Mondo Gazebo `piano_sopra_riki.world` (piano sopraelevato, scale, mobili, linee) |
| `src/turtlebot_controller/` | Pacchetto ROS 2: nodi di navigazione, registrazione dati, grafici, teleoperazione a frecce |
| `risultati/` | Qui vengono salvati CSV e grafici delle prove con le frecce (non versionati) |

## 1. Requisiti

- Ubuntu 22.04 (anche su Windows con WSL2)
- ROS 2 Humble, Nav2, TurtleBot3, Gazebo Classic 11
- Python 3 con `pandas`, `matplotlib`, `numpy`
- Connessione a Internet al primo avvio (Gazebo scarica i modelli dei mobili, vedi sotto)

Installazione dei pacchetti (ROS 2 Humble già installato):

```bash
sudo apt update
sudo apt install -y ros-humble-desktop ros-humble-navigation2 ros-humble-nav2-bringup \
  ros-humble-turtlebot3 ros-humble-turtlebot3-gazebo ros-humble-gazebo-ros-pkgs \
  python3-colcon-common-extensions python3-pip
pip3 install --user pandas matplotlib numpy
```

## 2. Download e compilazione

```bash
git clone https://github.com/scenedella/turtlebot-walker-sim.git
cd turtlebot-walker-sim
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=waffle
colcon build
source install/setup.bash
```

`colcon build` serve solo la prima volta e dopo modifiche al codice in `src/`.
In ogni nuovo terminale bisogna rifare `source /opt/ros/humble/setup.bash` e
`source install/setup.bash` (dalla cartella del progetto).

**Facoltativo:** se in Gazebo le texture risultano sbagliate:

```bash
sudo cp src/turtlebot_controller/gazebo.material /usr/share/gazebo-11/media/materials/scripts/
```

## 3. Avvio della simulazione

Dalla cartella del progetto:

```bash
bash scripts/avvia_simulazione.sh
```

Il menu chiede, in ordine:

1. **Mappa**: scegliere `piano_sopra_riki`.
2. **Linea gialla** da mostrare nel mondo: `1`, `2`, `3`, `t` (tutte) o `n` (nessuna).
3. **Modalità**:
   - `1` solo terminale (più leggera)
   - `2` RViz (vista 2D)
   - `3` Gazebo (vista 3D)
   - `4` Gazebo + RViz (più pesante)
4. **Posizione di partenza** del robot (invio per quella proposta).

Il primo avvio con Gazebo può richiedere uno-due minuti: Gazebo scarica da Internet i
modelli dei mobili (`NormalBed`, `MetalCabinet`, `BookshelfNew`, `OfficeDesk`, `Bathtub`,
`Toilet`, `BathroomSink`) e li conserva in `~/.gazebo/models`. Gli avvii successivi sono
immediati. **Ctrl+C** nel terminale del menu chiude tutto.

> Il menu riscrive le linee gialle dentro `worlds/piano_sopra_riki.world`: dopo un avvio
> `git status` può mostrare il file come modificato. È normale.

## 4. Navigazione autonoma A → B (andata e ritorno)

Con la simulazione già avviata, in altri terminali (ognuno con i due `source`, dalla cartella
del progetto):

```bash
# terminale 2
ros2 run turtlebot_controller turtle_distance_publisher
# terminale 3
export TURTLEBOT_WS=$PWD
ros2 run turtlebot_controller turtle_csv_handler
# terminale 4
ros2 run turtlebot_controller move_turtle_AB
```

I dati di ogni percorso vengono salvati in `src/turtlebot_controller/robot_data_csv/`.
Per i grafici (salvati in `~/grafici_turtlebot`, fuori dal progetto):

```bash
cd src/turtlebot_controller/script_python
python3 genera_grafici_png.py
```

## 5. Guida manuale con le frecce e linea gialla

Con la simulazione avviata (e una linea scelta nel menu):

```bash
python3 src/turtlebot_controller/script_python/teleop_frecce.py
```

Frecce su/giù = avanti/indietro, sinistra/destra = ruota, spazio = stop, `q` = esci.
Passando sulla linea gialla attiva, a fine percorso vengono salvati in `risultati/`
un CSV e un grafico dello scostamento dalla linea. Le linee sono definite in
`scripts/linee_config.py`.

## 6. Altre mappe

Basta mettere `nome.pgm` e `nome.yaml` in una sottocartella di `maps/`: il menu la propone
e genera da solo il mondo Gazebo con `maps/pgm_to_world.py`.

## Problemi comuni

- **`Package 'turtlebot_controller' not found`**: manca `source install/setup.bash`.
- **Gazebo non parte o è lento**: usare la modalità 1 o 2; chiudere altre finestre pesanti.
- **I mobili non compaiono**: verificare la connessione Internet e riavviare (il download dei modelli riparte).
- Dopo `wsl --shutdown` o un crash, chiudere tutto e rilanciare il menu da zero.

## Crediti

Il progetto parte dal lavoro del Gruppo 15 (Stefano Agnelli, Michele Giovanelli, Wen Wen Sun),
repository originale: https://github.com/tetano02/turtlebot_workspace
Questa versione estende la simulazione con mappe personalizzabili, piano sopraelevato con
scale, mobili, linee gialle di riferimento, guida manuale e analisi dello scostamento.

Autori di questa versione: Simone Cenedella e Riccardo Catelli.

## Licenza

Apache License 2.0, vedi il file `LICENSE`.
