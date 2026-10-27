import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use('Agg')  # nessuna finestra, solo file
import matplotlib.pyplot as plt

import elaborate_data as ed
from glob import glob

files = sorted(glob(os.path.join(ed.data_folder, "*.csv")))
goal_file = max([f for f in files if 'goal' in f])
home_file = max([f for f in files if 'home' in f])

print(f"Uso questi file:\n  goal: {goal_file}\n  home: {home_file}")

df_goal = ed.carica_dati(goal_file)
df_home = ed.carica_dati(home_file)

stat_goal = ed.calcola_statistiche(df_goal)
stat_home = ed.calcola_statistiche(df_home)
ed.stampa_statistiche(stat_goal, goal_file)
ed.stampa_statistiche(stat_home, home_file)

# Salva fuori dal progetto (cosi' i grafici non finiscono su git): ~/grafici_turtlebot
# oppure la cartella indicata nella variabile d'ambiente GRAFICI_DIR
output_dir = os.environ.get("GRAFICI_DIR") or os.path.expanduser("~/grafici_turtlebot")
os.makedirs(output_dir, exist_ok=True)

def salva_e_chiudi():
    for num in plt.get_fignums():
        fig = plt.figure(num)
        titolo = fig.axes[0].get_title() if fig.axes else f"grafico_{num}"
        nome_pulito = titolo.lower().replace(" ", "_")
        path_out = os.path.join(output_dir, f"{nome_pulito}_{num}.png")
        fig.savefig(path_out, dpi=150, bbox_inches='tight')
        print(f"Salvato: {path_out}")
    plt.close('all')
plt.show = salva_e_chiudi

ed.plot_grafici(df_goal, df_home)
print(f"\nTutti i grafici sono stati salvati in: {output_dir}")
print("Puoi aprirli direttamente da Windows, cartella 'grafici_turtlebot' sul Desktop.")
