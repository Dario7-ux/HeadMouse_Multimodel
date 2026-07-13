import logging
import threading
import time
import json
import os
import pynput.keyboard as keyboard
import pyaudio
import pyautogui
import numpy as np

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

from src.singleton_meta import Singleton
from src.utils.database import DatabaseManager

try:
    from vosk import Model, KaldiRecognizer
except ImportError:
    logger = logging.getLogger("VoiceController")
    logger.error("Vosk no está instalado. Ejecute: pip install -r requirements.txt")
    Model = None
    KaldiRecognizer = None

from src.utils.resource_helper import get_resource_path

logger = logging.getLogger("VoiceController")

# Ruta del modelo de Vosk
VOSK_MODEL_PATH = get_resource_path("assets/models/vosk-model-es-0.42")
class TempResetDLLDirectory:
    """Context manager to temporarily reset the DLL search directory on Windows.
    This prevents child processes from inheriting PyInstaller's internal search path
    and failing due to DLL conflicts.
    """
    def __enter__(self):
        import sys
        self.meipass = getattr(sys, '_MEIPASS', None)
        if self.meipass:
            try:
                import ctypes
                ctypes.windll.kernel32.SetDllDirectoryW(None)
            except Exception:
                pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.meipass:
            try:
                import ctypes
                ctypes.windll.kernel32.SetDllDirectoryW(self.meipass)
            except Exception:
                pass


# pyrefly: ignore [invalid-inheritance]
class VoiceController(metaclass=Singleton):
    """Controlador para el reconocimiento de voz utilizando Vosk (fuera de línea), dictado de voz y escritura automática."""

    def __init__(self):
        logger.info("Initialize VoiceController singleton")
        self.is_active = False
        self.config = {}
        self.keyboard_controller = keyboard.Controller()
        self.recognized_text = ""
        self._thread = None
        self._ui_callback = None  # Callback seguro para actualizar la interfaz de usuario
        self.vosk_model = None
        self.audio_stream = None
        self.p_audio = None
        self._lock = threading.Lock()
        import queue
        self.tts_queue = queue.Queue()
        self.tts_thread = None

    def start(self):
        """Iniciar el controlador de voz y su hilo de escucha en segundo plano."""
        logger.info("Start VoiceController singleton")
        self.is_active = True
        
        # Iniciar hilo de trabajo TTS dedicado libre de bloqueos mutuos (deadlocks)
        self._start_tts_worker()
        
        # Cargar la configuración más reciente si no está poblada
        if not self.config:
            from src.config_manager import ConfigManager
            self.config = ConfigManager().get_voice_config()

        if self.is_enabled():
            self._start_listening_thread()

    def stop(self):
        """Detener el controlador de voz y finalizar el hilo de escucha en segundo plano."""
        logger.info("Stop VoiceController singleton")
        self.is_active = False
        self._thread = None
        self._cleanup_audio()

    def _start_tts_worker(self):
        """Inicia un hilo de trabajo dedicado único para la retroalimentación de texto a voz (TTS).
        
        Esto evita que se ejecuten múltiples instancias de pyttsx3 en hilos separados,
        lo cual es la causa raíz de los conflictos de estado de apartamento COM y congelamientos fatales de la aplicación en Windows.
        """
        if self.tts_thread is not None and self.tts_thread.is_alive():
            return

        def _tts_loop():
            import pythoncom
            pythoncom.CoInitialize()
            try:
                import pyttsx3
                import queue
                engine = pyttsx3.init()
                while self.is_active:
                    try:
                        # Extracción no bloqueante con un pequeño tiempo de espera para que el hilo pueda salir limpiamente cuando is_active sea False
                        msg = self.tts_queue.get(timeout=0.5)
                        engine.say(msg)
                        engine.runAndWait()
                        self.tts_queue.task_done()
                    except queue.Empty:
                        continue
                    except Exception as e:
                        logger.debug(f"Error en el hilo de trabajo TTS: {e}")
                del engine
            except Exception as e:
                logger.error(f"Error al inicializar el motor TTS: {e}")
            finally:
                pythoncom.CoUninitialize()

        self.tts_thread = threading.Thread(target=_tts_loop, daemon=True)
        self.tts_thread.start()

    def _cleanup_audio(self):
        """Liberar los recursos de PyAudio."""
        try:
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
        except Exception as e:
            logger.debug(f"Error al cerrar el flujo de audio: {e}")
        
        try:
            if self.p_audio:
                self.p_audio.terminate()
                self.p_audio = None
        except Exception as e:
            logger.debug(f"Error al terminar PyAudio: {e}")

    def _start_listening_thread(self):
        """Lanza el hilo de escucha en segundo plano para el micrófono."""
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._listen_loop, daemon=True)
            self._thread.start()
            logger.info("Hilo de fondo para reconocimiento de voz de Vosk lanzado con éxito.")

    def _initialize_vosk_model(self) -> bool:
        """Inicializar el modelo de Vosk para el reconocimiento de voz fuera de línea.
        
        Returns:
            True si el modelo se cargó correctamente, False en caso contrario.
        """
        with self._lock:
            try:
                if self.vosk_model is None:
                    if not os.path.exists(VOSK_MODEL_PATH):
                        logger.warning(f"Modelo de Vosk no encontrado en: {VOSK_MODEL_PATH}")
                        logger.info("Intentando descargar el modelo de Vosk en español...")
                        
                        from src.utils.vosk_setup import setup_model, download_model_manual
                        if not setup_model():
                            logger.error(download_model_manual())
                            return False
                    
                    if not os.path.exists(VOSK_MODEL_PATH):
                        logger.error(f"El modelo de Vosk sigue sin estar disponible en: {VOSK_MODEL_PATH}")
                        return False
                    
                    self.vosk_model = Model(VOSK_MODEL_PATH)
                    logger.info("Modelo de Vosk cargado correctamente (modo fuera de línea - no requiere internet)")
                return True
            except Exception as e:
                logger.error(f"Error al inicializar el modelo de Vosk: {e}")
                return False

    def _listen_loop(self):
        """Bucle continuo en segundo plano que captura el habla usando Vosk (fuera de línea)."""
        try:
            # Inicializar el modelo de Vosk en el hilo de fondo
            if not self._initialize_vosk_model():
                logger.error("Error al inicializar el modelo de Vosk en el hilo de fondo.")
                return

            # Inicializar PyAudio
            self.p_audio = pyaudio.PyAudio()
            
            # Obtener el índice del micrófono de la configuración
            mic_id = self.config.get("microphone_id", 0)
            
            # Abrir el flujo de audio
            self.audio_stream = self.p_audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                input_device_index=mic_id,
                frames_per_buffer=2048
            )
            
            logger.info("El reconocedor de Vosk está escuchando... (modo fuera de línea)")
            
            # Crear reconocedor
            recognizer = KaldiRecognizer(self.vosk_model, 16000)
            
            # Variables para el control de la puerta de ruido (Noise Gate)
            gate_open_chunks = 0
            # hangover_chunks es el "tiempo de sostenido". A 16000Hz y un buffer de 2048 muestras,
            # cada bloque dura ~128ms. 4 bloques equivalen a ~512ms de margen para que la puerta
            # no se cierre abruptamente en medio de una frase o palabra.
            hangover_chunks = 4
            
            while self.is_active and self.is_enabled():
                try:
                    data = self.audio_stream.read(2048, exception_on_overflow=False)
                    
                    # CÁLCULO DE AMPLITUD RMS (VOLUMEN):
                    # Convertimos el buffer binario en un array numérico de tipo int16 (PCM 16 bits).
                    # Calculamos el valor RMS (Root Mean Square), que mide la potencia/amplitud de la señal.
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    rms = np.sqrt(np.mean(audio_data.astype(np.float32)**2))
                    
                    # CONTROL DE SENSIBILIDAD E UMBRAL:
                    # Obtenemos la sensibilidad configurada en el perfil (0 a 100).
                    sens = self.get_voice_sensitivity()
                    # Mapeamos la sensibilidad de forma inversa al umbral RMS.
                    # - Sensibilidad 100 -> Umbral 0 (pasa todo el audio).
                    # - Sensibilidad 50  -> Umbral 500 (ignora ruidos moderados).
                    # - Sensibilidad 0   -> Umbral 1000 (muy restrictivo, solo pasa sonidos muy fuertes).
                    threshold = (100 - sens) * 10
                    
                    # DECISIÓN DE LA PUERTA DE RUIDO:
                    if rms >= threshold:
                        # Si el volumen captado supera el umbral, consideramos que hay voz activa
                        # y abrimos/mantenemos abierta la puerta durante el tiempo de sostenido.
                        gate_open_chunks = hangover_chunks
                    else:
                        # Si el volumen es menor al umbral, reducimos el contador de sostenido
                        # para aproximarnos al cierre de la puerta.
                        if gate_open_chunks > 0:
                            gate_open_chunks -= 1
                    
                    # FILTRADO DE RUIDO:
                    # Si el contador de sostenido es 0, significa que no se ha detectado voz reciente.
                    # Reemplazamos todo el bloque de audio por silencio absoluto (bytes en cero).
                    # Esto evita que Vosk intente interpretar ruidos de fondo, murmullos o suspiros.
                    if gate_open_chunks <= 0:
                        data = b'\x00' * len(data)
                    
                    if recognizer.AcceptWaveform(data):
                        # Resultado final recibido
                        result_json = recognizer.Result()
                        try:
                            result = json.loads(result_json)
                            text = result.get("text", "")
                            if text.strip():
                                logger.info(f"El micrófono escuchó: '{text}'")
                                self._on_speech_recognized(text)
                        except json.JSONDecodeError:
                            pass
                    else:
                        # Resultado parcial disponible
                        try:
                            partial_json = recognizer.PartialResult()
                            partial = json.loads(partial_json)
                            if "partial" in partial and partial["partial"]:
                                logger.debug(f"Parcial: {partial['partial']}")
                        except json.JSONDecodeError:
                            pass
                            
                except Exception as e:
                    logger.debug(f"Error en el procesamiento de audio: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error en el bucle de escucha de Vosk: {e}")
        finally:
            self._cleanup_audio()

    def speak_confirmation(self, msg: str):
        """Añadir mensaje de voz a la cola del hilo de trabajo seguro."""
        if self.has_voice_feedback():
            logger.info(f"[VOICE FEEDBACK] Encolando confirmación de voz: {msg}")
            self.tts_queue.put(msg)

    def _on_speech_recognized(self, text: str):
        """Ejecuta acciones basadas en el habla reconocida: escribe en las casillas enfocadas y registra telemetria."""
        self.recognized_text = text

        # Comprobar comandos de voz normalizados
        norm_text = text.lower().strip().rstrip(".").rstrip(",")
        logger.info(f"Voice recognition result: '{text}' (normalized: '{norm_text}')")

        # Helpers de deteccion de palabras
        def _has_word(phrase, word):
            """Comprueba si word aparece como token independiente en phrase."""
            return (" " + word + " ") in (" " + phrase + " ")

        def _has_any_word(phrase, words):
            return any(_has_word(phrase, w) for w in words)

        def _has_any_substr(phrase, substrs):
            return any(s in phrase for s in substrs)

        # Funcion auxiliar para registrar telemetria
        def log_custom_event(event_type, action, extra_voice_text=None, is_click=False, click_count=1):
            try:
                from src.gui.pages.page_home import PageHome
                home_page = PageHome.get_instance()
                if home_page and home_page.is_recording:
                    x, y = pyautogui.position()
                    DatabaseManager().log_research_event(
                        session_id=home_page.session_id,
                        event_type=event_type,
                        gesture_name=action,
                        cursor_x=x,
                        cursor_y=y,
                        voice_text=extra_voice_text
                    )
                    if is_click:
                        home_page.total_clicks += click_count
                    else:
                        home_page.total_voice_commands += 1
            except Exception as e:
                logger.error(f"Error al registrar la telemetria de voz: {e}")

        # 1. Guardia de DESACTIVACION de escritura (evalua primero para mayor seguridad)
        STOP_WRITE = [
            "silencio", "silencia", "silenciar", "pausa", "pausar",
            "no escribir", "dejar de escribir", "deja de escribir",
            "parar de escribir", "para de escribir", "desactivar escritura",
            "pausar escritura", "detener escritura", "pausa escritura",
            "detener voz", "desactivar voz", "pausar voz",
            "voz down", "vos down", "boss down", "bos down",
            "voz off", "vos off", "voz of", "vos of",
            "boss off", "boss of", "bos off", "bos of",
        ]
        if _has_any_substr(norm_text, STOP_WRITE):
            from src.config_manager import ConfigManager
            ConfigManager().update_voice_config({"auto_type": False})
            self.speak_confirmation("Escritura desactivada")
            if self._ui_callback:
                self._ui_callback("[Comando: Escritura desactivada]")
            from src.gui.pages.page_home import PageHome
            home = PageHome.get_instance()
            if home:
                try:
                    home.after(1, lambda: home.root_callback("refresh_voice_write") if home.root_callback else None)
                except Exception:
                    pass
            return

        # 2. Guardia de ACTIVACION de escritura
        START_WRITE_SUBSTRS = [
            "activar escritura", "iniciar escritura", "activar voz", "iniciar voz",
            "voz activa", "voz up", "vos up", "boss up", "bos up",
            "voz on", "vos on", "boss on", "bos on",
        ]
        _WRITE_EXACT_WORDS = ["escribir", "escritura", "escribe", "escriba"]
        if _has_any_substr(norm_text, START_WRITE_SUBSTRS) or _has_any_word(norm_text, _WRITE_EXACT_WORDS):
            from src.config_manager import ConfigManager
            ConfigManager().update_voice_config({"auto_type": True})
            self.speak_confirmation("Escritura activada")
            if self._ui_callback:
                self._ui_callback("[Comando: Escritura activada]")
            from src.gui.pages.page_home import PageHome
            home = PageHome.get_instance()
            if home:
                try:
                    home.after(1, lambda: home.root_callback("refresh_voice_write") if home.root_callback else None)
                except Exception:
                    pass
            return

        # 3. Comandos de control de cursor (Mover / Quieto)
        START_CURSOR_SUBSTRS = ["activar cursor", "cursor on"]
        STOP_CURSOR_SUBSTRS = ["desactivar cursor", "cursor off", "detener cursor", "pausar cursor"]
        if _has_any_substr(norm_text, START_CURSOR_SUBSTRS) or _has_word(norm_text, "mover"):
            from src.controllers import MouseController
            MouseController().set_active(True)
            self.speak_confirmation("Control de cursor activado")
            if self._ui_callback:
                self._ui_callback("[Comando: Cursor activado]")
            log_custom_event(event_type="voice_command", action="cursor_on", extra_voice_text="activar cursor")
            return

        if _has_any_substr(norm_text, STOP_CURSOR_SUBSTRS) or _has_word(norm_text, "quieto"):
            from src.controllers import MouseController
            MouseController().set_active(False)
            self.speak_confirmation("Control de cursor desactivado")
            if self._ui_callback:
                self._ui_callback("[Comando: Cursor desactivado]")
            log_custom_event(event_type="voice_command", action="cursor_off", extra_voice_text="desactivar cursor")
            return

        # 4. Comandos de control de sesion
        words = norm_text.split()
        is_focuz_brand = any(w in words for w in ["focuz", "focus", "focu", "focuvoz", "focusvoz", "focuzvoz"])

        # Check if the user explicitly wants to close the program
        is_close_cmd = False
        if is_focuz_brand and any(w in words for w in ["finish", "finis", "finsh", "fini", "fin", "cerrar", "cierra", "exit", "finalizar"]):
            is_close_cmd = True
        elif any(w in words for w in ["cerrar", "cierra", "salir", "finalizar"]) and any(w in words for w in ["programa", "aplicacion", "aplicación"]):
            is_close_cmd = True

        if is_close_cmd:
            from src.gui.pages.page_home import PageHome
            home = PageHome.get_instance()
            if home:
                self.speak_confirmation("Cerrando aplicacion")
                if self._ui_callback:
                    self._ui_callback("[Comando: Cerrando aplicacion]")
                home.after(100, lambda: home.root_callback("close_app") if home.root_callback else None)
            return

            if any(w in words for w in ["go", "start", "iniciar", "inicia", "comenzar"]):
                from src.gui.pages.page_home import PageHome
                home = PageHome.get_instance()
                if home:
                    if home.session_id is None:
                        try:
                            import getpass
                            computer_user = getpass.getuser()
                            subject_id = computer_user if computer_user else "UsuarioLocal"
                            first_name = computer_user.capitalize() if computer_user else "Usuario"
                            home.session_id = DatabaseManager().start_research_session(
                                subject_id=subject_id,
                                profile_name="Default",
                                subject_first_name=first_name,
                                subject_last_name=""
                            )
                            home.is_recording = True
                            home.total_clicks = 0
                            home.total_voice_commands = 0
                            home.total_keystrokes = 0
                            self.speak_confirmation("Sesión iniciada")
                            if self._ui_callback:
                                self._ui_callback("[Comando: Sesión iniciada]")
                        except Exception as e:
                            logger.error(f"Error starting session via voice: {e}")
                    else:
                        self.speak_confirmation("Sesión ya está activa")
                        if self._ui_callback:
                            self._ui_callback("[Sesión ya activa]")
                return

        # 5. Comandos de CLICS con variantes fonéticas que Vosk en español puede producir
        CLIC_WORDS = ["clic", "click", "cli", "klik", "clik", "clique", "klick", "klic", "klique", "tic", "tick", "tique", "tics", "ticks"]
        LEFT_WORDS = ["izquierdo", "izquierda", "izquiedo", "izquiero", "izquerda"]
        DOUBLE_WORDS = ["doble", "dobles", "dobl"]

        has_clic = any(w in words for w in CLIC_WORDS)
        has_double = any(w in words for w in DOUBLE_WORDS)
        has_left = any(w in words for w in LEFT_WORDS)

        if has_clic:
            logger.info(f"[VOICE COMMAND] Clic command detected: has_double={has_double}, has_left={has_left}")
            if has_double:
                if has_left:
                    # "doble clic izquierdo"
                    pyautogui.click(button="left", clicks=2, interval=0.1)
                    self.speak_confirmation("Doble clic izquierdo")
                    if self._ui_callback:
                        self._ui_callback("[Comando: Doble clic izquierdo]")
                    log_custom_event(event_type="double_click", action="voice_double_click_left", is_click=True, click_count=2)
                    return
                else:
                    # "doble clic" -> Doble clic derecho
                    pyautogui.click(button="right", clicks=2, interval=0.1)
                    self.speak_confirmation("Doble clic derecho")
                    if self._ui_callback:
                        self._ui_callback("[Comando: Doble clic derecho]")
                    log_custom_event(event_type="double_click", action="voice_double_click_right", is_click=True, click_count=2)
                    return
            else:
                if has_left:
                    # "clic izquierdo"
                    pyautogui.click(button="left")
                    self.speak_confirmation("Clic izquierdo")
                    if self._ui_callback:
                        self._ui_callback("[Comando: Clic izquierdo]")
                    log_custom_event(event_type="click", action="voice_click_left", is_click=True, click_count=1)
                    return
                else:
                    # "clic" (o "cli") -> Clic derecho
                    pyautogui.click(button="right")
                    self.speak_confirmation("Clic derecho")
                    if self._ui_callback:
                        self._ui_callback("[Comando: Clic derecho]")
                    log_custom_event(event_type="click", action="voice_click_right", is_click=True, click_count=1)
                    return

        # 5. Comandos para abrir aplicaciones
        # Analizar verbos de apertura (ampliado para variantes y sinónimos en español)
        OPEN_VERBS = [
            "abrir", "abre", "abran", "ábreme", "abreme", "abrelo", "ábrelo", "abrela", "ábrela",
            "iniciar", "inicia", "inici", "lanzar", "lanza", "lanzame", "ejecutar", "ejecuta",
            "ejecutame", "run", "open", "lansa", "lansame", "abril"
        ]
        is_open_cmd = any(w in words for w in OPEN_VERBS)

        # A. Navegador / Internet
        NAV_TERMS = ["navegador", "internet", "chrome", "google", "explorador", "web", "browser", "edge", "firefox", "opera", "safari"]
        is_nav_term = any(w in words for w in NAV_TERMS)
        
        # B. Word (se remueven términos hiper-comunes 'por' y 'ver' para evitar falsos positivos)
        WORD_TERMS = [
            "word", "uord", "wor", "board", "work", "guor", "words", "works",
            "guord", "uort", "wort", "guort", "huor", "huort", "vuor", "vuort", "gor",
            "gort", "glor", "gual", "guol", "vor", "bor", "bord", "uard", "guard",
            "winword", "uor", "wors", "world"
        ]
        is_word_term = any(w in words for w in WORD_TERMS)
        
        # C. Bloc de notas / Notepad
        NOTEPAD_TERMS = ["notas", "nota", "notepad", "bloc", "notpad", "blocnotas", "blog", "block", "notapad"]
        is_notepad_term = any(w in words for w in NOTEPAD_TERMS)

        logger.debug(f"[VOICE COMMAND ENGINE] Match status: is_open_cmd={is_open_cmd}, is_nav_term={is_nav_term}, is_word_term={is_word_term}, is_notepad_term={is_notepad_term}")

        if is_open_cmd and is_nav_term:
            import os as _os
            with TempResetDLLDirectory():
                try:
                    _os.startfile("https://www.google.com")
                except Exception:
                    import webbrowser
                    webbrowser.open("https://www.google.com")
            self.speak_confirmation("Abriendo navegador")
            if self._ui_callback:
                self._ui_callback("[Comando: Abrir Navegador]")
            log_custom_event(event_type="voice_command", action="launch_browser", extra_voice_text="abrir internet")
            return

        elif is_open_cmd and is_word_term and not is_notepad_term:
            import os as _os
            word_launched = False
            possible_word_paths = [
                r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
                r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE",
                r"C:\Program Files\Microsoft Office\Office16\WINWORD.EXE",
                r"C:\Program Files (x86)\Microsoft Office\Office16\WINWORD.EXE",
                r"C:\Program Files\Microsoft Office\Office15\WINWORD.EXE",
                r"C:\Program Files (x86)\Microsoft Office\Office15\WINWORD.EXE",
                r"C:\Program Files\Microsoft Office\Office14\WINWORD.EXE",
                r"C:\Program Files (x86)\Microsoft Office\Office14\WINWORD.EXE",
            ]
            with TempResetDLLDirectory():
                for path in possible_word_paths:
                    if _os.path.exists(path):
                        try:
                            logger.info(f"Launching Word from absolute path: {path}")
                            _os.startfile(path)
                            word_launched = True
                            break
                        except Exception as e:
                            logger.warning(f"Failed to launch Word from absolute path {path}: {e}")
                if not word_launched:
                    try:
                        logger.info("Launching Word via os.startfile shortcut...")
                        _os.startfile("winword.exe")
                        word_launched = True
                    except Exception as e:
                        logger.warning(f"Failed to launch Word via startfile winword.exe: {e}")
                        try:
                            logger.info("Launching Word via system registry startup...")
                            _os.system("start winword")
                            word_launched = True
                        except Exception as ex:
                            logger.error(f"Error launching Word fallback: {ex}")
            self.speak_confirmation("Abriendo Word")
            if self._ui_callback:
                self._ui_callback("[Comando: Abrir Word]")
            log_custom_event(event_type="voice_command", action="launch_word", extra_voice_text="abrir word")
            return

        elif is_open_cmd and is_notepad_term:
            import os as _os
            notepad_launched = False
            possible_notepad_paths = [
                r"C:\Windows\System32\notepad.exe",
                r"C:\Windows\notepad.exe"
            ]
            with TempResetDLLDirectory():
                for path in possible_notepad_paths:
                    if _os.path.exists(path):
                        try:
                            logger.info(f"Launching Notepad from absolute path: {path}")
                            _os.startfile(path)
                            notepad_launched = True
                            break
                        except Exception as e:
                            logger.warning(f"Failed to launch Notepad from absolute path {path}: {e}")
                if not notepad_launched:
                    try:
                        logger.info("Launching Notepad via os.startfile...")
                        _os.startfile("notepad.exe")
                        notepad_launched = True
                    except Exception as e:
                        logger.warning(f"Failed to launch Notepad via startfile: {e}")
                        try:
                            logger.info("Launching Notepad via system PATH...")
                            _os.system("start notepad")
                            notepad_launched = True
                        except Exception as ex:
                            logger.error(f"Error launching Notepad fallback: {ex}")
            self.speak_confirmation("Abriendo bloc de notas")
            if self._ui_callback:
                self._ui_callback("[Comando: Abrir Notas]")
            log_custom_event(event_type="voice_command", action="launch_notepad", extra_voice_text="abrir bloc de notas")
            return

        # 6. Leer auto_type directamente de ConfigManager para evitar desync de config
        from src.config_manager import ConfigManager as _CM
        _auto_type_active = _CM().get_voice_config().get("auto_type", False)

        if _auto_type_active:
            cmd_text = norm_text.strip().rstrip(".").rstrip(",")

            # Borrar todo el texto
            if cmd_text in ["borrar todo", "eliminar todo", "limpiar todo", "limpiar", "borra todo", "elimina todo", "limpiar el texto", "borrar todo el texto"]:
                logger.info("[VOICE COMMAND] Clear current paragraph/line triggered!")
                try:
                    # Seleccionar hacia arriba para abarcar el párrafo
                    with self.keyboard_controller.pressed(keyboard.Key.ctrl, keyboard.Key.shift):
                        self.keyboard_controller.press(keyboard.Key.up)
                        self.keyboard_controller.release(keyboard.Key.up)
                    # Seleccionar hasta el inicio de la línea (para inputs de una sola línea)
                    with self.keyboard_controller.pressed(keyboard.Key.shift):
                        self.keyboard_controller.press(keyboard.Key.home)
                        self.keyboard_controller.release(keyboard.Key.home)
                    # Borrar la selección
                    self.keyboard_controller.press(keyboard.Key.backspace)
                    self.keyboard_controller.release(keyboard.Key.backspace)
                except Exception as e:
                    logger.error(f"Error al borrar todo: {e}")
                if self._ui_callback:
                    try:
                        self._ui_callback("[Comando: Texto Borrado]")
                    except Exception:
                        pass
                return

            # Borrar ultimo segmento escrito
            elif cmd_text in ["borrar", "eliminar", "corregir", "deshacer", "borra", "elimina", "deshaz"]:
                logger.info("[VOICE COMMAND] Delete last typed segment triggered!")
                last_len = getattr(self, "last_typed_len", 0)
                if last_len > 0:
                    try:
                        for _ in range(last_len):
                            self.keyboard_controller.press(keyboard.Key.backspace)
                            self.keyboard_controller.release(keyboard.Key.backspace)
                            time.sleep(0.005)
                    except Exception as e:
                        logger.error(f"Error al borrar segmento: {e}")
                    self.last_typed_len = 0
                else:
                    try:
                        for _ in range(8):
                            self.keyboard_controller.press(keyboard.Key.backspace)
                            self.keyboard_controller.release(keyboard.Key.backspace)
                    except Exception:
                        pass
                if self._ui_callback:
                    try:
                        self._ui_callback("[Comando: Deshacer segmento]")
                    except Exception:
                        pass
                return

        # 7. Dictado automatico de texto al campo enfocado
        if _auto_type_active:
            typed_str = text + " "
            self.last_typed_len = len(typed_str)
            self.type_text(typed_str)

        # 8. Actualizar UI con el texto reconocido
        if self._ui_callback:
            try:
                self._ui_callback(text)
            except Exception as e:
                logger.error(f"Error al actualizar la UI: {e}")

        # 9. Registrar en SQLite para la sesion activa de investigacion
        try:
            from src.gui.pages.page_home import PageHome
            home_page = PageHome.get_instance()
            if home_page and home_page.is_recording:
                word_count = len(text.split())
                approx_duration_ms = word_count * 400.0
                DatabaseManager().log_research_event(
                    session_id=home_page.session_id,
                    event_type="voice_dictation",
                    voice_text=text,
                    voice_confidence=0.95,
                    voice_success=1,
                    voice_duration_ms=approx_duration_ms
                )
                home_page.total_voice_commands += 1
        except Exception as e:
            logger.error(f"Error al registrar la telemetria de voz: {e}")


    def register_ui_callback(self, callback: callable):
        """Registrar un callback seguro para hilos para enviar el texto reconocido a la interfaz de usuario."""
        self._ui_callback = callback

    def update_config(self, config: dict):
        """Actualizar la configuración e iniciar/detener el hilo de fondo en consecuencia."""
        old_enabled = self.is_enabled()
        old_mic_id = self.config.get("microphone_id", 0) if self.config else None
        
        self.config = config
        logger.info(f"VoiceController config updated: {config}")
        
        if self.is_active:
            new_enabled = self.is_enabled()
            new_mic_id = self.config.get("microphone_id", 0)
            
            if not new_enabled:
                if self._thread is not None:
                    logger.info("Voice recognition disabled. Stopping listening thread...")
                    self.is_active = False  # Temporarily set to False to stop the loop
                    # Wait for thread to finish
                    if self._thread.is_alive():
                        self._thread.join(timeout=1.0)
                    self._cleanup_audio()
                    self._thread = None
                    self.is_active = True  # Restore
            else:
                # Restart if microphone changed, or if was previously disabled, or thread died
                if not old_enabled or (old_mic_id is not None and old_mic_id != new_mic_id) or self._thread is None or not self._thread.is_alive():
                    logger.info("Restarting listening thread due to config change...")
                    if self._thread is not None:
                        self.is_active = False
                        if self._thread.is_alive():
                            self._thread.join(timeout=1.0)
                        self._cleanup_audio()
                        self._thread = None
                        self.is_active = True
                    
                    self._start_listening_thread()

    def type_text(self, text: str):
        """Escribir texto carácter por carácter utilizando simulación de teclado.
        
        Args:
            text: El texto a escribir.
        """
        try:
            for char in text:
                self.keyboard_controller.type(char)
            logger.info(f"Typed text: {text}")
        except Exception as e:
            logger.error(f"Error typing text: {e}")

    def is_enabled(self) -> bool:
        """Comprobar si el reconocimiento de voz está habilitado.
        
        Returns:
            True si el reconocimiento de voz está habilitado, False en caso contrario.
        """
        return self.config.get("enabled", False)

    def get_language(self) -> str:
        """Obtener el idioma configurado para el reconocimiento de voz.
        
        Returns:
            Código de idioma (ej., 'es-ES', 'en-US')
        """
        return self.config.get("language", "es-ES")

    def get_confidence_threshold(self) -> float:
        """Obtener el umbral de confianza para el reconocimiento de voz.
        
        Returns:
            Umbral de confianza (0.0 a 1.0)
        """
        return self.config.get("confidence_threshold", 0.5)

    def get_voice_sensitivity(self) -> int:
        """Obtener la sensibilidad de voz configurada.
        
        Returns:
            Sensibilidad de voz (0-100)
        """
        return self.config.get("voice_sensitivity", 50)

    def should_auto_type(self) -> bool:
        """Comprobar si el texto debe escribirse automáticamente.
        
        Returns:
            True si la escritura automática está habilitada, False en caso contrario.
        """
        return self.config.get("auto_type", True)



    def should_pause_during_cursor(self) -> bool:
        """Comprobar si la voz debe pausarse durante el movimiento del cursor.
        
        Returns:
            True si la pausa durante el movimiento del cursor está habilitada, False en caso contrario.
        """
        return self.config.get("pause_during_cursor", True)

    def get_speech_timeout_ms(self) -> int:
        """Obtener el tiempo de espera de habla en milisegundos.
        
        Returns:
            Tiempo de espera en milisegundos.
        """
        return self.config.get("speech_timeout_ms", 5000)

    def has_voice_feedback(self) -> bool:
        """Comprobar si la retroalimentación de voz está habilitada.
        
        Returns:
            True si la retroalimentación de voz está habilitada, False en caso contrario.
        """
        return self.config.get("voice_feedback", True)
