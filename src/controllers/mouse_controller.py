import concurrent.futures as futures
import logging
import threading
import time
import tkinter as tk

import numpy as np
import numpy.typing as npt
import pyautogui

import src.utils as utils
from src.accel_graph import SigmoidAccel
from src.config_manager import ConfigManager
from src.singleton_meta import Singleton
from src.utils.one_euro_filter import OneEuroFilter2D

logger = logging.getLogger("MouseController")

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

# Número máximo de búfer para aplicar suavizado (legado, conservado para lógica de retardo).
N_BUFFER = 100

# Parámetros por defecto del filtro One Euro
DEFAULT_MIN_CUTOFF = 1.0    # Hz - menor = más suavizado cuando está quieto
DEFAULT_BETA = 0.007        # Coeficiente de velocidad - mayor = menos retardo al moverse
DEFAULT_D_CUTOFF = 1.0      # Hz - frecuencia de corte del filtro derivativo


class MouseController(metaclass=Singleton):

    def __init__(self):
        logger.info("Intialize MouseController singleton")
        self.prev_x = 0
        self.prev_y = 0
        self.curr_track_loc = None
        self.smooth_kernel = None
        self.one_euro_filter = None
        self.delay_count = 0
        self.top_count = 0
        self.is_started = False
        self.is_destroyed = False
        self.stop_flag = None
        # Bandera segura para hilos para el hilo de fondo
        self._active_flag = threading.Event()
        # Variable Tkinter para enlace de UI (usar únicamente desde el hilo principal)
        self.is_active = None

    def start(self):
        if not self.is_started:
            logger.info("Start MouseController singleton")
            # Búfer de puntos de seguimiento x, y (legado, conservado para Hamming)
            self.buffer = np.zeros([N_BUFFER, 2])
            self.accel = SigmoidAccel()
            self.pool = futures.ThreadPoolExecutor(max_workers=1)
            self.screen_w, self.screen_h = pyautogui.size()
            self.calc_smooth_kernel()

            # Inicializar el filtro One Euro
            config = ConfigManager().config
            t0 = time.time()
            self.one_euro_filter = OneEuroFilter2D(
                t0=t0, x0=0.0, y0=0.0,
                min_cutoff=config.get("one_euro_min_cutoff", DEFAULT_MIN_CUTOFF),
                beta=config.get("one_euro_beta", DEFAULT_BETA),
                d_cutoff=config.get("one_euro_d_cutoff", DEFAULT_D_CUTOFF)
            )
            logger.info("1 Euro Filter initialized for cursor smoothing")

            self.is_active = tk.BooleanVar()
            auto_play = ConfigManager().config["auto_play"]
            self.is_active.set(auto_play)
            if auto_play:
                self._active_flag.set()

            self.stop_flag = threading.Event()
            self.pool.submit(self.main_loop)
            self.is_started = True

    def reset_buffer(self, track_loc):
        if track_loc is not None:
            self.buffer[:] = track_loc
            self.prev_x, self.prev_y = track_loc
            self.delay_count = N_BUFFER  # Omitir retraso inicial
            # También restablecer el filtro One Euro para evitar saltos bruscos
            if self.one_euro_filter is not None:
                self.one_euro_filter.reset(
                    time.time(), float(track_loc[0]), float(track_loc[1]))

    def calc_smooth_kernel(self):
        new_pointer_smooth = ConfigManager().config["pointer_smooth"]
        if self.smooth_kernel is None:
            self.smooth_kernel = utils.calc_smooth_kernel(new_pointer_smooth)

        elif new_pointer_smooth != len(self.smooth_kernel):
            self.smooth_kernel = utils.calc_smooth_kernel(new_pointer_smooth)

        else:
            pass

    def asymmetry_scale(self, vel_x, vel_y):
        if vel_x > 0:
            vel_x *= ConfigManager().config["spd_right"]
        else:
            vel_x *= ConfigManager().config["spd_left"]

        if vel_y > 0:
            vel_y *= ConfigManager().config["spd_down"]
        else:
            vel_y *= ConfigManager().config["spd_up"]

        return vel_x, vel_y

    def act(self, track_loc: npt.ArrayLike):
        self.curr_track_loc = track_loc

    def main_loop(self) -> None:
        """Hilo separado para el controlador del ratón."""

        if self.is_destroyed:
            return

        loop_count = 0
        while not self.stop_flag.is_set():
            # Usar un Event seguro para hilos en lugar de tk.BooleanVar.get()
            if not self._active_flag.is_set():
                time.sleep(0.005)
                continue

            if self.curr_track_loc is None:
                time.sleep(0.005)
                continue

            # Aplicar el filtro One Euro para el suavizado adaptativo
            t_now = time.time()
            raw_x = float(self.curr_track_loc[0])
            raw_y = float(self.curr_track_loc[1])

            # Actualizar los parámetros del filtro One Euro desde la configuración si han cambiado
            config = ConfigManager().config
            self.one_euro_filter.update_params(
                min_cutoff=config.get("one_euro_min_cutoff", DEFAULT_MIN_CUTOFF),
                beta=config.get("one_euro_beta", DEFAULT_BETA)
            )

            smooth_px, smooth_py = self.one_euro_filter(t_now, raw_x, raw_y)

            vel_x = smooth_px - self.prev_x
            vel_y = smooth_py - self.prev_y

            self.prev_x = smooth_px
            self.prev_y = smooth_py

            # Estado de retardo (esperar a que el filtro se estabilice)
            self.delay_count += 1
            if self.delay_count < 10:
                time.sleep(0.001)
                continue

            vel_x, vel_y = self.asymmetry_scale(vel_x, vel_y)

            if config["mouse_acceleration"]:
                vel_x *= self.accel(vel_x)
                vel_y *= self.accel(vel_y)

            # Registro de diagnóstico (cada 200 iteraciones del bucle)
            loop_count += 1
            if loop_count % 200 == 0:
                logger.info(f"[DIAG] loop={loop_count} "
                            f"raw=({raw_x:.1f},{raw_y:.1f}) vel=({vel_x:.2f},{vel_y:.2f})")

            # pydirectinput no está funcionando aquí
            pyautogui.move(xOffset=vel_x, yOffset=vel_y)

            time.sleep(config["tick_interval_ms"] / 1000)

    def set_active(self, flag: bool, track_loc=None) -> None:
        # Actualizar la bandera segura para hilos
        if flag:
            self._active_flag.set()
        else:
            self._active_flag.clear()
        # Actualizar la variable de tkinter (para el interruptor de la UI)
        if self.is_active is not None:
            self.is_active.set(flag)
        if flag and track_loc is not None:
            self.reset_buffer(track_loc)

    def toggle_active(self, track_loc=None):
        logging.info("Toggle active")
        curr_state = self._active_flag.is_set()
        self.set_active(not curr_state, track_loc)

    def destroy(self):
        self._active_flag.clear()
        if self.is_active is not None:
            self.is_active.set(False)
        if self.stop_flag is not None:
            self.stop_flag.set()
        self.is_destroyed = True
