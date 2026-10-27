import tkinter as tk

def button(go):
    # Variabile globale per tenere traccia dello stato
    torna_a_casa_selezionato = False

    def torna_a_casa():
        nonlocal torna_a_casa_selezionato  # Permette di modificare la variabile definita fuori dalla funzione
        # Cambia lo stato della variabile globale
        torna_a_casa_selezionato = True
        print("Il paziente ha scelto: Torna a casa.")
        print(f"Variabile torna_a_casa_selezionato: {torna_a_casa_selezionato}")
        label_feedback.config(text="Il robot sta tornando alla base.")
        
        # Dopo un breve ritardo, termina il ciclo Tkinter, chiudendo la finestra
        root.after(500, root.quit)  # Ritarda la chiusura di mezzo secondo per far vedere il messaggio

    # Creazione della finestra principale
    root = tk.Tk()
    root.title("Interfaccia Robot")
    root.geometry("300x150")
    root.resizable(False, False)

    # Etichetta per istruzioni
    label_instruction = tk.Label(root, text="Cosa vuoi che faccia il robot?", font=("Arial", 14))
    label_instruction.pack(pady=10)

    # Pulsante "Torna a casa"
    button_torna = tk.Button(root, text="Torna a casa", font=("Arial", 12), bg="lightblue", command=torna_a_casa)
    button_torna.pack(pady=5, fill=tk.X, padx=20)

    # Etichetta per feedback
    label_feedback = tk.Label(root, text="", font=("Arial", 12), fg="darkgreen")
    label_feedback.pack(pady=10)

    # Avvio del loop principale di Tkinter
    if go:
        root.mainloop()

    # Restituisce il valore della variabile, che è stato cambiato se il bottone è stato premuto
    return torna_a_casa_selezionato


# Main 

# Esegui la funzione e ottieni il valore di ritorno
# result = button()
# print(f"Stato finale del robot: {result}")
