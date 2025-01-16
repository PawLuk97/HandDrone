"""
Modified by Pawel Lukowicz
pawellukowicz97@gmail.com
"""

import numpy as np
from numpy import pi
from hand_detecting_waypoints import hand_tracking
import tkinter as tk
from tkinter import simpledialog, messagebox

deg2rad = pi / 180.0

# Przechowywanie zmiennych globalnych
t_global, wp_global, yaw_global = None, None, None

def makeWaypoints():
    v_average = 1.6

    # Tworzymy okno główne Tkinter
    root = tk.Tk()
    root.geometry("300x300")  # Okno o rozmiarze 400x350
    root.title("Wybór parametrów trajektorii")  # Tytuł okna

    # Funkcja do zamknięcia okna po zatwierdzeniu
    def on_submit():
        global t_global, wp_global, yaw_global  # Używamy globalnych zmiennych

        try:
            mode = mode_var.get()
            param1 = int(param1_var.get())
            param2 = float(param2_var.get())
        except ValueError:
            messagebox.showerror("Błąd", "Proszę wprowadzić prawidłowe wartości.")
            return

        if mode not in ["time", "gestures"]:
            messagebox.showerror("Błąd", "Nieprawidłowy tryb! Wybierz 'time' lub 'gestures'.")
            return
        else:
            wp = hand_tracking(mode, param1, param2*-1)
            print(f"Wynik ręcznego śledzenia ({mode}): ", wp)

            # Normalizowanie wp
            wp = normalize_matrix(wp)
            print("Znormalizowana macierz wp: ", wp)

            yaw_ini = 0
            yaw = np.array([20, -90, 120, 45])

            t_ini = 3
            t = np.hstack((t_ini, np.array([2, 0, 2, 0]))).astype(float)
            wp = np.vstack((np.array([0, 0, 0]), wp)).astype(float)
            yaw = np.hstack((yaw_ini, yaw)).astype(float) * deg2rad

            # Przechowywanie wyników w zmiennych globalnych
            t_global, wp_global, yaw_global = t, wp, yaw

            # Zamknięcie okna po zatwierdzeniu
            root.quit()

    # Etykiety i pola wejściowe
    mode_label = tk.Label(root, text="Wybierz tryb:")
    mode_label.pack(pady=10)

    mode_var = tk.StringVar(value="time")
    mode_time_rb = tk.Radiobutton(root, text="Time", variable=mode_var, value="time")
    mode_gestures_rb = tk.Radiobutton(root, text="Gestures", variable=mode_var, value="gestures")
    mode_time_rb.pack()
    mode_gestures_rb.pack()

    param1_label = tk.Label(root, text="Podaj liczbę punktów trajektorii:")
    param1_label.pack(pady=10)
    param1_var = tk.StringVar()
    param1_entry = tk.Entry(root, textvariable=param1_var)
    param1_entry.pack()

    param2_label = tk.Label(root, text="Podaj wysokość wzniesienia:")
    param2_label.pack(pady=10)
    param2_var = tk.StringVar()
    param2_entry = tk.Entry(root, textvariable=param2_var)
    param2_entry.pack()

    # Przycisk do zatwierdzenia
    submit_button = tk.Button(root, text="Zatwierdź", command=on_submit)
    submit_button.pack(pady=20)

    root.mainloop()  # Uruchomienie głównej pętli Tkinter

    # Zwracanie wartości po zatwierdzeniu (zmienne globalne)
    return t_global, wp_global, yaw_global, v_average

# Funkcja normalizująca
def normalize_matrix(mat, new_min=-5, new_max=5):
    mat_to_normalize = mat[:-1, :2]  # Wybieramy tylko pierwsze dwie kolumny, z wyjątkiem ostatniego wiersza
    mat_min = mat_to_normalize.min()
    mat_max = mat_to_normalize.max()
    normalized_mat = ((mat_to_normalize - mat_min) / (mat_max - mat_min)) * (new_max - new_min) + new_min
    # Łączymy z ostatnim wierszem, pozostawiając go nienaruszonym
    mat[:-1, :2] = normalized_mat
    return mat
