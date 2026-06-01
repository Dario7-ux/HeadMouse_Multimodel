import logging
import time
import math
import customtkinter
from PIL import Image

from src.gui.frames.safe_disposable_frame import SafeDisposableFrame
from src.gui.theme_colors import (
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TITLE,
    ACCENT, BG_CARD, BORDER, BG_PRIMARY
)

logger = logging.getLogger("PageHome")
LOGO_SIZE = (240, 118)

# Instructions details
STEPS = [
    ("Paso 1: Mueve tu Nariz", "Mueve tu cabeza/nariz suavemente\npara controlar el puntero en la pantalla."),
    ("Paso 2: Apunta y Clica", "Lleva el cursor hasta el campo de abajo\ny haz tu gesto facial para seleccionarlo."),
    ("Paso 3: Di tu Nombre", "Cuando el campo esté enfocado, di tu\nnombre para escribirlo con tu voz.")
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
        
        # We split center into two main columns
        center.grid_columnconfigure(0, weight=1, minsize=420)
        center.grid_columnconfigure(1, weight=1, minsize=420)

        # --- Top Header (Spans across both columns) ---
        header_frame = customtkinter.CTkFrame(center, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, pady=(10, 15), sticky="w")
        header_frame.grid_columnconfigure(0, weight=1)

        title_lbl = customtkinter.CTkLabel(
            header_frame,
            text="FocuzVoz - Panel de Control",
            text_color=TEXT_TITLE,
            font=customtkinter.CTkFont(family="Google Sans", size=24, weight="bold")
        )
        title_lbl.grid(row=0, column=0, sticky="w", padx=25)

        tagline = customtkinter.CTkLabel(
            header_frame,
            text="Monitoreo en tiempo real y asistencia de voz bimodal",
            text_color=TEXT_SECONDARY,
            font=customtkinter.CTkFont(family="Google Sans", size=13))
        tagline.grid(row=1, column=0, sticky="w", padx=25, pady=(2, 0))

        # --- TWO MAIN COLUMN CONTAINER FRAMES ---
        left_column = customtkinter.CTkFrame(center, fg_color="transparent")
        left_column.grid(row=1, column=0, sticky="nsew", padx=(10, 10), pady=0)
        left_column.grid_columnconfigure(0, weight=1)

        right_column = customtkinter.CTkFrame(center, fg_color="transparent")
        right_column.grid(row=1, column=1, sticky="nsew", padx=(10, 10), pady=0)
        right_column.grid_columnconfigure(0, weight=1)

        # ==========================================
        # === COLUMN 0 (LEFT): MONITOREO, REGISTRO & PASOS ===
        # ==========================================

        # --- Live Status Badges & Voice Captions ---
        status_frame = customtkinter.CTkFrame(left_column, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER)
        status_frame.grid(row=0, column=0, padx=15, pady=8, sticky="ew")
        status_frame.grid_columnconfigure((0, 1), weight=1)

        # Badges (2x2 layout inside left_column to avoid overflow)
        self.mouse_badge = customtkinter.CTkLabel(
            status_frame, text="🖱️ CONTROL FACIAL", text_color="white",
            corner_radius=8, fg_color="gray", height=28,
            font=customtkinter.CTkFont(family="Google Sans", size=11, weight="bold"))
        self.mouse_badge.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.voice_badge = customtkinter.CTkLabel(
            status_frame, text="🎤 MICRÓFONO", text_color="white",
            corner_radius=8, fg_color="gray", height=28,
            font=customtkinter.CTkFont(family="Google Sans", size=11, weight="bold"))
        self.voice_badge.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.record_badge = customtkinter.CTkLabel(
            status_frame, text="⚪ SESIÓN PAUSADA", text_color="white",
            corner_radius=8, fg_color="gray", height=28,
            font=customtkinter.CTkFont(family="Google Sans", size=11, weight="bold"))
        self.record_badge.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")

        # Real-time Voice Transcription Caption Box
        self.speech_monitor_label = customtkinter.CTkLabel(
            status_frame,
            text="🎤 Micrófono pasivo listo. Comienza a hablar...",
            text_color=TEXT_SECONDARY,
            wraplength=380,
            font=customtkinter.CTkFont(family="Google Sans", size=13, slant="italic"))
        self.speech_monitor_label.grid(row=2, column=0, columnspan=2, pady=(5, 12), sticky="ew")

        # --- Research Participant Registry Card & Exporter ---
        registry_frame = customtkinter.CTkFrame(left_column, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER)
        registry_frame.grid(row=1, column=0, padx=15, pady=12, sticky="ew")
        registry_frame.grid_columnconfigure(0, weight=1)

        # Left Column: Registry Input
        self.input_subframe = customtkinter.CTkFrame(registry_frame, fg_color="transparent")
        self.input_subframe.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="nsew")
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
            self.input_container, placeholder_text="Apunta con tu nariz, haz clic y escribe...",
            height=36, font=customtkinter.CTkFont(family="Google Sans", size=13))
        self.name_entry.grid(row=1, column=0, sticky="ew")

        # Container for Active Session details (Shown when recording - Stacked vertically to avoid layout squeeze)
        self.active_session_frame = customtkinter.CTkFrame(self.input_subframe, fg_color="transparent")
        self.active_session_frame.grid_columnconfigure(0, weight=1)

        self.active_user_label = customtkinter.CTkLabel(
            self.active_session_frame, text="👤 Participante: None",
            text_color=ACCENT, font=customtkinter.CTkFont(family="Google Sans", size=13, weight="bold"))
        self.active_user_label.grid(row=0, column=0, pady=(2, 2), sticky="w")

        self.timer_label = customtkinter.CTkLabel(
            self.active_session_frame, text="⏱️ Tiempo: 00:00",
            text_color=TEXT_PRIMARY, font=customtkinter.CTkFont(family="Google Sans", size=13, weight="bold"))
        self.timer_label.grid(row=1, column=0, pady=(2, 2), sticky="w")

        # Live status feedback text (placed on row 1)
        self.recording_status_label = customtkinter.CTkLabel(
            self.input_subframe, text="Ingresa tu nombre para habilitar el registro de investigación.",
            text_color="gray", font=customtkinter.CTkFont(family="Google Sans", size=11))
        self.recording_status_label.grid(row=2, column=0, pady=(6, 0), sticky="w")

        # Bottom Subframe for Buttons
        btn_subframe = customtkinter.CTkFrame(registry_frame, fg_color="transparent")
        btn_subframe.grid(row=1, column=0, padx=15, pady=(5, 15), sticky="nsew")
        btn_subframe.grid_columnconfigure(0, weight=1)

        self.export_btn = customtkinter.CTkButton(
            btn_subframe, text="📥 Exportar Datos (CSV)", height=34,
            command=self.export_research_data, fg_color="transparent",
            border_color="#1A73E8", border_width=1, text_color="#1A73E8", hover_color="#E8F0FE",
            font=customtkinter.CTkFont(family="Google Sans", size=12, weight="bold"))
        self.export_btn.grid(row=0, column=0, pady=4, sticky="ew")

        # --- Accessibility step-by-step instructions dashboard (Sleek Timeline Card) ---
        guide_frame = customtkinter.CTkFrame(left_column, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER)
        guide_frame.grid(row=2, column=0, padx=15, pady=8, sticky="ew")
        guide_frame.grid_columnconfigure(0, weight=1)

        # Header for the guide with left blue accent bar
        guide_header = customtkinter.CTkFrame(guide_frame, fg_color="transparent")
        guide_header.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="w")
        
        accent_bar_g = customtkinter.CTkFrame(guide_header, fg_color=ACCENT, width=4, height=18, corner_radius=2)
        accent_bar_g.grid(row=0, column=0, padx=(0, 10), sticky="ns")

        guide_header_lbl = customtkinter.CTkLabel(
            guide_header, text="Pasos para empezar a usar FocuzVoz", text_color=TEXT_TITLE,
            font=customtkinter.CTkFont(family="Google Sans", size=14, weight="bold"))
        guide_header_lbl.grid(row=0, column=1, sticky="w")

        # Container for Steps
        steps_container = customtkinter.CTkFrame(guide_frame, fg_color="transparent")
        steps_container.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="ew")
        steps_container.grid_columnconfigure(0, weight=1)

        for idx, (title, desc) in enumerate(STEPS):
            step_row = customtkinter.CTkFrame(steps_container, fg_color="transparent")
            step_row.grid(row=idx, column=0, pady=6, sticky="ew")
            step_row.grid_columnconfigure(1, weight=1)

            # Circular number icon
            num_lbl = customtkinter.CTkLabel(
                step_row, text=f" {idx + 1} ", text_color="white", fg_color=ACCENT,
                corner_radius=12, width=24, height=24,
                font=customtkinter.CTkFont(family="Google Sans", size=11, weight="bold")
            )
            num_lbl.grid(row=0, column=0, padx=(0, 12), sticky="nw")

            # Text block next to number
            text_block = customtkinter.CTkFrame(step_row, fg_color="transparent")
            text_block.grid(row=0, column=1, sticky="ew")
            text_block.grid_columnconfigure(0, weight=1)

            st_title = customtkinter.CTkLabel(
                text_block, text=title.replace(f"Paso {idx+1}: ", ""), text_color=TEXT_PRIMARY,
                font=customtkinter.CTkFont(family="Google Sans", size=12, weight="bold"))
            st_title.grid(row=0, column=0, sticky="w")

            st_desc = customtkinter.CTkLabel(
                text_block, text=desc, text_color=TEXT_SECONDARY, justify="left",
                font=customtkinter.CTkFont(family="Google Sans", size=11))
            st_desc.grid(row=1, column=0, sticky="w")

        # ==========================================
        # === COLUMN 1 (RIGHT): COMANDOS DE VOZ COMPLETO ===
        # ==========================================

        # --- Voice Commands Quick Guide Card ---
        commands_guide_frame = customtkinter.CTkFrame(
            right_column, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER
        )
        commands_guide_frame.grid(row=0, column=0, padx=15, pady=8, sticky="nsew")
        commands_guide_frame.grid_columnconfigure(0, weight=1)

        # Title block with vertical accent bar
        guide_header = customtkinter.CTkFrame(commands_guide_frame, fg_color="transparent")
        guide_header.grid(row=0, column=0, padx=15, pady=(15, 4), sticky="w")
        guide_header.grid_rowconfigure(0, weight=1)

        accent_bar = customtkinter.CTkFrame(guide_header, fg_color=ACCENT, width=4, height=18, corner_radius=2)
        accent_bar.grid(row=0, column=0, padx=(0, 10), sticky="ns")

        guide_title_lbl = customtkinter.CTkLabel(
            guide_header,
            text="Guía Rápida de Comandos de Voz",
            text_color=TEXT_TITLE,
            font=customtkinter.CTkFont(family="Google Sans", size=15, weight="bold")
        )
        guide_title_lbl.grid(row=0, column=1, sticky="w")

        guide_desc_lbl = customtkinter.CTkLabel(
            commands_guide_frame,
            text="Di cualquiera de las siguientes frases para controlar el sistema con tu voz:",
            text_color=TEXT_SECONDARY,
            font=customtkinter.CTkFont(family="Google Sans", size=12)
        )
        guide_desc_lbl.grid(row=1, column=0, padx=15, pady=(0, 8), sticky="w")

        # Category grids (1 column layout - stacked vertically so they are wide and perfectly clear!)
        categories_frame = customtkinter.CTkFrame(commands_guide_frame, fg_color="transparent")
        categories_frame.grid(row=2, column=0, padx=12, pady=(0, 12), sticky="ew")
        categories_frame.grid_columnconfigure(0, weight=1)

        # Local helper function to draw perfectly aligned and colorized command rows
        def add_command_row(card, row_idx, command_text, action_text):
            cmd_lbl = customtkinter.CTkLabel(
                card, text=command_text,
                text_color=("#1B66C9", "#8AB4F8"),
                font=customtkinter.CTkFont(family="Google Sans", size=12, weight="bold")
            )
            cmd_lbl.grid(row=row_idx, column=0, padx=(15, 10), pady=5, sticky="w")
            
            arrow_lbl = customtkinter.CTkLabel(
                card, text="➔",
                text_color=TEXT_SECONDARY,
                font=customtkinter.CTkFont(family="Google Sans", size=12)
            )
            arrow_lbl.grid(row=row_idx, column=1, padx=10, pady=5)
            
            act_lbl = customtkinter.CTkLabel(
                card, text=action_text,
                text_color=TEXT_PRIMARY,
                font=customtkinter.CTkFont(family="Google Sans", size=12)
            )
            act_lbl.grid(row=row_idx, column=2, padx=(10, 15), pady=5, sticky="w")

        # --- CATEGORY 1: Clics de Ratón ---
        cat1 = customtkinter.CTkFrame(categories_frame, fg_color=BG_PRIMARY, corner_radius=10, border_width=1, border_color=BORDER)
        cat1.grid(row=0, column=0, padx=6, pady=6, sticky="ew")
        cat1.grid_columnconfigure(0, minsize=210)  # Align all columns perfectly!
        cat1.grid_columnconfigure(1, minsize=30)
        cat1.grid_columnconfigure(2, weight=1)
        
        lbl_cat1 = customtkinter.CTkLabel(
            cat1, text="Clics de Ratón", text_color=ACCENT,
            font=customtkinter.CTkFont(family="Google Sans", size=14, weight="bold")
        )
        lbl_cat1.grid(row=0, column=0, columnspan=3, padx=15, pady=(12, 6), sticky="w")
        
        add_command_row(cat1, 1, '"click" / "clic" / "click izquierdo"', "Clic izquierdo")
        add_command_row(cat1, 2, '"click derecho" / "clic derecho"', "Clic derecho")
        add_command_row(cat1, 3, '"doble click" / "doble clic"', "Doble clic izquierdo")
        add_command_row(cat1, 4, '"doble click derecho"', "Doble clic derecho")

        # --- CATEGORY 2: Dictado y Escritura ---
        cat2 = customtkinter.CTkFrame(categories_frame, fg_color=BG_PRIMARY, corner_radius=10, border_width=1, border_color=BORDER)
        cat2.grid(row=1, column=0, padx=6, pady=6, sticky="ew")
        cat2.grid_columnconfigure(0, minsize=210)  # Align all columns perfectly!
        cat2.grid_columnconfigure(1, minsize=30)
        cat2.grid_columnconfigure(2, weight=1)
        
        lbl_cat2 = customtkinter.CTkLabel(
            cat2, text="Dictado y Edición", text_color=ACCENT,
            font=customtkinter.CTkFont(family="Google Sans", size=14, weight="bold")
        )
        lbl_cat2.grid(row=0, column=0, columnspan=3, padx=15, pady=(12, 6), sticky="w")
        
        add_command_row(cat2, 1, '"escribir" / "activar escritura"', "Activar dictado de voz")
        add_command_row(cat2, 2, '"silencio" / "no escribir"', "Pausar dictado de voz")
        add_command_row(cat2, 3, '"borrar" / "deshacer"', "Borrar último segmento")
        add_command_row(cat2, 4, '"borrar todo" / "limpiar"', "Limpiar todo el texto")

        # --- CATEGORY 4: Atajos y Sesión ---
        cat4 = customtkinter.CTkFrame(categories_frame, fg_color=BG_PRIMARY, corner_radius=10, border_width=1, border_color=BORDER)
        cat4.grid(row=2, column=0, padx=6, pady=6, sticky="ew")
        cat4.grid_columnconfigure(0, minsize=210)  # Align all columns perfectly!
        cat4.grid_columnconfigure(1, minsize=30)
        cat4.grid_columnconfigure(2, weight=1)
        
        lbl_cat4 = customtkinter.CTkLabel(
            cat4, text="Atajos y Sesión", text_color=ACCENT,
            font=customtkinter.CTkFont(family="Google Sans", size=14, weight="bold")
        )
        lbl_cat4.grid(row=0, column=0, columnspan=3, padx=15, pady=(12, 6), sticky="w")
        
        add_command_row(cat4, 1, '"abrir navegador" / "abrir internet"', "Google Chrome")
        add_command_row(cat4, 2, '"abrir bloc de notas" / "abrir word"', "Bloc de notas o Word")
        add_command_row(cat4, 3, '"focuzvoz finish"', "Cerrar programa")

        # Register speech callback in background VoiceController
        from src.controllers.voice_controller import VoiceController
        VoiceController().register_ui_callback(self.update_speech_display)

        # ─── Card: Gestos de Raton configurados ───────────────────────────────
        self._mouse_bindings_frame = customtkinter.CTkFrame(
            right_column, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER
        )
        self._mouse_bindings_frame.grid(row=1, column=0, padx=15, pady=8, sticky="ew")
        self._mouse_bindings_frame.grid_columnconfigure(0, weight=1)

        _mb_header = customtkinter.CTkFrame(self._mouse_bindings_frame, fg_color="transparent")
        _mb_header.grid(row=0, column=0, padx=15, pady=(15, 4), sticky="w")
        _mb_accent = customtkinter.CTkFrame(_mb_header, fg_color="#E8711A", width=4, height=18, corner_radius=2)
        _mb_accent.grid(row=0, column=0, padx=(0, 10), sticky="ns")
        customtkinter.CTkLabel(
            _mb_header, text="Gestos de Raton Configurados",
            text_color=TEXT_TITLE,
            font=customtkinter.CTkFont(family="Google Sans", size=15, weight="bold")
        ).grid(row=0, column=1, sticky="w")

        customtkinter.CTkLabel(
            self._mouse_bindings_frame,
            text="Gestos faciales asignados a acciones del raton:",
            text_color=TEXT_SECONDARY,
            font=customtkinter.CTkFont(family="Google Sans", size=12)
        ).grid(row=1, column=0, padx=15, pady=(0, 6), sticky="w")

        # Container dinamico — se reconstruye en refresh_gesture_bindings()
        self._mouse_bindings_inner = customtkinter.CTkFrame(
            self._mouse_bindings_frame, fg_color="transparent")
        self._mouse_bindings_inner.grid(row=2, column=0, padx=12, pady=(0, 12), sticky="ew")
        self._mouse_bindings_inner.grid_columnconfigure(0, weight=1)

        # ─── Card: Teclas por Gesto configuradas ──────────────────────────────
        self._kb_bindings_frame = customtkinter.CTkFrame(
            right_column, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER
        )
        self._kb_bindings_frame.grid(row=2, column=0, padx=15, pady=8, sticky="ew")
        self._kb_bindings_frame.grid_columnconfigure(0, weight=1)

        _kb_header = customtkinter.CTkFrame(self._kb_bindings_frame, fg_color="transparent")
        _kb_header.grid(row=0, column=0, padx=15, pady=(15, 4), sticky="w")
        _kb_accent = customtkinter.CTkFrame(_kb_header, fg_color="#8E44AD", width=4, height=18, corner_radius=2)
        _kb_accent.grid(row=0, column=0, padx=(0, 10), sticky="ns")
        customtkinter.CTkLabel(
            _kb_header, text="Teclas por Gesto Configuradas",
            text_color=TEXT_TITLE,
            font=customtkinter.CTkFont(family="Google Sans", size=15, weight="bold")
        ).grid(row=0, column=1, sticky="w")

        customtkinter.CTkLabel(
            self._kb_bindings_frame,
            text="Gestos faciales asignados a teclas del teclado:",
            text_color=TEXT_SECONDARY,
            font=customtkinter.CTkFont(family="Google Sans", size=12)
        ).grid(row=1, column=0, padx=15, pady=(0, 6), sticky="w")

        self._kb_bindings_inner = customtkinter.CTkFrame(
            self._kb_bindings_frame, fg_color="transparent")
        self._kb_bindings_inner.grid(row=2, column=0, padx=12, pady=(0, 12), sticky="ew")
        self._kb_bindings_inner.grid_columnconfigure(0, weight=1)

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

    def refresh_gesture_bindings(self):
        """Reconstruye las cards de gestos de raton y teclas con los bindings actuales del perfil activo."""
        from src.config_manager import ConfigManager
        import src.shape_list as shape_list

        # Traducciones legibles para acciones del raton
        MOUSE_ACTION_LABELS = {
            "left":   "Clic izquierdo",
            "right":  "Clic derecho",
            "middle": "Clic central",
            "pause":  "Pausar / Reanudar cursor",
            "reset":  "Restablecer cursor al centro",
            "cycle":  "Cambiar entre monitores",
        }
        MODE_LABELS = {"hold": "Mantener", "single": "Pulsar"}
        GESTURE_LABELS = shape_list.gesture_translation_map

        def _rebuild_card(inner_frame, bindings, action_labels, show_mode=True):
            """Destruye y reconstruye los widgets dentro del inner_frame."""
            for w in inner_frame.winfo_children():
                w.destroy()

            if not bindings:
                empty_lbl = customtkinter.CTkLabel(
                    inner_frame,
                    text="Sin asignaciones configuradas. Ve a la seccion correspondiente para agregar.",
                    text_color="gray",
                    font=customtkinter.CTkFont(family="Google Sans", size=12),
                    wraplength=380, justify="left"
                )
                empty_lbl.grid(row=0, column=0, padx=10, pady=10, sticky="w")
                return

            card = customtkinter.CTkFrame(
                inner_frame, fg_color=BG_PRIMARY, corner_radius=10,
                border_width=1, border_color=BORDER)
            card.grid(row=0, column=0, padx=6, pady=4, sticky="ew")
            card.grid_columnconfigure(0, minsize=190)
            card.grid_columnconfigure(1, minsize=26)
            card.grid_columnconfigure(2, weight=1)
            if show_mode:
                card.grid_columnconfigure(3, minsize=80)

            for row_idx, (gesture, vals) in enumerate(bindings.items()):
                _, action, thres, mode = vals
                gesture_label = GESTURE_LABELS.get(gesture, gesture)
                action_label  = action_labels.get(action, action.upper())
                mode_label    = MODE_LABELS.get(mode, mode)
                thres_pct     = int(round(float(thres) * 100))

                # Columna 0: gesto
                gesture_lbl = customtkinter.CTkLabel(
                    card, text=f"  {gesture_label}",
                    text_color=("#1B66C9", "#8AB4F8"),
                    font=customtkinter.CTkFont(family="Google Sans", size=12, weight="bold"),
                    anchor="w"
                )
                gesture_lbl.grid(row=row_idx, column=0, padx=(10, 4), pady=5, sticky="w")

                # Columna 1: flecha
                customtkinter.CTkLabel(
                    card, text="➔",
                    text_color=TEXT_SECONDARY,
                    font=customtkinter.CTkFont(family="Google Sans", size=12)
                ).grid(row=row_idx, column=1, padx=4, pady=5)

                # Columna 2: accion + umbral
                action_text = f"{action_label}  ({thres_pct}%)"
                customtkinter.CTkLabel(
                    card, text=action_text,
                    text_color=TEXT_PRIMARY,
                    font=customtkinter.CTkFont(family="Google Sans", size=12),
                    anchor="w"
                ).grid(row=row_idx, column=2, padx=(4, 8), pady=5, sticky="w")

                # Columna 3: modo (solo para teclado)
                if show_mode:
                    mode_color = "#188038" if mode == "single" else "#1A73E8"
                    mode_tag = customtkinter.CTkLabel(
                        card, text=f"  {mode_label}  ",
                        text_color="white",
                        fg_color=mode_color,
                        corner_radius=6,
                        font=customtkinter.CTkFont(family="Google Sans", size=10, weight="bold")
                    )
                    mode_tag.grid(row=row_idx, column=3, padx=(4, 10), pady=5, sticky="e")

                # Linea separadora (excepto ultima)
                if row_idx < len(bindings) - 1:
                    sep = customtkinter.CTkFrame(card, height=1, fg_color=BORDER, corner_radius=0)
                    sep.grid(row=row_idx, column=0, columnspan=4 if show_mode else 3,
                             padx=10, pady=0, sticky="ew")

        try:
            mouse_bindings = ConfigManager().mouse_bindings
            _rebuild_card(self._mouse_bindings_inner, mouse_bindings, MOUSE_ACTION_LABELS, show_mode=False)
        except Exception as e:
            logger.error(f"Error al reconstruir card de gestos de raton: {e}")

        try:
            kb_bindings = ConfigManager().keyboard_bindings
            _rebuild_card(self._kb_bindings_inner, kb_bindings, {}, show_mode=True)
        except Exception as e:
            logger.error(f"Error al reconstruir card de teclas: {e}")

    def enter(self):
        super().enter()
        # Auto-start recording when entering this page
        if not self.is_recording:
            self.after(500, self.toggle_recording)
        # Refresh gesture binding cards every time the user navigates to home
        self.after(50, self.refresh_gesture_bindings)

    def leave(self):
        super().leave()

    def destroy(self):
        if hasattr(self, "is_recording") and self.is_recording:
            try:
                self.end_active_session()
            except Exception as e:
                logger.error(f"Error auto-saving session on destroy: {e}")
        super().destroy()
