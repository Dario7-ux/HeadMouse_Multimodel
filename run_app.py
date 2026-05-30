import os
import sys
import shutil
import logging

# Configurar el registro (logging) temprano
FORMAT = "%(asctime)s %(levelname)s %(name)s: %(funcName)s: %(message)s"
logging.basicConfig(format=FORMAT,
                    level=logging.INFO,
                    handlers=[
                        logging.FileHandler("log.txt", mode='w'),
                        logging.StreamHandler(sys.stdout)
                    ])

# --- Ayudante para rutas dinámicas en PyInstaller ---
def get_resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Monkeypatch (parche dinámico) de PIL.Image.open y cv2.imread para carga de recursos ---
try:
    from PIL import Image
    original_open = Image.open

    def patched_open(fp, mode="r", formats=None):
        if isinstance(fp, str) and fp.startswith("assets"):
            fp = get_resource_path(fp)
        return original_open(fp, mode, formats)

    Image.open = patched_open
    logging.info("Successfully monkeypatched PIL.Image.open")
except Exception as e:
    logging.error(f"Failed to monkeypatch PIL.Image.open: {e}")

try:
    import cv2
    original_imread = cv2.imread

    def patched_imread(filename, flags=None):
        if isinstance(filename, str) and filename.startswith("assets"):
            filename = get_resource_path(filename)
        if flags is not None:
            return original_imread(filename, flags)
        return original_imread(filename)

    cv2.imread = patched_imread
    logging.info("Successfully monkeypatched cv2.imread")
except Exception as e:
    logging.error(f"Failed to monkeypatch cv2.imread: {e}")

# --- Inicializar la carpeta configs local desde la plantilla si falta ---
configs_dir = os.path.abspath("configs")
if not os.path.isdir(configs_dir):
    logging.info("configs folder not found in workspace, trying to copy templates...")
    internal_configs = get_resource_path("configs")
    if os.path.isdir(internal_configs) and internal_configs != configs_dir:
        try:
            shutil.copytree(internal_configs, configs_dir)
            logging.info("Successfully initialized local configs folder from bundle.")
        except Exception as e:
            logging.error(f"Error copying configs templates: {e}")
    else:
        # Crear simplemente el directorio vacío si no hay nada que copiar
        os.makedirs(configs_dir, exist_ok=True)
else:
    # Asegurar que las plantillas default.json y default/ existan incluso si configs ya existe (seguridad de respaldo)
    default_json = os.path.join(configs_dir, "default.json")
    if not os.path.exists(default_json):
        internal_default_json = get_resource_path("configs/default.json")
        if os.path.exists(internal_default_json):
            try:
                shutil.copy(internal_default_json, default_json)
                logging.info("Copied missing default.json template.")
            except Exception as e:
                logging.error(f"Error copying default.json: {e}")
                
    default_subdir = os.path.join(configs_dir, "default")
    if not os.path.isdir(default_subdir):
        internal_default_subdir = get_resource_path("configs/default")
        if os.path.isdir(internal_default_subdir):
            try:
                shutil.copytree(internal_default_subdir, default_subdir)
                logging.info("Copied missing configs/default subdirectory.")
            except Exception as e:
                logging.error(f"Error copying configs/default directory: {e}")

import customtkinter
import src.gui as gui
from src.pipeline import Pipeline
from src.task_killer import TaskKiller


class MainApp(gui.MainGui, Pipeline):

    def __init__(self, tk_root):
        # Inicializar la GUI y la Tubería (Pipeline)
        super().__init__(tk_root)
        Pipeline.__init__(self)
        
        self.tk_root.wm_protocol("WM_DELETE_WINDOW", self.close_all)

        # Iniciar el procesamiento de video y el hilo de fondo de control del cursor de inmediato
        self.start()

    def close_all(self):
        logging.info("Close all")
        # Guardar automáticamente la hora de finalización si la sesión de investigación está activa
        try:
            page_home = self.pages.get("page_home")
            if page_home and getattr(page_home, "is_recording", False):
                logging.info("Auto-ending research session on close_all protocol.")
                page_home.end_active_session()
        except Exception as e:
            logging.error(f"Error saving research session on closing: {e}")

        # Detener limpiamente el hilo de fondo antes de salir
        self.stop()
        # Cerrar completamente este proceso
        TaskKiller().exit()


if __name__ == "__main__":
    tk_root = customtkinter.CTk()

    logging.info("Starting main app.")
    TaskKiller().start()

    main_app = MainApp(tk_root)
    main_app.tk_root.mainloop()

    main_app = None
