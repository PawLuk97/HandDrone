# -*- coding: utf-8 -*-
"""
author: John Bass
email: john.bobzwik@gmail.com
license: MIT
Please feel free to use and modify this, but keep the above information. Thanks!
"""

"""
Modified by Pawel Lukowicz
pawellukowicz97@gmail.com
"""

import numpy as np
import matplotlib.pyplot as plt
import time
import tkinter as tk
from tkinter import ttk
import cProfile

from trajectory import Trajectory
from ctrl import Control
from quadFiles.quad import Quadcopter
from utils.windModel import Wind
import utils
import config


def quad_sim(t, Ts, quad, ctrl, wind, traj):
    # Dynamics (using last timestep's commands)
    # ---------------------------
    quad.update(t, Ts, ctrl.w_cmd, wind)
    t += Ts

    # Trajectory for Desired States
    # ---------------------------
    sDes = traj.desiredState(t, Ts, quad)

    # Generate Commands (for next iteration)
    # ---------------------------
    ctrl.controller(traj, quad, sDes, Ts)

    return t


def get_traj_select_from_user():
    """Display a Tkinter window to get user input for trajSelect[0]."""
    options = {
        0: "Hover",
        1: "Position Waypoint Timed",
        2: "Position Waypoint Interpolated",
        3: "Minimum Velocity",
        4: "Minimum Acceleration",
        5: "Minimum Jerk",
        6: "Minimum Snap",
        7: "Minimum Acceleration Stop",
        8: "Minimum Jerk Stop",
        9: "Minimum Snap Stop",
        10: "Minimum Jerk Full Stop",
        11: "Minimum Snap Full Stop",
        12: "Position Waypoint Arrived",
        13: "Position Waypoint Arrived and Wait"
    }

    def submit():
        nonlocal selected_option
        selected_option = int(combo.get().split(" - ")[0])
        root.destroy()

    root = tk.Tk()
    root.title("Ustawienia")
    root.geometry("400x150")

    label = tk.Label(root, text="Wybierz typ trajektorii:", font=("Arial", 12))
    label.pack(pady=10)

    combo = ttk.Combobox(root, state="readonly", font=("Arial", 10), width=35)
    combo['values'] = [f"{key} - {value}" for key, value in options.items()]
    combo.current(8)  # Default to option 8 ("Minimum Jerk Stop")
    combo.pack(pady=10)

    button = tk.Button(root, text="Zatwierdź", command=submit, font=("Arial", 10))
    button.pack(pady=10)

    selected_option = 8  # Default value
    root.mainloop()

    return selected_option


def get_wind_params_from_user():
    """Display a Tkinter window to get user input for wind parameters."""
    wind_types = ['None', 'Sine', 'RandomSine', 'Fixed']

    root = tk.Tk()  # Tworzymy okno GUI jako pierwsze
    root.title("Ustawienia wiatru")
    root.geometry("400x320")

    selected_wind_type = tk.StringVar(value='None')  # Teraz możemy utworzyć zmienną powiązaną z oknem

    selected_wind = None  # Inicjalizujemy zmienną selected_wind

    def submit():
        nonlocal selected_wind
        wind_type = selected_wind_type.get()
        if wind_type == 'Sine':
            wind_params = [float(velW_entry.get()), float(qW1_entry.get()), float(qW2_entry.get())]
            selected_wind = Wind('Sine', *wind_params)
        elif wind_type == 'RandomSine':
            wind_params = [float(velW_entry.get()), float(qW1_entry.get()), float(qW2_entry.get())]
            selected_wind = Wind('RandomSine', *wind_params)
        elif wind_type == 'Fixed':
            wind_params = [float(velW_entry.get()), float(qW1_entry.get()), float(qW2_entry.get())]
            selected_wind = Wind('Fixed', *wind_params)
        else:
            selected_wind = Wind('None', 2.0, 90, -15)
        root.destroy()

    label = tk.Label(root, text="Wybierz typ wiatru:", font=("Arial", 12))
    label.pack(pady=10)

    wind_type_menu = ttk.Combobox(root, textvariable=selected_wind_type, values=wind_types, state="readonly",
                                  font=("Arial", 10))
    wind_type_menu.pack(pady=10)

    label = tk.Label(root, text="Prędkość wiatru (m/s):", font=("Arial", 10))
    label.pack(pady=5)

    velW_entry = tk.Entry(root, font=("Arial", 10))
    velW_entry.insert(0, "2.0")  # Domyślna wartość
    velW_entry.pack(pady=5)

    label = tk.Label(root, text="Kąt wiatru (deg) - Heading:", font=("Arial", 10))
    label.pack(pady=5)

    qW1_entry = tk.Entry(root, font=("Arial", 10))
    qW1_entry.insert(0, "90")  # Domyślna wartość
    qW1_entry.pack(pady=5)

    label = tk.Label(root, text="Kąt wiatru (deg) - Elevation:", font=("Arial", 10))
    label.pack(pady=5)

    qW2_entry = tk.Entry(root, font=("Arial", 10))
    qW2_entry.insert(0, "-15")  # Domyślna wartość
    qW2_entry.pack(pady=5)

    button = tk.Button(root, text="Zatwierdź", command=submit, font=("Arial", 10))
    button.pack(pady=10)

    root.mainloop()  # Uruchamiamy główną pętlę GUI

    return selected_wind


def main():
    start_time = time.time()

    # Simulation Setup
    # ---------------------------
    Ti = 0
    Ts = 0.005
    Tf = 40
    ifsave = 0

    # Choose trajectory settings
    # ---------------------------
    ctrlOptions = ["xyz_pos", "xy_vel_z_pos", "xyz_vel"]
    trajSelect = np.zeros(3)

    # Select Control Type             (0: xyz_pos, 1: xy_vel_z_pos, 2: xyz_vel)
    ctrlType = ctrlOptions[0]

    # Get trajSelect[0] from user via Tkinter
    trajSelect[0] = get_traj_select_from_user()

    # Select Yaw Trajectory Type      (0: none, 1: yaw_waypoint_timed, 2: yaw_waypoint_interp, 3: follow, 4: zero)
    trajSelect[1] = 3

    # Select if waypoint time is used, or if average speed is used to calculate waypoint time (0: waypoint time, 1: average speed)
    trajSelect[2] = 1

    print("Control type: {}".format(ctrlType))

    # Get Wind Parameters from user
    # ---------------------------
    wind = get_wind_params_from_user()

    # Initialize Quadcopter, Controller, Wind, Result Matrixes
    # ---------------------------
    quad = Quadcopter(Ti)
    traj = Trajectory(quad, ctrlType, trajSelect)
    ctrl = Control(quad, traj.yawType)

    # Trajectory for First Desired States
    # ---------------------------
    sDes = traj.desiredState(0, Ts, quad)

    # Generate First Commands
    # ---------------------------
    ctrl.controller(traj, quad, sDes, Ts)

    # Initialize Result Matrixes
    # ---------------------------
    numTimeStep = int(Tf / Ts + 1)

    t_all = np.zeros(numTimeStep)
    s_all = np.zeros([numTimeStep, len(quad.state)])
    pos_all = np.zeros([numTimeStep, len(quad.pos)])
    vel_all = np.zeros([numTimeStep, len(quad.vel)])
    quat_all = np.zeros([numTimeStep, len(quad.quat)])
    omega_all = np.zeros([numTimeStep, len(quad.omega)])
    euler_all = np.zeros([numTimeStep, len(quad.euler)])
    sDes_traj_all = np.zeros([numTimeStep, len(traj.sDes)])
    sDes_calc_all = np.zeros([numTimeStep, len(ctrl.sDesCalc)])
    w_cmd_all = np.zeros([numTimeStep, len(ctrl.w_cmd)])
    wMotor_all = np.zeros([numTimeStep, len(quad.wMotor)])
    thr_all = np.zeros([numTimeStep, len(quad.thr)])
    tor_all = np.zeros([numTimeStep, len(quad.tor)])

    t_all[0] = Ti
    s_all[0, :] = quad.state
    pos_all[0, :] = quad.pos
    vel_all[0, :] = quad.vel
    quat_all[0, :] = quad.quat
    omega_all[0, :] = quad.omega
    euler_all[0, :] = quad.euler
    sDes_traj_all[0, :] = traj.sDes
    sDes_calc_all[0, :] = ctrl.sDesCalc
    w_cmd_all[0, :] = ctrl.w_cmd
    wMotor_all[0, :] = quad.wMotor
    thr_all[0, :] = quad.thr
    tor_all[0, :] = quad.tor

    # Run Simulation
    # ---------------------------
    t = Ti
    i = 1
    while round(t, 3) < Tf:
        t = quad_sim(t, Ts, quad, ctrl, wind, traj)

        t_all[i] = t
        s_all[i, :] = quad.state
        pos_all[i, :] = quad.pos
        vel_all[i, :] = quad.vel
        quat_all[i, :] = quad.quat
        omega_all[i, :] = quad.omega
        euler_all[i, :] = quad.euler
        sDes_traj_all[i, :] = traj.sDes
        sDes_calc_all[i, :] = ctrl.sDesCalc
        w_cmd_all[i, :] = ctrl.w_cmd
        wMotor_all[i, :] = quad.wMotor
        thr_all[i, :] = quad.thr
        tor_all[i, :] = quad.tor

        i += 1

    end_time = time.time()
    print("Simulated {:.2f}s in {:.6f}s.".format(t, end_time - start_time))

    # View Results
    # ---------------------------

    ani = utils.sameAxisAnimation(t_all, traj.wps, pos_all, quat_all, sDes_traj_all, Ts, quad.params, traj.xyzType,
                                  traj.yawType, ifsave)


if __name__ == "__main__":
    if (config.orient == "NED" or config.orient == "ENU"):
        main()
    else:
        raise Exception("{} is not a valid orientation. Verify config.py file.".format(config.orient))
