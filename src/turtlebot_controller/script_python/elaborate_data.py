import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from glob import glob

# Percorso della cartella contenente i CSV
data_folder = os.path.join("..", "robot_data_csv")

def seleziona_file():
    scelta = input("Scegli un'opzione:\nA) Ultimi due file (home e goal)\nB) Inserisci data e run specifica\n").upper()
    if scelta == 'A':
        # Trova gli ultimi file per ciascun tipo (goal e home)
        files = sorted(glob(os.path.join(data_folder, "*.csv")))
        last_goal_file = max([f for f in files if 'goal' in f])
        last_home_file = max([f for f in files if 'home' in f])
        return last_goal_file, last_home_file
    elif scelta == 'B':
        data_run = input("Inserisci la corsa che vuoi visualizzare (YYYYMMDD_00run): ")
        goal_file = os.path.join(data_folder, f"{data_run}_goal.csv")
        home_file = os.path.join(data_folder, f"{data_run}_home.csv")
        if os.path.exists(goal_file) and os.path.exists(home_file):
            return goal_file, home_file
        else:
            print("File specificati non trovati.")
            return None, None
    else:
        print("Opzione non valida.")
        return None, None

def carica_dati(file_path):
    df = pd.read_csv(file_path)
    df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S').dt.time
    return df

def calcola_statistiche(df):
    tempo_inizio = datetime.combine(datetime.today(), df['time'].iloc[0])
    tempo_fine = datetime.combine(datetime.today(), df['time'].iloc[-1])
    tempo_percorrenza = (tempo_fine - tempo_inizio).total_seconds()
    
    distanza_totale = df['distance'].sum()
    velocita_media = df['vel_lin'].mean()
    posizione_iniziale = (df['pos_x'].iloc[0], df['pos_y'].iloc[0])
    posizione_finale = (df['pos_x'].iloc[-1], df['pos_y'].iloc[-1])
    
    return tempo_percorrenza, velocita_media, distanza_totale, posizione_iniziale, posizione_finale

def stampa_statistiche(statistiche, nome_file):
    tempo, vel_media, dist_totale, pos_iniz, pos_fin = statistiche
    print(f"\nStatistiche per {nome_file}:")
    print(f"Tempo di percorrenza: {tempo} secondi")
    print(f"Velocità media: {vel_media:.2f} m/s")
    print(f"Distanza totale percorsa: {dist_totale:.2f} m")
    print(f"Posizione iniziale:\nX: {pos_iniz[0]}\nY: {pos_iniz[1]}")
    print(f"Posizione finale:\nX:{pos_fin[0]}\nY:{pos_fin[1]}")

def converti_tempo_in_secondi(df):
    # Convertiamo la colonna `time` in timedelta a partire da mezzanotte
    df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S').dt.time
    df['time_sec'] = pd.to_timedelta(df['time'].astype(str)).dt.total_seconds()
    
    # Troviamo il tempo di inizio
    start_time = df['time_sec'].iloc[0]
    df['time_sec'] -= start_time  # Convertiamo a secondi rispetto all'inizio
    return df

def plot_grafici(df_goal, df_home):

    # Colors

    color1 = '#1f77b4'
    color2 = '#ff7f0e'

    # Converti la colonna tempo in secondi dall'inizio per entrambi i dataframe
    df_goal = converti_tempo_in_secondi(df_goal)
    df_home = converti_tempo_in_secondi(df_home)

    # Plot velocità lineare - goal
    plt.figure(figsize=(10, 6))
    plt.subplot(2,1,1)
    plt.plot(df_goal['time_sec'], df_goal['vel_lin'], label="Goal", color=color1)
    plt.xlabel("Tempo [s]")
    plt.ylabel("Velocità lineare [m/s]")
    plt.title("Velocità Lineare nel Tempo")
    plt.legend()
    plt.grid()
    # Plot velocità lineare - home
    plt.subplot(2,1,2)
    plt.plot(df_home['time_sec'], df_home['vel_lin'], label="Home", color=color2)
    plt.xlabel("Tempo [s]")
    plt.ylabel("Velocità lineare [m/s]")
    plt.title("Velocità Lineare nel Tempo")
    plt.legend()
    plt.grid()

    # Plot velocità angolare - goal
    plt.figure(figsize=(10, 6))
    plt.subplot(2,1,1)
    plt.plot(df_goal['time_sec'], df_goal['vel_ang'], label="Goal", color=color1)
    plt.xlabel("Tempo [s]")
    plt.ylabel("Velocità angolare [rad/s]")
    plt.title("Velocità Angolare nel Tempo")
    plt.legend()
    plt.grid()
    # Plot velocità angolare - home 
    plt.subplot(2,1,2)
    plt.plot(df_home['time_sec'], df_home['vel_ang'], label="Home", color=color2)
    plt.xlabel("Tempo [s]")
    plt.ylabel("Velocità angolare [rad/s]")
    plt.title("Velocità Angolare nel Tempo")
    plt.legend()
    plt.grid()

    # Plot distanza percorsa totale man mano - goal
    plt.figure(figsize=(10, 6))
    plt.subplot(2,1,1)
    plt.plot(df_goal['time_sec'], df_goal['distance'].cumsum(), label="Goal", color=color1)
    plt.xlabel("Tempo [s]")
    plt.ylabel("Distanza Totale Percorsa [m]")
    plt.title("Distanza Totale Percorsa nel Tempo")
    plt.legend()
    plt.grid()
    # Plot distanza percorsa totale man mano - home
    plt.subplot(2,1,2)
    plt.plot(df_home['time_sec'], df_home['distance'].cumsum(), label="Home", color=color2)
    plt.xlabel("Tempo [s]")
    plt.ylabel("Distanza Totale Percorsa [m]")
    plt.title("Distanza Totale Percorsa nel Tempo")
    plt.legend()
    plt.grid()

    # Plot della traiettoria (grafico xy) - goal
    plt.figure(figsize=(10, 6))
    plt.subplot(2,1,1)
    plt.plot(-df_goal['pos_y'], df_goal['pos_x'], label="Goal Trajectory", color=color1)
    plt.xlabel("Posizione Y [m]")
    plt.ylabel("Posizione X [m]")
    plt.title("Traiettoria del Robot")
    plt.legend()
    plt.grid()
    # Plot della traiettoria (grafico xy) - home
    plt.subplot(2,1,2)
    plt.plot(-df_home['pos_y'], df_home['pos_x'], label="Home Trajectory", color=color2)
    plt.xlabel("Posizione Y [m]")
    plt.ylabel("Posizione X [m]")
    plt.title("Traiettoria del Robot")
    plt.legend()
    plt.grid()

    plt.show()

def main():
    goal_file, home_file = seleziona_file()
    if goal_file and home_file:
        df_goal = carica_dati(goal_file)
        df_home = carica_dati(home_file)

        # Calcolo delle statistiche
        statistiche_goal = calcola_statistiche(df_goal)
        statistiche_home = calcola_statistiche(df_home)

        # Stampa statistiche
        stampa_statistiche(statistiche_goal, goal_file)
        stampa_statistiche(statistiche_home, home_file)

        # Plot dei grafici
        plot_grafici(df_goal, df_home)

# Avvio dello script
if __name__ == "__main__":
    main()
