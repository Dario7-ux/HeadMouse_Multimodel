import logging
import time
import math
import customtkinter
from PIL import Image

from src.gui.frames.safe_disposable_frame import SafeDisposableFrame
from src.gui.theme_colors import (
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TITLE,
    ACCENT, BG_CARD, BORDER
)

logger = logging.getLogger("PageHome")
LOGO_SIZE = (240, 118)

# Instructions details
STEPS = [
    ("1️⃣ Mueve tu Nariz 🎯", "Mueve tu cabeza/nariz suavemente\npara controlar el puntero en la pantalla."),
    ("2️⃣ Apunta y Clica 🖱️", "Lleva el cursor hasta el campo de abajo\ny haz tu gesto facial para seleccionarlo."),
    ("3️⃣ Di tu Nombre 🎤", "Cuando el campo esté enfocado, di tu\nnombre para escribirlo con tu voz.")
]


class PageHome(SafeDisposableFrame):
    _instance = None

    @classmethod
    def get_instance(cls):
        return cls._instance

    def __init__(self, master, root_callback: callable, **kwargs):
        PageHome._instance = self
        super().__init__(master, **kwargs)
        logger.info("Create PageHome with Research telemetry and Accessibility guidance")
        self.root_callback = root_callback
        self.is_recording = False
        self.session_id = None
        self.total_clicks = 0
        self.total_keystrokes = 0
        self.total_voice_commands = 0
        self.total_distance_px = 0.0
        self.start_time = None
        self.last_cursor_pos = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Scrollable center container
        center = customtkinter.CTkScrollableFrame(self, fg_color="transparent")
        center.grid(row=0, column=0, sticky="nswe", padx=10, pady=5)
        center.grid_columnconfigure(0, weight=1)

        # --- Top Header ---
        header_frame = customtkinter.CTkFrame(center, fg_color="transparent")
        header_frame.grid(row=0, column=0, pady=(5, 10))
        header_frame.grid_columnconfigure(0, weight=1)

        from src.utils import get_resource_path

        light_img = Image.open(get_resource_path("assets/images/FVB.png")).resize(LOGO_SIZE, Image.LANCZOS)
        dark_img = Image.open(get_resource_path("assets/images/FVA.png")).resize(LOGO_SIZE, Image.LANCZOS)
        logo_image = customtkinter.CTkImage(
            light_image=light_img,
            dark_image=dark_img,
            size=LOGO_SIZE)

        logo_label = customtkinter.CTkLabel(header_frame, image=logo_image, text="")
        logo_label.grid(row=0, column=0, pady=(5, 2))

        tagline = customtkinter.CTkLabel(
            header_frame,
            text="Control facial e inteligencia de voz bimodal",
            text_color=TEXT_PRIMARY,
            font=customtkinter.CTkFont(family="Google Sans", size=15, weight="bold"))
        tagline.grid(row=1, column=0, pady=(0, 2))

        # --- Live Status Badges & Voice Captions ---
        status_frame = customtkinter.CTkFrame(center, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER)
        status_frame.grid(row=1, column=0, padx=25, pady=8, sticky="ew")
        status_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Badges
        self.mouse_badge = customtkinter.CTkLabel(
            status_frame, text="🖱️ CONTROL FACIAL", text_color="white",
            corner_radius=8, fg_color="gray", width=180, height=28,
            font=customtkinter.CTkFont(family="Google Sans", size=11, weight="bold"))
        self.mouse_badge.grid(row=0, column=0, padx=10, pady=10)

        self.voice_badge = customtkinter.CTkLabel(
            status_frame, text="🎤 MICRÓFONO", text_color="white",
            corner_radius=8, fg_color="gray", width=180, height=28,
            font=customtkinter.CTkFont(family="Google Sans", size=11, weight="bold"))
        self.voice_badge.grid(row=0, column=1, padx=10, pady=10)

        self.record_badge = customtkinter.CTkLabel(
            status_frame, text="⚪ SESIÓN PAUSADA", text_color="white",
            corner_radius=8, fg_color="gray", width=180, height=28,
            font=customtkinter.CTkFont(family="Google Sans", size=11, weight="bold"))
        self.record_badge.grid(row=0, column=2, padx=10, pady=10)

        # Real-time Voice Transcription Caption Box
        self.speech_monitor_label = customtkinter.CTkLabel(
            status_frame,
            text="🎤 Micrófono pasivo listo. Comienza a hablar...",
            text_color=TEXT_SECONDARY,
            font=customtkinter.CTkFont(family="Google Sans", size=13, slant="italic"))
        self.speech_monitor_label.grid(row=1, column=0, columnspan=3, pady=(5, 12))

        # --- Accessibility step-by-step instructions dashboard ---
        guide_frame = customtkinter.CTkFrame(center, fg_color="transparent")
        guide_frame.grid(row=2, column=0, padx=25, pady=8, sticky="ew")
        guide_frame.grid_columnconfigure((0, 1, 2), weight=1)

        for idx, (title, desc) in enumerate(STEPS):
            step_card = customtkinter.CTkFrame(guide_frame, fg_color=BG_CARD, corner_radius=10, border_width=1, border_color=BORDER)
            step_card.grid(row=0, column=idx, padx=6, pady=4, sticky="nsew")
            step_card.grid_columnconfigure(0, weight=1)

            st_title = customtkinter.CTkLabel(
                step_card, text=title, text_color=TEXT_PRIMARY,
                font=customtkinter.CTkFont(family="Google Sans", size=12, weight="bold"))
            st_title.grid(row=0, column=0, padx=8, pady=(8, 2), sticky="w")

            st_desc = customtkinter.CTkLabel(
                step_card, text=desc, text_color=TEXT_SECONDARY, justify="left",
                font=customtkinter.CTkFont(family="Google Sans", size=11))
            st_desc.grid(row=1, column=0, padx=8, pady=(0, 8), sticky="w")

        # --- Research Participant Registry Card & Exporter ---
        registry_frame = customtkinter.CTkFrame(center, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER)
        registry_frame.grid(row=3, column=0, padx=25, pady=12, sticky="ew")
        registry_frame.grid_columnconfigure(0, weight=2)
        registry_frame.grid_columnconfigure(1, weight=1)

        # Left Column: Registry Input
        self.input_subframe = customtkinter.CTkFrame(registry_frame, fg_color="transparent")
        self.input_subframe.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        self.input_subframe.grid_columnconfigure(0, weight=1)

        # Container for Input fields (Shown when NOT recording)
        self.input_container = customtkinter.CTkFrame(self.input_subframe, fg_color="transparent")
        self.input_container.grid(row=0, column=0, sticky="nsew")
        self.input_container.grid_columnconfigure(0, weight=1)

        self.name_label = customtkinter.CTkLabel(
            self.input_container, text="👤 Nombre del Participante:",
            text_color=TEXT_PRIMARY, font=customtkinter.CTkFont(family="Google Sans", size=13, weight="bold"))
        self.name_label.grid(row=0, column=0, pady=(0, 4), sticky="w")

        self.name_entry = customtkinter.CTkEntry(
            self.input_container, placeholder_text="Apunta con tu nariz, haz clic y escribe tu nombre...",
            height=36, font=customtkinter.CTkFont(family="Google Sans", size=13))
        self.name_entry.grid(row=1, column=0, sticky="ew")

        # Container for Active Session details (Shown when recording)
        self.active_session_frame = customtkinter.CTkFrame(self.input_subframe, fg_color="transparent")
        self.active_session_frame.grid_columnconfigure(0, weight=1)
        self.active_session_frame.grid_columnconfigure(1, weight=1)

        self.active_user_label = customtkinter.CTkLabel(
            self.active_session_frame, text="👤 Participante: None",
            text_color=ACCENT, font=customtkinter.CTkFont(family="Google Sans", size=14, weight="bold"))
        self.active_user_label.grid(row=0, column=0, padx=(0, 15), sticky="w")

        self.timer_label = customtkinter.CTkLabel(
            self.active_session_frame, text="⏱️ Tiempo: 00:00",
            text_color=TEXT_PRIMARY, font=customtkinter.CTkFont(family="Google Sans", size=14, weight="bold"))
        self.timer_label.grid(row=0, column=1, padx=15, sticky="w")

        # Live status feedback text (placed on row 1)
        self.recording_status_label = customtkinter.CTkLabel(
            self.input_subframe, text="Ingresa tu nombre para habilitar el registro de investigación.",
            text_color="gray", font=customtkinter.CTkFont(family="Google Sans", size=11))
        self.recording_status_label.grid(row=1, column=0, pady=(6, 0), sticky="w")

        # Right Column: Usability Control Buttons
        btn_subframe = customtkinter.CTkFrame(registry_frame, fg_color="transparent")
        btn_subframe.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        btn_subframe.grid_columnconfigure(0, weight=1)

        self.export_btn = customtkinter.CTkButton(
            btn_subframe, text="📥 Exportar Datos (CSV)", height=34,
            command=self.export_research_data, fg_color="transparent",
            border_color="#1A73E8", border_width=1, text_color="#1A73E8", hover_color="#E8F0FE",
            font=customtkinter.CTkFont(family="Google Sans", size=12, weight="bold"))
        self.export_btn.grid(row=0, column=0, pady=4, sticky="ew")

        # Register speech callback in background VoiceController
        from src.controllers.voice_controller import VoiceController
        VoiceController().register_ui_callback(self.update_speech_display)

        # Trigger live ticks
        self.after(500, self.update_live_badges)
        self.after(100, self.track_cursor_movement)

    def update_speech_display(self, text: str):
        """Thread-safe UI callback to render captured speech in real-time."""
        self.after(1, lambda: self.speech_monitor_label.configure(
            text=f"🎤 Escuchado: '{text}' ✓",
            text_color="#1A73E8"
        ))

    def update_live_badges(self):
        """Monitors and updates live status flags for vision, mic, and database."""
        if self.is_destroyed:
            return

        # 1. Mouse Control Tracking status
        from src.controllers.mouse_controller import MouseController
        if MouseController()._active_flag.is_set():
            self.mouse_badge.configure(text="🟢 SEGUIMIENTO ACTIVO", fg_color="#188038")
        else:
            self.mouse_badge.configure(text="🔴 SEGUIMIENTO PAUSADO", fg_color="#D93025")

        # 2. Microphone status
        from src.controllers.voice_controller import VoiceController
        if VoiceController().is_enabled():
            self.voice_badge.configure(text="🔵 MICRÓFONO LISTO", fg_color="#1A73E8")
        else:
            self.voice_badge.configure(text="⚪ MICRÓFONO APAGADO", fg_color="gray")

        self.after(500, self.update_live_badges)

    def track_cursor_movement(self):
        """Tracks the overall distance in pixels traveled by the cursor during a recording session."""
        if self.is_destroyed:
            return

        if self.is_recording:
            import pydirectinput
            curr_pos = pydirectinput.position()
            if self.last_cursor_pos is not None:
                dx = curr_pos[0] - self.last_cursor_pos[0]
                dy = curr_pos[1] - self.last_cursor_pos[1]
                dist = math.sqrt(dx*dx + dy*dy)
                self.total_distance_px += dist
            self.last_cursor_pos = curr_pos

        self.after(100, self.track_cursor_movement)

    def update_timer(self):
        """Thread-safe loop to update the session duration timer live."""
        if not self.is_recording or self.is_destroyed:
            return

        elapsed = int(time.time() - self.start_time)
        mins = elapsed // 60
        secs = elapsed % 60
        timer_str = f"⏱️ Tiempo: {mins:02d}:{secs:02d}"

        try:
            self.timer_label.configure(text=timer_str)
        except Exception:
            pass

        self.after(1000, self.update_timer)

    def end_active_session(self):
        """Ends the research session if it is currently active, saving metrics to the database."""
        if hasattr(self, "is_recording") and self.is_recording and getattr(self, "session_id", None):
            from src.utils.database import DatabaseManager
            self.is_recording = False
            duration = time.time() - self.start_time
            try:
                DatabaseManager().end_research_session(
                    session_id=self.session_id,
                    total_clicks=self.total_clicks,
                    total_keystrokes=self.total_keystrokes,
                    total_voice_commands=self.total_voice_commands,
                    total_distance_px=self.total_distance_px,
                    active_duration_seconds=duration
                )
                logger.info(f"Research logging session ended. Duration: {duration:.1f}s")
            except Exception as e:
                logger.error(f"Error ending research session: {e}")

            # Toggle UI panels back to standard name entry
            try:
                self.active_session_frame.grid_remove()
                self.input_container.grid(row=0, column=0, sticky="nsew")
                self.record_badge.configure(text="⚪ SESIÓN PAUSADA", fg_color="gray")
                self.recording_status_label.configure(
                    text="Sesión guardada en SQLite. Listo para exportar.", text_color="gray")
            except Exception:
                pass

    def toggle_recording(self):
        """Starts or stops the usability metrics collection session."""
        from src.config_manager import ConfigManager
        from src.utils.database import DatabaseManager
        from datetime import datetime

        if not self.is_recording:
            # Start usability tracking
            subject = self.name_entry.get().strip()
            # Auto-generate name if empty with timestamp
            if not subject:
                subject = f"Participante_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.name_entry.delete(0, "end")
                self.name_entry.insert(0, subject)

            # Disable voice auto-type immediately to prevent false positives when starting!
            ConfigManager().update_voice_config({"auto_type": False})
            if self.root_callback:
                try:
                    self.root_callback("refresh_voice_write")
                except Exception:
                    pass

            self.is_recording = True
            self.total_clicks = 0
            self.total_keystrokes = 0
            self.total_voice_commands = 0
            self.total_distance_px = 0.0
            self.start_time = time.time()
            self.last_cursor_pos = None

            profile = ConfigManager().curr_profile_name.get()
            self.session_id = DatabaseManager().start_research_session(
                subject_id=subject,
                profile_name=profile,
                subject_first_name=subject,
                subject_last_name=""
            )

            # Toggle UI panels to show active participant and timer inside
            self.input_container.grid_remove()
            self.active_user_label.configure(text=f"👤 Participante: {subject}")
            self.timer_label.configure(text="⏱️ Tiempo: 00:00")
            self.active_session_frame.grid(row=0, column=0, sticky="nsew")

            # Update UI controls
            self.record_badge.configure(text="🔴 GRABANDO SESIÓN", fg_color="#D93025")
            self.recording_status_label.configure(
                text=f"Grabando sesión para {subject}...", text_color="#188038")
            logger.info(f"Research logging session started for {subject}")

            # Trigger live timer updates
            self.update_timer()
        else:
            self.end_active_session()

    def export_research_data(self):
        """Exports tracked usability sessions to a clean, user-friendly CSV file."""
        import csv
        from tkinter import filedialog
        from src.utils.database import DatabaseManager

        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("Archivos CSV", "*.csv")],
                initialfile="sesiones_usabilidad_focuzvoz.csv",
                title="Exportar base de datos de investigación"
            )
            if not file_path:
                return

            db = DatabaseManager()
            sessions = db.get_all_research_sessions()

            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "ID Sesion", "Nombre Participante", "Perfil Utilizado", "Hora Inicio", "Hora Fin",
                    "Clicks Totales", "Teclas Totales", "Comandos Voz", "Eficiencia Cursor (px)", "Duración Uso (seg)"
                ])
                for s in sessions:
                    writer.writerow([
                        s["session_id"], s["subject_id"], s["profile_name"], s["start_time"], s["end_time"],
                        s["total_clicks"], s["total_keystrokes"], s["total_voice_commands"], s["total_distance_px"], s["active_duration_seconds"]
                    ])

            self.recording_status_label.configure(
                text="✓ Base de datos exportada con éxito en CSV.", text_color="#188038")
            logger.info(f"Research data successfully exported to {file_path}")
        except Exception as e:
            logger.error(f"Error exporting database logs: {e}")
            self.recording_status_label.configure(
                text=f"Error al exportar: {e}", text_color="#D93025")

    def enter(self):
        super().enter()
        # Auto-start recording when entering this page
        if not self.is_recording:
            self.after(500, self.toggle_recording)

    def leave(self):
        super().leave()

    def destroy(self):
        if hasattr(self, "is_recording") and self.is_recording:
            try:
                self.end_active_session()
            except Exception as e:
                logger.error(f"Error auto-saving session on destroy: {e}")
        super().destroy()
