import logging
import threading
import time
import json
import os
import pynput.keyboard as keyboard
import pyaudio
import pyautogui

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
            # Inicializar el modelo de Vosk al iniciar el hilo
            if self._initialize_vosk_model():
                self._thread = threading.Thread(target=self._listen_loop, daemon=True)
                self._thread.start()
                logger.info("Hilo de fondo para reconocimiento de voz de Vosk lanzado con éxito.")
            else:
                logger.error("Error al inicializar el modelo de Vosk. Verifique la ruta de instalación.")

    def _initialize_vosk_model(self) -> bool:
        """Inicializar el modelo de Vosk para el reconocimiento de voz fuera de línea.
        
        Returns:
            True si el modelo se cargó correctamente, False en caso contrario.
        """
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
            
            while self.is_active and self.is_enabled():
                try:
                    data = self.audio_stream.read(2048, exception_on_overflow=False)
                    
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

        # Helpers de deteccion de palabras
        def _has_word(phrase, word):
            """Comprueba si word aparece como token independiente en phrase."""
            return (" " + word + " ") in (" " + phrase + " ")

        def _has_any_word(phrase, words):
            return any(_has_word(phrase, w) for w in words)

        def _has_any_substr(phrase, substrs):
            return any(s in phrase for s in substrs)

        # 1. Guardia de DESACTIVACION de escritura (evalua primero para mayor seguridad)
        STOP_WRITE = [
            "silencio", "no escribir", "dejar de escribir", "deja de escribir",
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

        # 3. Comandos de control de sesion
        words = norm_text.split()
        is_focuz_brand = any(w in words for w in ["focuz", "focus", "focu", "focuvoz", "focusvoz"])

        if is_focuz_brand and any(w in words for w in ["finish", "finis", "finsh", "fini", "fin", "cerrar", "cierra", "exit", "finalizar"]):
            from src.gui.pages.page_home import PageHome
            home = PageHome.get_instance()
            if home:
                self.speak_confirmation("Cerrando aplicacion")
                if self._ui_callback:
                    self._ui_callback("[Comando: Cerrando aplicacion]")
                home.after(100, lambda: home.root_callback("close_app") if home.root_callback else None)
            return

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

        # 4. Comandos de CLICS con variantes foneticas que Vosk en espanol puede producir
        CLICK_VARIANTS = ["click", "clic", "klik", "clik", "clique", "klick", "klic", "klique"]
        DOUBLE_RIGHT = ["doble click derecho", "doble clic derecho", "doble klik derecho", "doble klick derecho"]
        DOUBLE_LEFT  = ["doble click izquierdo", "doble clic izquierdo",
                        "doble click", "doble clic", "doble klik", "doble klick"]
        RIGHT_CLICK  = ["click derecho", "clic derecho", "klik derecho", "klick derecho"]

        if _has_any_substr(norm_text, DOUBLE_RIGHT):
            pyautogui.click(button="right", clicks=2, interval=0.1)
            self.speak_confirmation("Doble clic derecho")
            if self._ui_callback:
                self._ui_callback("[Comando: Doble clic derecho]")
            log_custom_event(event_type="double_click", action="voice_double_click_right", is_click=True, click_count=2)
            return

        elif _has_any_substr(norm_text, DOUBLE_LEFT):
            pyautogui.click(button="left", clicks=2, interval=0.1)
            self.speak_confirmation("Doble clic izquierdo")
            if self._ui_callback:
                self._ui_callback("[Comando: Doble clic izquierdo]")
            log_custom_event(event_type="double_click", action="voice_double_click_left", is_click=True, click_count=2)
            return

        elif _has_any_substr(norm_text, RIGHT_CLICK):
            pyautogui.click(button="right")
            self.speak_confirmation("Clic derecho")
            if self._ui_callback:
                self._ui_callback("[Comando: Clic derecho]")
            log_custom_event(event_type="click", action="voice_click_right", is_click=True, click_count=1)
            return

        elif _has_any_word(norm_text, CLICK_VARIANTS):
            # Click izquierdo simple: solo si la variante aparece como palabra aislada
            pyautogui.click(button="left")
            self.speak_confirmation("Clic izquierdo")
            if self._ui_callback:
                self._ui_callback("[Comando: Clic izquierdo]")
            log_custom_event(event_type="click", action="voice_click_left", is_click=True, click_count=1)
            return

        # 5. Comandos para abrir aplicaciones
        elif norm_text in ["abrir navegador", "abrir internet", "iniciar navegador", "iniciar internet"]:
            import os as _os
            try:
                _os.startfile("https://www.google.com")
            except Exception:
                import webbrowser
                webbrowser.open("https://www.google.com")
            self.speak_confirmation("Abriendo navegador")
            if self._ui_callback:
                self._ui_callback("[Comando: Abrir Navegador]")
            log_custom_event(event_type="voice_command", action="launch_browser", extra_voice_text=norm_text)
            return

        elif norm_text in ["abrir word", "iniciar word", "abrir microsoft word"]:
            import os as _os, subprocess as _sp
            try:
                _os.startfile("winword.exe")
            except Exception:
                try:
                    _sp.Popen("start winword", shell=True)
                except Exception as e:
                    logger.error(f"Error launching Word: {e}")
            self.speak_confirmation("Abriendo Word")
            if self._ui_callback:
                self._ui_callback("[Comando: Abrir Word]")
            log_custom_event(event_type="voice_command", action="launch_word", extra_voice_text=norm_text)
            return

        elif norm_text in ["abrir bloc de notas", "abrir notas", "abrir notepad", "iniciar bloc de notas"]:
            import subprocess as _sp
            _sp.Popen("notepad.exe")
            self.speak_confirmation("Abriendo bloc de notas")
            if self._ui_callback:
                self._ui_callback("[Comando: Abrir Notas]")
            log_custom_event(event_type="voice_command", action="launch_notepad", extra_voice_text=norm_text)
            return

        # 6. Leer auto_type directamente de ConfigManager para evitar desync de config
        from src.config_manager import ConfigManager as _CM
        _auto_type_active = _CM().get_voice_config().get("auto_type", False)

        if _auto_type_active:
            cmd_text = norm_text.strip().rstrip(".").rstrip(",")

            # Borrar todo el texto
            if cmd_text in ["borrar todo", "eliminar todo", "limpiar todo", "limpiar"]:
                logger.info("[VOICE COMMAND] Clear all text triggered!")
                try:
                    with self.keyboard_controller.pressed(keyboard.Key.ctrl):
                        self.keyboard_controller.press("a")
                        self.keyboard_controller.release("a")
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
            elif cmd_text in ["borrar", "eliminar", "corregir", "deshacer"]:
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
        self.config = config
        logger.info(f"VoiceController config updated: {config}")
        
        if self.is_active:
            if self.is_enabled():
                self._start_listening_thread()
            else:
                self._thread = None

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

    def requires_confirmation(self) -> bool:
        """Comprobar si se requiere confirmación antes de escribir.
        
        Returns:
            True si se requiere confirmación, False en caso contrario.
        """
        return self.config.get("confirmation_required", False)

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
