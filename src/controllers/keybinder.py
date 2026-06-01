import copy
import logging
import math
import time

import pydirectinput
import win32api

import src.shape_list as shape_list
from src.config_manager import ConfigManager
from src.controllers.mouse_controller import MouseController
from src.controllers.facial_event_manager import FacialEventManager
from src.utils.database import DatabaseManager
from src.singleton_meta import Singleton

logger = logging.getLogger("Keybinder")

# Desactivar retardo para máxima responsividad
pydirectinput.PAUSE = 0
pydirectinput.FAILSAFE = False


# pyrefly: ignore [invalid-inheritance]
class Keybinder(metaclass=Singleton):

    def __init__(self) -> None:
        logger.info("Intialize Keybinder singleton")
        self.top_count = 0
        self.triggered = False
        self.start_hold_ts = math.inf
        self.holding = False
        self.is_started = False
        self.last_know_keybinds = {}

    def start(self):
        if not self.is_started:
            logger.info("Start Keybinder singleton")
            self.init_states()
            self.screen_w, self.screen_h = pydirectinput.size()
            self.monitors = self.get_monitors()
            self.is_started = True

    def init_states(self) -> None:
        """Reinicializa el estado del keybinder si se añaden nuevas asignaciones de teclas."""
        # Mantener los estados de todas las teclas registradas
        self.key_states = {}
        for _, v in (ConfigManager().mouse_bindings |
                     ConfigManager().keyboard_bindings).items():
            self.key_states[v[0] + "_" + v[1]] = False
        self.key_states["holding"] = False
        self.last_know_keybinds = copy.deepcopy(
            (ConfigManager().mouse_bindings |
             ConfigManager().keyboard_bindings))

    def get_monitors(self) -> list[dict]:
        out_list = []
        monitors = win32api.EnumDisplayMonitors()
        for i, (_, _, loc) in enumerate(monitors):
            mon_info = {}
            mon_info["id"] = i
            mon_info["x1"] = loc[0]
            mon_info["y1"] = loc[1]
            mon_info["x2"] = loc[2]
            mon_info["y2"] = loc[3]
            mon_info["center_x"] = (loc[0] + loc[2]) // 2
            mon_info["center_y"] = (loc[1] + loc[3]) // 2
            out_list.append(mon_info)

        return out_list

    def get_curr_monitor(self):
        x, y = pydirectinput.position()
        for mon_id, mon in enumerate(self.monitors):
            if x >= mon["x1"] and x <= mon["x2"] and y >= mon[
                    "y1"] and y <= mon["y2"]:
                return mon_id
        return 0

    def mouse_action(self, is_triggered, is_stable_active, action, mode) -> None:
        state_name = "mouse_" + action

        if mode == "hold":
            if is_stable_active and (self.key_states[state_name] is False):
                pydirectinput.mouseDown(button=action)
                self.key_states[state_name] = True
                
                # Notificar a la sesión de investigación (si está activa)
                self._log_research_event("click_hold_start", action)
                
            elif (not is_stable_active) and (self.key_states[state_name] is True):
                pydirectinput.mouseUp(button=action)
                self.key_states[state_name] = False
                
                self._log_research_event("click_hold_end", action)

        elif mode == "single":
            if is_triggered:
                pydirectinput.click(button=action)
                self.start_hold_ts = time.time()
                self.key_states[state_name] = True
                
                # Notificar a la sesión de investigación
                self._log_research_event("click", action)

                if not self.holding and (
                    ((time.time() - self.start_hold_ts) * 1000) >=
                        ConfigManager().config["hold_trigger_ms"]):
                    pydirectinput.mouseDown(button=action)
                    self.holding = True

            elif (not is_stable_active) and (self.key_states[state_name] is True):
                self.key_states[state_name] = False

                if self.holding:
                    pydirectinput.mouseUp(button=action)
                    self.holding = False
                    self.start_hold_ts = math.inf

    def keyboard_action(self, is_triggered, is_stable_active, keysym, mode):
        keysym = keysym.lower()
        state_name = "keyboard_" + keysym

        import pyautogui
        if mode == "hold":
            if is_stable_active and (self.key_states[state_name] is False):
                try:
                    pyautogui.keyDown(keysym)
                except Exception:
                    import pydirectinput
                    pydirectinput.keyDown(keysym)
                self.key_states[state_name] = True
                self._log_research_event("key_hold_start", keysym)
            elif (not is_stable_active) and (self.key_states[state_name] is True):
                try:
                    pyautogui.keyUp(keysym)
                except Exception:
                    import pydirectinput
                    pydirectinput.keyUp(keysym)
                self.key_states[state_name] = False
                self._log_research_event("key_hold_end", keysym)
        else: # pulsación única
            if is_triggered:
                try:
                    pyautogui.press(keysym)
                except Exception:
                    import pydirectinput
                    pydirectinput.press(keysym)
                self._log_research_event("keystroke", keysym)

    def _log_research_event(self, event_type: str, action: str):
        """Registra eventos de activación de acciones en la sesión de investigación activa."""
        try:
            from src.gui.pages.page_home import PageHome
            home_page = PageHome.get_instance()
            if home_page and home_page.is_recording:
                x, y = pydirectinput.position()
                DatabaseManager().log_research_event(
                    session_id=home_page.session_id,
                    event_type=event_type,
                    gesture_name=action,
                    cursor_x=x,
                    cursor_y=y
                )
                if event_type == "click":
                    home_page.total_clicks += 1
                elif event_type == "keystroke":
                    home_page.total_keystrokes += 1
        except Exception as e:
            logger.error(f"Error al registrar la telemetría científica: {e}")

    def act(self, blendshape_values, track_loc=None) -> dict:
        """Dispara acciones de dispositivos basadas en los valores de blendshapes.

        Args:
            blendshape_values: Valores de blendshapes del modelo facial.
            track_loc: Ubicación del punto de seguimiento de la malla facial.

        Returns:
            dict: Estados de depuración.
        """

        if blendshape_values is None:
            return

        if (ConfigManager().mouse_bindings |
                ConfigManager().keyboard_bindings) != self.last_know_keybinds:
            self.init_states()

        event_manager = FacialEventManager()

        for shape_name, v in (ConfigManager().mouse_bindings |
                              ConfigManager().keyboard_bindings).items():
            if shape_name not in shape_list.blendshape_names:
                continue
            device, action, thres, mode = v

            # Obtener el valor del blendshape
            idx = shape_list.blendshape_indices[shape_name]
            val = blendshape_values[idx]

            # Filtrar el gesto usando el FacialEventManager con estado (Anti-Midas Touch)
            is_triggered = event_manager.filter_gesture(shape_name, val, thres)
            is_stable_active = event_manager.get_gesture_state(shape_name)["is_active"]

            if (device == "mouse") and (action == "pause"):
                state_name = "mouse_" + action

                if is_triggered and (self.key_states[state_name] is False):
                    MouseController().toggle_active(track_loc)
                    self.key_states[state_name] = True
                    self._log_research_event("pause_toggle", "pause")
                elif (not is_stable_active) and (self.key_states[state_name] is True):
                    self.key_states[state_name] = False

            elif MouseController()._active_flag.is_set():

                if device == "mouse":

                    if action == "reset":
                        state_name = "mouse_" + action
                        if is_triggered and (self.key_states[state_name] is False):
                            mon_id = self.get_curr_monitor()
                            if mon_id is None:
                                return

                            pydirectinput.moveTo(
                                self.monitors[mon_id]["center_x"],
                                self.monitors[mon_id]["center_y"])
                            self.key_states[state_name] = True
                            self._log_research_event("reset_position", "reset")
                        elif (not is_stable_active) and (self.key_states[state_name] is True):
                            self.key_states[state_name] = False

                    elif action == "cycle":
                        state_name = "mouse_" + action
                        if is_triggered and (self.key_states[state_name] is False):
                            mon_id = self.get_curr_monitor()
                            next_mon_id = (mon_id + 1) % len(self.monitors)
                            pydirectinput.moveTo(
                                self.monitors[next_mon_id]["center_x"],
                                self.monitors[next_mon_id]["center_y"])
                            self.key_states[state_name] = True
                            self._log_research_event("cycle_monitor", "cycle")
                        elif (not is_stable_active) and (self.key_states[state_name] is True):
                            self.key_states[state_name] = False

                    else:
                        self.mouse_action(is_triggered, is_stable_active, action, mode)

                elif device == "keyboard":
                    self.keyboard_action(is_triggered, is_stable_active, action, mode)

    def destroy(self):
        """Destruir el keybinder."""
        return
