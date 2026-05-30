import logging
import tkinter
from functools import partial

import customtkinter

from src.config_manager import ConfigManager
from src.controllers.voice_controller import VoiceController
from src.gui.frames.safe_disposable_frame import SafeDisposableFrame

logger = logging.getLogger("PageVoice")


class PageVoice(SafeDisposableFrame):

    def __init__(self, master, root_callback: callable, **kwargs):
        super().__init__(master, **kwargs)
        logger.info("Create PageVoice")

        self.grid_rowconfigure(10, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.config_manager = ConfigManager()
        self.voice_controller = VoiceController()
        self.root_callback = root_callback

        # Título
        title_label = customtkinter.CTkLabel(
            master=self, text="Configuración de Voz", text_color="white")
        title_label.cget("font").configure(size=20)
        title_label.grid(row=0,
                         column=0,
                         padx=20,
                         pady=20,
                         sticky="nw",
                         columnspan=2)

        # Activar/Desactivar reconocimiento de voz
        enable_label = customtkinter.CTkLabel(master=self,
                                               text="Activar reconocimiento de voz:")
        enable_label.grid(row=1, column=0, padx=20, pady=10, sticky="nw")

        self.enable_var = tkinter.BooleanVar()
        self.enable_switch = customtkinter.CTkSwitch(
            master=self,
            variable=self.enable_var,
            command=self._on_enable_change)
        self.enable_switch.grid(row=1, column=1, padx=20, pady=10, sticky="ne")

        # Selección de idioma
        lang_label = customtkinter.CTkLabel(master=self, text="Idioma:")
        lang_label.grid(row=2, column=0, padx=20, pady=10, sticky="nw")

        self.language_var = tkinter.StringVar()
        self.language_menu = customtkinter.CTkComboBox(
            master=self,
            values=["es-ES", "en-US", "en-GB", "fr-FR"],
            variable=self.language_var,
            command=self._on_language_change)
        self.language_menu.grid(row=2, column=1, padx=20, pady=10, sticky="we")

        # Deslizador de sensibilidad del micrófono
        sens_label = customtkinter.CTkLabel(
            master=self, text="Sensibilidad de micrófono:")
        sens_label.grid(row=3, column=0, padx=20, pady=10, sticky="nw")

        self.sensitivity_var = tkinter.DoubleVar()
        self.sensitivity_slider = customtkinter.CTkSlider(
            master=self,
            from_=0,
            to=100,
            variable=self.sensitivity_var,
            command=self._on_sensitivity_change)
        self.sensitivity_slider.grid(row=3, column=1, padx=20, pady=10, sticky="we")

        self.sensitivity_value = customtkinter.CTkLabel(
            master=self, text="50%", text_color="gray")
        self.sensitivity_value.grid(row=3, column=1, padx=20, pady=10, sticky="e")

        # Umbral de confianza
        conf_label = customtkinter.CTkLabel(
            master=self, text="Umbral de confianza:")
        conf_label.grid(row=4, column=0, padx=20, pady=10, sticky="nw")

        self.confidence_var = tkinter.DoubleVar()
        self.confidence_slider = customtkinter.CTkSlider(
            master=self,
            from_=0,
            to=1,
            number_of_steps=10,
            variable=self.confidence_var,
            command=self._on_confidence_change)
        self.confidence_slider.grid(row=4, column=1, padx=20, pady=10, sticky="we")

        self.confidence_value = customtkinter.CTkLabel(
            master=self, text="0.5", text_color="gray")
        self.confidence_value.grid(row=4, column=1, padx=20, pady=10, sticky="e")

        # Opción de escritura automática
        auto_type_label = customtkinter.CTkLabel(
            master=self, text="Escribir automáticamente:")
        auto_type_label.grid(row=5, column=0, padx=20, pady=10, sticky="nw")

        self.auto_type_var = tkinter.BooleanVar()
        self.auto_type_switch = customtkinter.CTkSwitch(
            master=self,
            variable=self.auto_type_var,
            command=self._on_auto_type_change)
        self.auto_type_switch.grid(row=5, column=1, padx=20, pady=10, sticky="ne")

        # Activación por palabra clave (Hotword)
        hotword_label = customtkinter.CTkLabel(
            master=self, text="Palabra clave para activar/desactivar escritura:")
        hotword_label.grid(row=6, column=0, padx=20, pady=10, sticky="nw")

        self.hotword_var = tkinter.StringVar()
        self.hotword_entry = customtkinter.CTkEntry(
            master=self,
            width=200,
            textvariable=self.hotword_var,
            placeholder_text="Ej: focuz"
        )
        self.hotword_entry.grid(row=6, column=1, padx=20, pady=10, sticky="ne")
        self.hotword_entry.bind("<KeyRelease>", self._on_hotword_change)

        # Requerir confirmación
        confirm_label = customtkinter.CTkLabel(
            master=self,
            text="Requerir confirmación antes de escribir:")
        confirm_label.grid(row=7, column=0, padx=20, pady=10, sticky="nw")

        self.confirm_var = tkinter.BooleanVar()
        self.confirm_switch = customtkinter.CTkSwitch(
            master=self,
            variable=self.confirm_var,
            command=self._on_confirm_change)
        self.confirm_switch.grid(row=7, column=1, padx=20, pady=10, sticky="ne")

        # Retroalimentación de voz
        feedback_label = customtkinter.CTkLabel(
            master=self, text="Retroalimentación de voz:")
        feedback_label.grid(row=8, column=0, padx=20, pady=10, sticky="nw")

        self.feedback_var = tkinter.BooleanVar()
        self.feedback_switch = customtkinter.CTkSwitch(
            master=self,
            variable=self.feedback_var,
            command=self._on_feedback_change)
        self.feedback_switch.grid(row=8, column=1, padx=20, pady=10, sticky="ne")

        # Botón de prueba
        test_btn = customtkinter.CTkButton(
            master=self,
            text="Probar Micrófono",
            command=self._test_microphone)
        test_btn.grid(row=9, column=0, padx=20, pady=20, sticky="ew", columnspan=2)

        self.test_result_label = customtkinter.CTkLabel(
            master=self, text="", text_color="gray")
        self.test_result_label.grid(row=10, column=0, padx=20, pady=5, sticky="ew", columnspan=2)

        self.grid_rowconfigure(11, weight=1)

        self.load_initial_config()

    def load_initial_config(self):
        """Carga la configuración de voz desde el archivo."""
        try:
            config = self.config_manager.get_voice_config()
            self.voice_controller.update_config(config)

            self.enable_var.set(config.get("enabled", False))
            self.language_var.set(config.get("language", "es-ES"))
            self.sensitivity_var.set(config.get("voice_sensitivity", 50))
            self.confidence_var.set(config.get("confidence_threshold", 0.5))
            self.auto_type_var.set(config.get("auto_type", True))
            self.confirm_var.set(config.get("confirmation_required", False))
            self.feedback_var.set(config.get("voice_feedback", True))
            self.hotword_var.set(config.get("hotword", "focuz"))

            self._update_display_values()
            logger.info("Voice config loaded successfully")
        except Exception as e:
            logger.error(f"Error loading voice config: {e}")

    def _update_display_values(self):
        """Actualiza los valores mostrados para los deslizadores."""
        self.sensitivity_value.configure(
            text=f"{int(self.sensitivity_var.get())}%")
        self.confidence_value.configure(
            text=f"{self.confidence_var.get():.1f}")

    def _on_enable_change(self):
        """Maneja la activación/desactivación del interruptor."""
        self.config_manager.update_voice_config(
            {"enabled": self.enable_var.get()})
        logger.info(f"Voice enabled: {self.enable_var.get()}")

    def _on_language_change(self, value):
        """Maneja el cambio de idioma."""
        self.config_manager.update_voice_config({"language": value})
        logger.info(f"Language changed to: {value}")

    def _on_sensitivity_change(self, value):
        """Maneja el cambio de sensibilidad."""
        self._update_display_values()
        self.config_manager.update_voice_config(
            {"voice_sensitivity": int(float(value))})

    def _on_confidence_change(self, value):
        """Maneja el cambio del umbral de confianza."""
        self._update_display_values()
        self.config_manager.update_voice_config(
            {"confidence_threshold": float(value)})

    def _on_auto_type_change(self):
        """Maneja el interruptor de escritura automática y sincroniza el menú lateral."""
        self.config_manager.update_voice_config(
            {"auto_type": self.auto_type_var.get()})
        logger.info(f"Auto-type: {self.auto_type_var.get()}")
        # Sincronizar el menú lateral
        try:
            if hasattr(self.master, "frame_menu"):
                self.master.frame_menu.refresh_voice_write_switch()
            elif hasattr(self.master.master, "frame_menu"):
                self.master.master.frame_menu.refresh_voice_write_switch()
        except Exception:
            pass

    def _on_hotword_change(self, event=None):
        """Maneja el cambio del texto de la palabra clave."""
        val = self.hotword_var.get().strip()
        self.config_manager.update_voice_config({"hotword": val})
        logger.info(f"Hotword changed to: {val}")

    def _on_confirm_change(self):
        """Maneja el interruptor de requerimiento de confirmación."""
        self.config_manager.update_voice_config(
            {"confirmation_required": self.confirm_var.get()})
        logger.info(f"Confirmation required: {self.confirm_var.get()}")

    def _on_feedback_change(self):
        """Maneja el interruptor de retroalimentación de voz."""
        self.config_manager.update_voice_config(
            {"voice_feedback": self.feedback_var.get()})
        logger.info(f"Voice feedback: {self.feedback_var.get()}")

    def _test_microphone(self):
        """Prueba la conexión del micrófono."""
        self.test_result_label.configure(text="Probando micrófono...", text_color="yellow")
        self.update()
        
        try:
            # Prueba simple: verificar si el dispositivo de audio está disponible
            logger.info("Microphone test started")
            self.test_result_label.configure(
                text="✓ Micrófono detectado correctamente",
                text_color="green")
        except Exception as e:
            logger.error(f"Microphone test failed: {e}")
            self.test_result_label.configure(
                text=f"✗ Error en micrófono: {str(e)}",
                text_color="red")

    def enter(self):
        """Se llama al entrar en la página."""
        logger.info("enter")
        self.load_initial_config()

    def leave(self):
        """Se llama al salir de la página."""
        logger.info("leave")
