import copy
import json
import logging
import shutil
import time
import tkinter as tk
from pathlib import Path

from src.singleton_meta import Singleton
from src.task_killer import TaskKiller
from src.utils.database import DatabaseManager

VERSION = "3.0"

DEFAULT_JSON = Path("configs/default.json")
BACKUP_PROFILE = Path("configs/default")

logger = logging.getLogger("ConfigManager")


# pyrefly: ignore [invalid-inheritance]
class ConfigManager(metaclass=Singleton):

    def __init__(self):
        logger.info("Intialize ConfigManager singleton")
        self.version = VERSION
        self.unsave_configs = False
        self.unsave_mouse_bindings = False
        self.unsave_keyboard_bindings = False
        self.config = None

        # Cargar configuración
        self.curr_profile_path = None
        self.curr_profile_name = tk.StringVar()
        self.is_started = False

        # Inicializar la base de datos SQLite
        self.db = DatabaseManager()
        
        # Realizar la migración automática al iniciar
        self._migrate_to_sqlite()

        self.profiles = self.list_profile()

    def _migrate_to_sqlite(self):
        """Migra automáticamente las configuraciones JSON del sistema de archivos a la base de datos SQLite si está vacía."""
        try:
            db_profiles = self.db.get_profiles()
            fs_profiles = []
            
            # Listar perfiles del sistema de archivos
            for path in DEFAULT_JSON.parent.glob("*"):
                if path.is_dir():
                    fs_profiles.append(path.name)
            
            logger.info(f"Flesystem profiles: {fs_profiles}. DB profiles: {db_profiles}")
            
            # Migrar cada perfil del sistema de archivos que aún no esté en SQLite
            for profile_name in fs_profiles:
                if profile_name not in db_profiles:
                    logger.info(f"Migrating profile '{profile_name}' to SQLite database...")
                    self.db.add_profile(profile_name)
                    
                    profile_dir = DEFAULT_JSON.parent / profile_name
                    
                    # 1. Migración de la configuración del cursor
                    cursor_file = profile_dir / "cursor.json"
                    if cursor_file.is_file():
                        with open(cursor_file) as f:
                            self.db.save_cursor_config(profile_name, json.load(f))
                            
                    # 2. Migración de las asignaciones de ratón
                    mouse_file = profile_dir / "mouse_bindings.json"
                    if mouse_file.is_file():
                        with open(mouse_file) as f:
                            self.db.save_bindings(profile_name, "mouse", json.load(f))
                            
                    # 3. Migración de las asignaciones de teclado
                    keyboard_file = profile_dir / "keyboard_bindings.json"
                    if keyboard_file.is_file():
                        with open(keyboard_file) as f:
                            self.db.save_bindings(profile_name, "keyboard", json.load(f))
                            
                    # 4. Migración de la configuración de voz
                    voice_file = profile_dir / "voice.json"
                    if voice_file.is_file():
                        with open(voice_file) as f:
                            self.db.save_voice_config(profile_name, json.load(f))
            logger.info("Automatic SQLite database migration check completed.")
        except Exception as e:
            logger.error(f"Error during SQLite database migration: {e}")

    def start(self):
        if not self.is_started:
            logger.info("Start ConfigManager singleton")
            if not DEFAULT_JSON.is_file():
                logger.critical(f"Missing {DEFAULT_JSON}, exit program...")
                TaskKiller().exit()

            try:
                with open(DEFAULT_JSON) as f:
                    self.load_profile(json.load(f)["default"])
            except Exception as e:
                logging.error(e)
                logging.error(
                    f"Failed to load default profile {DEFAULT_JSON}, using first profile instead."
                )
                self.load_profile(self.list_profile()[0])
            self.is_started = True

    def list_profile(self) -> list:
        # Cargar desde la base de datos SQLite para consistencia relacional
        profile_names = self.db.get_profiles()
        logger.info(f"Profiles loaded from SQLite: {profile_names}")
        return profile_names

    def remove_profile(self, profile_name):
        logger.info(f"Remove profile {profile_name}")
        # Eliminar de la base de datos SQLite
        self.db.delete_profile(profile_name)
        
        # Mantener el sistema de archivos sincronizado
        fs_path = Path(DEFAULT_JSON.parent, profile_name)
        if fs_path.is_dir():
            shutil.rmtree(fs_path)
            
        if profile_name in self.profiles:
            self.profiles.remove(profile_name)
        logger.info(f"Current profiles: {self.profiles}")

    def add_profile(self):
        # Nombre aleatorio basado en la marca de tiempo local
        new_profile_name = "profile_z" + str(hex(int(time.time() * 1000)))[2:]
        logger.info(f"Add profile {new_profile_name}")
        
        # Copiar asignaciones y configuraciones en la base de datos SQLite desde el respaldo
        self.db.add_profile(new_profile_name)
        self.db.save_cursor_config(new_profile_name, self.db.get_cursor_config("default"))
        self.db.save_bindings(new_profile_name, "mouse", self.db.get_bindings("default", "mouse"))
        self.db.save_bindings(new_profile_name, "keyboard", self.db.get_bindings("default", "keyboard"))
        self.db.save_voice_config(new_profile_name, self.db.get_voice_config("default"))
        
        # Mantener el sistema de archivos sincronizado
        shutil.copytree(BACKUP_PROFILE, Path(DEFAULT_JSON.parent, new_profile_name))
        
        self.profiles.append(new_profile_name)
        logger.info(f"Current profiles: {self.profiles}")

    def rename_profile(self, old_profile_name, new_profile_name):
        logger.info(f"Rename profile {old_profile_name} to {new_profile_name}")
        # Renombrar en SQLite
        self.db.rename_profile(old_profile_name, new_profile_name)
        
        # Renombrar en el sistema de archivos para respaldo
        old_path = Path(DEFAULT_JSON.parent, old_profile_name)
        new_path = Path(DEFAULT_JSON.parent, new_profile_name)
        if old_path.is_dir():
            shutil.move(old_path, new_path)
            
        if old_profile_name in self.profiles:
            self.profiles.remove(old_profile_name)
        self.profiles.append(new_profile_name)

        if self.curr_profile_name.get() == old_profile_name:
            self.curr_profile_name.set(new_profile_name)

    def load_profile(self, profile_name: str) -> None:
        profile_path = Path(DEFAULT_JSON.parent, profile_name)
        logger.info(f"Loading profile from SQLite: {profile_name}")

        # Asegurar que la base de datos lo contenga; recurrir a la carga de JSON si no se encuentra en la BD
        cursor_data = self.db.get_cursor_config(profile_name)
        if not cursor_data:
            # Recurrir a la migración del sistema de archivos
            self._migrate_to_sqlite()
            cursor_data = self.db.get_cursor_config(profile_name)

        self.config = cursor_data
        
        # Cargar plantilla por defecto como base de respaldo para evitar KeyErrors
        default_template = {
            "fix_width": 640,
            "fix_height": 480,
            "camera_id": 0,
            "tracking_vert_idxs": [1],
            "spd_up": 18.0,
            "spd_down": 22.0,
            "spd_left": 18.0,
            "spd_right": 18.0,
            "pointer_smooth": 6.0,
            "shape_smooth": 11,
            "tick_interval_ms": 8,
            "hold_trigger_ms": 250,
            "auto_play": True,
            "mouse_acceleration": True,
            "use_transformation_matrix": False,
            "one_euro_min_cutoff": 2.5,
            "one_euro_beta": 0.015,
            "one_euro_d_cutoff": 1.0
        }
        
        # Mezclar plantilla y datos reales para robustez total
        merged_config = copy.deepcopy(default_template)
        merged_config.update(cursor_data)
        self.config = merged_config

        self.mouse_bindings = self.db.get_bindings(profile_name, "mouse")
        self.keyboard_bindings = self.db.get_bindings(profile_name, "keyboard")

        self.temp_config = copy.deepcopy(self.config)
        self.temp_mouse_bindings = copy.deepcopy(self.mouse_bindings)
        self.temp_keyboard_bindings = copy.deepcopy(self.keyboard_bindings)

        self.curr_profile_path = profile_path
        self.curr_profile_name.set(profile_name)

    def switch_profile(self, profile_name: str):
        logger.info(f"Switching to profile: {profile_name}")
        self.load_profile(profile_name)
        with open(DEFAULT_JSON, "w") as f:
            json.dump({"default": profile_name}, f)

    # ------------------------------- CONFIGURACIÓN BÁSICA ------------------------------- #

    def set_temp_config(self, field: str, value):
        logger.info(f"Setting {field} to {value}")
        self.temp_config[field] = value
        self.unsave_configs = True

    def write_config_file(self):
        # Escribir en SQLite
        self.db.save_cursor_config(self.curr_profile_name.get(), self.config)
        
        # Escribir respaldo en el archivo
        cursor_config_file = Path(self.curr_profile_path, "cursor.json")
        logger.info(f"Writing backup config file {cursor_config_file}")
        with open(cursor_config_file, 'w') as f:
            json.dump(self.config, f, indent=4, separators=(', ', ': '))

    def apply_config(self):
        logger.info("Applying config")
        self.config = copy.deepcopy(self.temp_config)
        self.write_config_file()
        self.unsave_configs = False

    # ------------------------------ CONFIGURACIÓN DE ASIGNACIONES DE RATÓN ----------------------------- #

    def set_temp_mouse_binding(self, gesture, device: str, action: str,
                               threshold: float, trigger_type: str):

        logger.info(
            "setting keybind for gesture: %s, device: %s, key: %s, threshold: %s, trigger_type: %s",
            gesture, device, action, threshold, trigger_type)

        # Eliminar asignaciones de teclas duplicadas
        self.remove_temp_mouse_binding(device, action)
        # ¡También eliminar este gesto de las asignaciones de teclado para evitar conflictos!
        self.remove_temp_keyboard_binding(device="keyboard", gesture=gesture)

        # Asignar
        self.temp_mouse_bindings[gesture] = [
            device, action, float(threshold), trigger_type
        ]
        self.unsave_mouse_bindings = True

    def remove_temp_mouse_binding(self, device: str, action: str, gesture: str = "None"):
        logger.info(
            f"remove_temp_mouse_binding for device: {device}, key: {action} or gesture: {gesture}")
        out_keybinds = {}
        for key, vals in self.temp_mouse_bindings.items():
            if gesture == key:
                continue
            if (device == vals[0]) and (action == vals[1]):
                continue
            out_keybinds[key] = vals
        self.temp_mouse_bindings = out_keybinds
        self.unsave_mouse_bindings = True

    def apply_mouse_bindings(self):
        logger.info("Applying keybinds")
        self.mouse_bindings = copy.deepcopy(self.temp_mouse_bindings)
        self.write_mouse_bindings_file()
        self.unsave_mouse_bindings = False

    def write_mouse_bindings_file(self):
        # Escribir en SQLite
        self.db.save_bindings(self.curr_profile_name.get(), "mouse", self.mouse_bindings)
        
        # Escribir respaldo en el archivo
        mouse_bindings_file = Path(self.curr_profile_path, "mouse_bindings.json")
        logger.info(f"Writing backup keybinds file {mouse_bindings_file}")
        with open(mouse_bindings_file, 'w') as f:
            out_json = dict(sorted(self.mouse_bindings.items()))
            json.dump(out_json, f, indent=4, separators=(', ', ': '))

    # ------------------------------ CONFIGURACIÓN DE ASIGNACIONES DE TECLADO ----------------------------- #

    def set_temp_keyboard_binding(self, device: str, key_action: str,
                                  gesture: str, threshold: float,
                                  trigger_type: str):
        logger.info(
            "setting keybind for gesture: %s, device: %s, key: %s, threshold: %s, trigger_type: %s",
            gesture, device, key_action, threshold, trigger_type)

        # Eliminar asignaciones de teclas duplicadas
        self.remove_temp_keyboard_binding(device, key_action, gesture)
        # ¡También eliminar este gesto de las asignaciones de ratón para evitar conflictos!
        self.remove_temp_mouse_binding(device="mouse", action="None", gesture=gesture)

        # Asignar
        self.temp_keyboard_bindings[gesture] = [
            device, key_action,
            float(threshold), trigger_type
        ]
        self.unsave_keyboard_bindings = True

    def remove_temp_keyboard_binding(self,
                                     device: str,
                                     key_action: str = "None",
                                     gesture: str = "None"):
        logger.info(
            f"remove_temp_keyboard_binding for device: {device}, key: {key_action} or gesture {gesture}"
        )

        out_keybinds = {}
        for ges, vals in self.temp_keyboard_bindings.items():
            if (gesture == ges):
                continue
            if (key_action == vals[1]):
                continue

            out_keybinds[ges] = vals

        self.temp_keyboard_bindings = out_keybinds
        self.unsave_keyboard_bindings = True

    def apply_keyboard_bindings(self):
        logger.info("Applying keyboard bindings")
        self.keyboard_bindings = copy.deepcopy(self.temp_keyboard_bindings)
        self.write_keyboard_bindings_file()
        self.unsave_keyboard_bindings = False

    def write_keyboard_bindings_file(self):
        # Escribir en SQLite
        self.db.save_bindings(self.curr_profile_name.get(), "keyboard", self.keyboard_bindings)
        
        # Escribir respaldo en el archivo
        keyboard_bindings_file = Path(self.curr_profile_path, "keyboard_bindings.json")
        logger.info(f"Writing backup keyboard bindings file {keyboard_bindings_file}")
        with open(keyboard_bindings_file, 'w') as f:
            out_json = dict(sorted(self.keyboard_bindings.items()))
            json.dump(out_json, f, indent=4, separators=(', ', ': '))

    # ------------------------------ CONFIGURACIÓN DE VOZ ----------------------------- #

    def get_voice_config(self) -> dict:
        # Cargar principalmente desde SQLite
        voice_data = self.db.get_voice_config(self.curr_profile_name.get())
        if voice_data:
            return voice_data
            
        # Recurrir a los valores por defecto
        return {
            "enabled": True,
            "language": "es-ES",
            "microphone_id": 0,
            "confidence_threshold": 0.5,
            "voice_sensitivity": 50,
            "auto_type": True,
            "confirmation_required": False,
            "pause_during_cursor": True,
            "speech_timeout_ms": 5000,
            "voice_feedback": True
        }

    def update_voice_config(self, updates: dict):
        # Obtener configuración actual
        current_config = self.get_voice_config()
        # Actualizar con los nuevos valores
        current_config.update(updates)
        
        # Guardar en SQLite
        self.db.save_voice_config(self.curr_profile_name.get(), current_config)
        
        # Escribir respaldo en el archivo
        voice_config_file = Path(self.curr_profile_path, "voice.json")
        try:
            with open(voice_config_file, 'w') as f:
                json.dump(current_config, f, indent=4, separators=(',', ': '))
            logger.info(f"Voice config backup updated: {updates}")
        except Exception as e:
            logger.error(f"Error writing voice config backup: {e}")
            
        # Notificar al singleton VoiceController en tiempo real
        try:
            from src.controllers.voice_controller import VoiceController
            VoiceController().update_config(current_config)
        except Exception as e:
            logger.error(f"Error notifying VoiceController of update: {e}")

    # ---------------------------------------------------------------------------- #
    def apply_all(self):
        self.apply_config()
        self.apply_mouse_bindings()
        self.apply_keyboard_bindings()

    def destroy(self):
        logger.info("Destroy")
