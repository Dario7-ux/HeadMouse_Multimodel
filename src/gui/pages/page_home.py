import logging
import time
import math
import random
import customtkinter
from PIL import Image

from src.gui.frames.safe_disposable_frame import SafeDisposableFrame
from src.gui.theme_colors import (
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TITLE,
    ACCENT, BG_CARD, BORDER, BG_PRIMARY
)

logger = logging.getLogger("PageHome")

class PageHome(SafeDisposableFrame):
    _instance = None

    @classmethod
    def get_instance(cls):
        return cls._instance

    def __init__(self, master, root_callback: callable, **kwargs):
        PageHome._instance = self
        super().__init__(master, **kwargs)
        logger.info("Create PageHome with only CSV Export")
        self.root_callback = root_callback

        # Telemetry variables
        self.is_recording = True
        self.total_clicks = 0
        self.total_voice_commands = 0
        self.total_keystrokes = 0
        
        from src.utils.database import DatabaseManager
        try:
            self.session_id = DatabaseManager().start_research_session(
                subject_id="UsuarioLocal",
                profile_name="Default",
                subject_first_name="Usuario",
                subject_last_name="Local"
            )
        except Exception as e:
            import uuid
            self.session_id = str(uuid.uuid4())
            logger.error(f"Error starting research session: {e}")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Main scrollable container
        center = customtkinter.CTkScrollableFrame(self, fg_color="transparent")
        center.grid(row=0, column=0, sticky="nswe", padx=10, pady=5)
        center.grid_columnconfigure(0, weight=1)

        # Header Title
        title_lbl = customtkinter.CTkLabel(
            center,
            text="FocuzVOZ",
            text_color=TEXT_TITLE,
            font=customtkinter.CTkFont(family="Google Sans", size=28, weight="bold")
        )
        title_lbl.grid(row=0, column=0, sticky="w", padx=25, pady=(10, 5))

        tagline = customtkinter.CTkLabel(
            center,
            text="Panel de Control y Exportación de Datos",
            text_color=TEXT_SECONDARY,
            font=customtkinter.CTkFont(family="Google Sans", size=14))
        tagline.grid(row=1, column=0, sticky="w", padx=25, pady=(0, 15))

        # Two Column Layout inside Center
        content_frame = customtkinter.CTkFrame(center, fg_color="transparent")
        content_frame.grid(row=2, column=0, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)

        # Left Column - Cards
        left_col = customtkinter.CTkFrame(content_frame, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=10)
        left_col.grid_columnconfigure(0, weight=1)

        # 1. Hola FocuzVOZ (Left Top)
        hola_frame = customtkinter.CTkFrame(left_col, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER)
        hola_frame.grid(row=0, column=0, pady=(12, 10), sticky="ew")
        hola_frame.grid_columnconfigure(0, weight=1)

        hola_header = customtkinter.CTkLabel(
            hola_frame, text="¡Hola! FocuzVOZ está listo", text_color=TEXT_TITLE,
            font=customtkinter.CTkFont(family="Google Sans", size=18, weight="bold")
        )
        hola_header.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        # --- Onda de voz animada ---
        import tkinter
        self._wave_canvas = tkinter.Canvas(
            hola_frame, height=60, bg="#161B22", highlightthickness=0
        )
        self._wave_canvas.grid(row=1, column=0, sticky="ew", padx=20, pady=(6, 20))
        self._wave_bars = []
        self._wave_speaking = False
        self._wave_anim_id = None
        # Construir barras al cambiar tamaño
        self._wave_canvas.bind("<Configure>", self._build_wave_bars)
        # Registrar callback de voz
        try:
            from src.controllers.voice_controller import VoiceController
            _orig_cb = VoiceController()._ui_callback
            def _voice_wave_cb(text):
                self._wave_speaking = True
                self.after(800, lambda: setattr(self, '_wave_speaking', False))
                if _orig_cb:
                    try:
                        _orig_cb(text)
                    except Exception:
                        pass
            VoiceController().register_ui_callback(_voice_wave_cb)
        except Exception:
            pass
        self._start_wave_animation()
        
        # Spacer
        customtkinter.CTkFrame(left_col, height=5, fg_color="transparent").grid(row=1, column=0)

        # --- Tabla de Gestos ---
        gesture_frame = customtkinter.CTkFrame(left_col, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER)
        gesture_frame.grid(row=1, column=0, pady=(0, 10), sticky="ew")
        gesture_frame.grid_columnconfigure(0, weight=1)

        g_header = customtkinter.CTkLabel(
            gesture_frame, text="🖐 Resumen de Gestos", text_color="#8E44AD",
            font=customtkinter.CTkFont(family="Google Sans", size=15, weight="bold")
        )
        g_header.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 8))

        self._gesture_table_frame = customtkinter.CTkFrame(gesture_frame, fg_color="transparent")
        self._gesture_table_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 15))
        self._gesture_table_frame.grid_columnconfigure(0, weight=1)
        self._refresh_gesture_table()

        refresh_btn = customtkinter.CTkButton(
            gesture_frame, text="↻ Actualizar", height=28, width=100,
            fg_color="#8E44AD", hover_color="#6C3483", corner_radius=6,
            font=customtkinter.CTkFont(family="Google Sans", size=12),
            command=self._refresh_gesture_table
        )
        refresh_btn.grid(row=2, column=0, pady=(0, 15))

        # 2. Exportar Datos (Left Bottom)
        registry_frame = customtkinter.CTkFrame(left_col, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER)
        registry_frame.grid(row=2, column=0, pady=(0, 12), sticky="ew")
        registry_frame.grid_columnconfigure(0, weight=1)
        
        export_header = customtkinter.CTkLabel(
            registry_frame, text="📤 Exportar Datos", text_color="#E8711A",
            font=customtkinter.CTkFont(family="Google Sans", size=15, weight="bold")
        )
        export_header.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 5))
        registry_frame.grid_columnconfigure(0, weight=1)

        self.export_btn = customtkinter.CTkButton(
            registry_frame, text="📄 Exportar Datos (CSV)", height=40,
            command=self.export_research_data, fg_color="#1A73E8",
            text_color="white", hover_color="#1557B0", corner_radius=8,
            font=customtkinter.CTkFont(family="Google Sans", size=14, weight="bold"))
        self.export_btn.grid(row=1, column=0, padx=20, pady=(15, 5), sticky="ew")

        self.recording_status_label = customtkinter.CTkLabel(
            registry_frame, text="Listo para exportar.", text_color="gray", font=customtkinter.CTkFont(family="Google Sans", size=12)
        )
        self.recording_status_label.grid(row=2, column=0, pady=(0, 15))

        # Decorative line
        sep_line = customtkinter.CTkFrame(registry_frame, height=1, fg_color=BORDER)
        sep_line.grid(row=3, column=0, sticky="ew", padx=20, pady=5)

        # Mock UI elements for Export Config
        mock_lbl_1 = customtkinter.CTkLabel(registry_frame, text="Exportar configuración", text_color=TEXT_SECONDARY, font=customtkinter.CTkFont(family="Google Sans", size=12))
        mock_lbl_1.grid(row=4, column=0, sticky="w", padx=20, pady=(5, 0))

        mock_dropdown = customtkinter.CTkOptionMenu(
            registry_frame, values=["Exportar Datos (CSV)", "Exportar Datos (JSON)"],
            fg_color=("#F1F3F4", "#1E232D"), button_color=("#F1F3F4", "#1E232D"),
            button_hover_color=("#E1E3E4", "#2A2F3A"), dropdown_fg_color=("#FFFFFF", "#1E232D"),
            text_color=TEXT_PRIMARY
        )
        mock_dropdown.grid(row=5, column=0, sticky="ew", padx=20, pady=5)

        mock_check = customtkinter.CTkCheckBox(registry_frame, text="Exportar comportar datos CSV", text_color=TEXT_SECONDARY, font=customtkinter.CTkFont(family="Google Sans", size=12))
        mock_check.grid(row=6, column=0, sticky="w", padx=20, pady=5)

        # Status section
        status_frame = customtkinter.CTkFrame(registry_frame, fg_color="transparent")
        status_frame.grid(row=7, column=0, sticky="ew", padx=20, pady=(10, 20))
        status_frame.grid_columnconfigure(0, weight=1)

        status_text_frame = customtkinter.CTkFrame(status_frame, fg_color="transparent")
        status_text_frame.grid(row=0, column=0, sticky="w")
        
        customtkinter.CTkLabel(status_text_frame, text="Estatus", text_color=TEXT_PRIMARY, font=customtkinter.CTkFont(family="Google Sans", size=12, weight="bold")).grid(row=0, column=0, sticky="w")
        customtkinter.CTkLabel(status_text_frame, text="Exportar activo: 200", text_color="#28A745", font=customtkinter.CTkFont(family="Google Sans", size=11)).grid(row=1, column=0, sticky="w")
        customtkinter.CTkLabel(status_text_frame, text="Exportaración: 20 min", text_color=TEXT_SECONDARY, font=customtkinter.CTkFont(family="Google Sans", size=11)).grid(row=2, column=0, sticky="w")

        mock_badge = customtkinter.CTkFrame(status_frame, fg_color=("#F1F3F4", "#1E232D"), corner_radius=8)
        mock_badge.grid(row=0, column=1, sticky="e")
        customtkinter.CTkLabel(mock_badge, text="20 GB", text_color="#1A73E8", font=customtkinter.CTkFont(family="Google Sans", size=18, weight="bold")).pack(padx=15, pady=(5, 0))
        customtkinter.CTkLabel(mock_badge, text="Datos Recientes", text_color="gray", font=customtkinter.CTkFont(family="Google Sans", size=10)).pack(padx=15, pady=(0, 5))

        # Right Column - Voice Commands
        right_col = customtkinter.CTkFrame(content_frame, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", padx=10)
        right_col.grid_columnconfigure(0, weight=1)

        commands_guide_frame = customtkinter.CTkFrame(
            right_col, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER
        )
        commands_guide_frame.grid(row=0, column=0, pady=12, sticky="nsew")
        commands_guide_frame.grid_columnconfigure(0, weight=1)

        guide_header = customtkinter.CTkFrame(commands_guide_frame, fg_color="transparent")
        guide_header.grid(row=0, column=0, padx=15, pady=(15, 4), sticky="ew")
        guide_header.grid_columnconfigure(1, weight=1)
        
        guide_title_lbl = customtkinter.CTkLabel(
            guide_header,
            text="🎤 Comandos Inteligente",
            text_color=TEXT_TITLE,
            font=customtkinter.CTkFont(family="Google Sans", size=16, weight="bold")
        )
        guide_title_lbl.grid(row=0, column=0, sticky="w", padx=(5, 0))

        search_bar = customtkinter.CTkEntry(
            guide_header, placeholder_text="🔍 Buscar Comando...", 
            width=200, height=30, corner_radius=15, fg_color=("#F1F3F4", "#1E232D"),
            border_width=0, text_color=TEXT_PRIMARY
        )
        search_bar.grid(row=0, column=1, sticky="e", padx=(0, 10))

        # Container for the commands list
        commands_list_frame = customtkinter.CTkFrame(commands_guide_frame, fg_color="transparent")
        commands_list_frame.grid(row=1, column=0, padx=10, pady=(5, 15), sticky="nsew")

        def add_category(row, icon, title, commands, color, show_action=False):
            cat_header = customtkinter.CTkFrame(commands_list_frame, fg_color="transparent")
            cat_header.grid(row=row, column=0, sticky="ew", pady=(15, 5), padx=5)
            cat_header.grid_columnconfigure(1, weight=1)

            cat_lbl = customtkinter.CTkLabel(
                cat_header, text=f"{icon}  {title}", text_color=color,
                font=customtkinter.CTkFont(family="Google Sans", size=13, weight="bold")
            )
            cat_lbl.grid(row=0, column=0, sticky="w")
            
            chevron_lbl = customtkinter.CTkLabel(
                cat_header, text="^", text_color=TEXT_SECONDARY,
                font=customtkinter.CTkFont(family="Google Sans", size=14, weight="bold")
            )
            chevron_lbl.grid(row=0, column=2, sticky="e", padx=5)
            
            for i, cmd in enumerate(commands):
                cmd_row = customtkinter.CTkFrame(commands_list_frame, fg_color=("#F1F3F4", "#1E232D") if i % 2 == 0 else "transparent", corner_radius=6)
                cmd_row.grid(row=row+1+i, column=0, sticky="ew", padx=5, pady=2)
                cmd_row.grid_columnconfigure(1, weight=1)

                cmd_lbl = customtkinter.CTkLabel(
                    cmd_row, text=f"🎤 {cmd}", text_color=TEXT_PRIMARY,
                    font=customtkinter.CTkFont(family="Google Sans", size=12, weight="bold")
                )
                cmd_lbl.grid(row=0, column=0, sticky="w", padx=10, pady=8)

                if show_action and i in [0, 3]: # Add actions to some specific rows to match the screenshot
                    action_btn = customtkinter.CTkButton(
                        cmd_row, text="Action", width=60, height=24, fg_color="#E8711A", hover_color="#C85A12",
                        font=customtkinter.CTkFont(family="Google Sans", size=11, weight="bold"), corner_radius=12
                    )
                    action_btn.grid(row=0, column=2, sticky="e", padx=10)
                
            return row + 1 + len(commands)

        next_row = add_category(0, "🖱️", "CLICS DE RATÓN", [
            '"click" / "clic" ➔ Clic derecho',
            '"click izquierdo" ➔ Clic izquierdo',
            '"doble click" ➔ Doble clic derecho',
            '"doble click izquierdo" ➔ Doble clic izquierdo'
        ], "#E8711A", show_action=True)

        next_row = add_category(next_row, "⌨️", "DICTADO Y ESCRITURA", [
            '"escribir" ➔ "Activar escritura" ➔ Activar dictado de voz',
            '"silencio" / "no escribir" ➔ Pausar dictado de voz',
            '"borrar" / "deshacer" ➔ Borrar último segmento',
            '"borrar todo" / "limpiar" ➔ Limpiar todo el texto'
        ], "#8E44AD")

        next_row = add_category(next_row, "🚀", "ATAJOS Y SESIÓN", [
            '"abrir navegador" ➔ "Abrir internet" ➔ Abre Google Chrome',
            '"abrir word" ➔ Abre Microsoft Word',
            '"abrir bloc de notas" ➔ Abre el Bloc de notas',
            '"Focuzvoz finish" ➔ Cerrar programa'
        ], "#E8A01A", show_action=True)

    def _build_wave_bars(self, event=None):
        """Dibuja las barras de la onda de voz en el canvas."""
        try:
            self._wave_canvas.delete("all")
            self._wave_bars = []
            w = self._wave_canvas.winfo_width()
            if w < 10:
                return
            n_bars = max(12, w // 14)
            bar_w = max(4, (w - n_bars * 4) // n_bars)
            for i in range(n_bars):
                x1 = i * (bar_w + 4) + 4
                x2 = x1 + bar_w
                bar = self._wave_canvas.create_rectangle(
                    x1, 30, x2, 31, fill="#E8A01A", outline=""
                )
                self._wave_bars.append((bar, x1, x2))
        except Exception:
            pass

    def _start_wave_animation(self):
        """Anima las barras de la onda según si se está hablando."""
        if self.is_destroyed:
            return
        try:
            h = 60
            mid = h // 2
            for i, (bar, x1, x2) in enumerate(self._wave_bars):
                if self._wave_speaking:
                    amp = random.randint(4, mid - 2)
                else:
                    amp = random.randint(1, 4)
                self._wave_canvas.coords(bar, x1, mid - amp, x2, mid + amp)
                color = "#E8A01A" if self._wave_speaking else "#4A4F5A"
                self._wave_canvas.itemconfig(bar, fill=color)
        except Exception:
            pass
        self._wave_anim_id = self.after(80, self._start_wave_animation)

    def _refresh_gesture_table(self):
        """Actualiza la tabla de resumen de gestos — muestra TODOS los gestos configurados."""
        for w in self._gesture_table_frame.winfo_children():
            w.destroy()

        try:
            from src.config_manager import ConfigManager
            from src.utils.database import DatabaseManager
            import re

            # ── 1. Obtener todos los gestos configurados (ratón + teclado) ──
            mouse_b = ConfigManager().mouse_bindings   # {gesture_name: [device, action, thres, mode]}
            keyb_b  = ConfigManager().keyboard_bindings

            # Unificar sin sobreescribir duplicados
            all_bindings = {}  # gesture_name -> action_label
            action_map = {
                "left":  "Clic izquierdo 🖱️",
                "right": "Clic derecho 🖱️",
                "middle": "Clic central 🖱️",
                "pause": "Pausar/Reanudar ⏸️",
                "reset": "Centrar cursor 🎯",
                "scroll_up": "Scroll arriba ↑",
                "scroll_down": "Scroll abajo ↓",
            }
            for g_name, v in mouse_b.items():
                action = action_map.get(v[1], v[1])
                all_bindings[g_name] = action
            for g_name, v in keyb_b.items():
                if g_name not in all_bindings:
                    action = f"Tecla: {v[1].upper()}"
                    all_bindings[g_name] = action

            # ── 2. Buscar conteos en la base de datos para cada gesto configurado ──
            db = DatabaseManager()
            gesture_counts = {}  # gesture_name -> count
            with db._get_connection() as conn:
                for g_name in all_bindings:
                    clean = re.sub(r'[^a-zA-Z0-9]', '_', g_name.lower().strip())
                    table = f"research_events_gesture_{clean}"
                    try:
                        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    except Exception:
                        count = 0
                    gesture_counts[g_name] = count

            total = sum(gesture_counts.values())
            colors = ["#E8A01A", "#1A73E8", "#34A853", "#E8711A", "#8E44AD", "#E74C3C"]
            sorted_gestures = sorted(gesture_counts.items(), key=lambda x: -x[1])

            # ── 3. Encabezado de columnas ──
            hdr = customtkinter.CTkFrame(self._gesture_table_frame, fg_color=("#F1F3F4", "#1E232D"), corner_radius=6)
            hdr.grid(row=0, column=0, sticky="ew", pady=(0, 4))
            hdr.grid_columnconfigure(0, weight=1)
            for col, (txt, anchor, px) in enumerate([
                ("Gesto / Acción", "w", (10, 0)),
                ("Total", "e", (0, 5)),
                ("%", "e", (10, 10)),
            ]):
                customtkinter.CTkLabel(
                    hdr, text=txt, text_color=TEXT_SECONDARY,
                    font=customtkinter.CTkFont(family="Google Sans", size=12, weight="bold")
                ).grid(row=0, column=col, sticky=anchor, padx=px, pady=5)

            # ── 4. Fila TOTAL general ──
            tot_row = customtkinter.CTkFrame(self._gesture_table_frame, fg_color="#8E44AD", corner_radius=6)
            tot_row.grid(row=1, column=0, sticky="ew", pady=(0, 8))
            tot_row.grid_columnconfigure(0, weight=1)
            customtkinter.CTkLabel(tot_row, text="🖐 TOTAL GESTOS", text_color="white",
                font=customtkinter.CTkFont(family="Google Sans", size=13, weight="bold")
            ).grid(row=0, column=0, sticky="w", padx=10, pady=7)
            customtkinter.CTkLabel(tot_row, text=str(total), text_color="white",
                font=customtkinter.CTkFont(family="Google Sans", size=13, weight="bold")
            ).grid(row=0, column=1, sticky="e", padx=(0, 5), pady=7)
            customtkinter.CTkLabel(tot_row, text="100%", text_color="white",
                font=customtkinter.CTkFont(family="Google Sans", size=12)
            ).grid(row=0, column=2, sticky="e", padx=10, pady=7)

            # ── 5. Una fila por cada gesto configurado ──
            for idx, (g_name, count) in enumerate(sorted_gestures):
                pct = round((count / total * 100) if total > 0 else 0, 1)
                color = colors[idx % len(colors)]
                bg = ("#F1F3F4", "#1E232D") if idx % 2 == 0 else "transparent"
                action_lbl = all_bindings.get(g_name, "")

                row_frame = customtkinter.CTkFrame(
                    self._gesture_table_frame, fg_color=bg, corner_radius=6
                )
                row_frame.grid(row=idx + 2, column=0, sticky="ew", pady=2)
                row_frame.grid_columnconfigure(0, weight=1)

                # Nombre del gesto + acción asignada (en dos líneas)
                name_frame = customtkinter.CTkFrame(row_frame, fg_color="transparent")
                name_frame.grid(row=0, column=0, sticky="w", padx=10, pady=4)
                customtkinter.CTkLabel(
                    name_frame, text=f"● {g_name}", text_color=color,
                    font=customtkinter.CTkFont(family="Google Sans", size=12, weight="bold")
                ).pack(anchor="w")
                customtkinter.CTkLabel(
                    name_frame, text=action_lbl, text_color=TEXT_SECONDARY,
                    font=customtkinter.CTkFont(family="Google Sans", size=10)
                ).pack(anchor="w")

                # Número total
                customtkinter.CTkLabel(
                    row_frame, text=str(count), text_color=TEXT_PRIMARY,
                    font=customtkinter.CTkFont(family="Google Sans", size=13, weight="bold")
                ).grid(row=0, column=1, sticky="e", padx=(0, 5), pady=4)

                # Barra mini + porcentaje
                pct_frame = customtkinter.CTkFrame(row_frame, fg_color="transparent")
                pct_frame.grid(row=0, column=2, sticky="e", padx=10, pady=4)
                bar = customtkinter.CTkProgressBar(pct_frame, width=55, height=8, corner_radius=4)
                bar.configure(progress_color=color, fg_color="#2A2F3A")
                bar.set(count / total if total > 0 else 0)
                bar.pack(side="top", pady=(2, 0))
                customtkinter.CTkLabel(
                    pct_frame, text=f"{pct}%", text_color=TEXT_SECONDARY,
                    font=customtkinter.CTkFont(family="Google Sans", size=10)
                ).pack(side="top")

            if not all_bindings:
                customtkinter.CTkLabel(
                    self._gesture_table_frame,
                    text="No hay gestos configurados aún.", text_color=TEXT_SECONDARY,
                    font=customtkinter.CTkFont(family="Google Sans", size=12)
                ).grid(row=2, column=0, pady=8)
        except Exception as e:
            logger.error(f"Error refreshing gesture table: {e}")

    def export_research_data(self):
        import csv
        import re
        from datetime import datetime
        from tkinter import filedialog
        from src.utils.database import DatabaseManager
        import src.shape_list as shape_list

        try:
            file_path = filedialog.asksaveasfilename(
                title="Guardar reporte de datos FocuzVoz",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile=f"focuzvoz_reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            if not file_path:
                return

            db = DatabaseManager()
            sessions = db.get_all_research_sessions()

            # ── Columnas fijas: TODOS los gestos posibles de la app (sin "None") ──
            ALL_GESTURES = [g for g in shape_list.available_gestures_keys if g != "None"]
            # Nombre de tabla en BD para cada gesto
            def gesture_to_table(g):
                return "research_events_gesture_" + re.sub(r'[^a-zA-Z0-9]', '_', g.lower().strip())

            # ── Columnas fijas: TODOS los comandos de voz conocidos en la app ──
            ALL_VOICE = [
                "abrir internet", "abrir word", "abrir bloc de notas",
            ]
            def voice_to_table(v):
                return "research_events_voice_" + re.sub(r'[^a-zA-Z0-9]', '_', v.lower().strip())

            with db._get_connection() as conn:
                # Pre-calcular conteos por (session_id, tabla)
                g_session_counts = {}
                for g in ALL_GESTURES:
                    table = gesture_to_table(g)
                    try:
                        for r in conn.execute(
                            f"SELECT session_id, COUNT(*) FROM {table} GROUP BY session_id;"
                        ).fetchall():
                            g_session_counts[(r[0], table)] = r[1]
                    except Exception:
                        pass  # tabla aún no creada

                v_session_counts = {}
                for v in ALL_VOICE:
                    table = voice_to_table(v)
                    try:
                        for r in conn.execute(
                            f"SELECT session_id, COUNT(*) FROM {table} GROUP BY session_id;"
                        ).fetchall():
                            v_session_counts[(r[0], table)] = r[1]
                    except Exception:
                        pass

            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)

                # ── Encabezado: métricas base + un campo por CADA gesto + un campo por CADA voz ──
                header = [
                    "Participante", "Perfil", "Hora Inicio", "Hora Fin",
                    "Duracion (seg)", "Clicks Totales", "Teclas Totales",
                    "Comandos Voz Totales", "Distancia Cursor (px)",
                    "Distancia Cursor (cm)", "Gestos Totales",
                ]
                for g in ALL_GESTURES:
                    translated_g = shape_list.gesture_translation_map.get(g, g)
                    header.append(f"Gestos {translated_g}")
                for v in ALL_VOICE:
                    header.append(f"Vocz {v.title()}")
                writer.writerow(header)

                # ── Una fila por sesión ──
                for s in sessions:
                    sid = s["session_id"]
                    
                    # Si es la sesión activa actual, obtener estadísticas vivas en tiempo real
                    if hasattr(self, 'session_id') and self.session_id and sid == self.session_id:
                        from src.controllers.mouse_controller import MouseController
                        stats = MouseController().get_session_stats()
                        dist_px = stats["total_distance_px"]
                        dist_cm = round(dist_px * 2.54 / 96.0, 2)
                        duration_sec = stats["total_session_seconds"]
                        clicks = self.total_clicks
                        keystrokes = self.total_keystrokes
                        voice_commands = self.total_voice_commands
                    else:
                        dist_px = round(float(s["total_distance_px"] or 0), 2)
                        dist_cm = round(dist_px * 2.54 / 96.0, 2)
                        duration_sec = round(float(s["active_duration_seconds"] or 0), 2)
                        clicks = s["total_clicks"]
                        keystrokes = s["total_keystrokes"]
                        voice_commands = s["total_voice_commands"]

                    name = (f"{s.get('subject_first_name', '')} {s.get('subject_last_name', '')}".strip()
                            or s["subject_id"])

                    g_counts = [g_session_counts.get((sid, gesture_to_table(g)), 0) for g in ALL_GESTURES]
                    v_counts = [v_session_counts.get((sid, voice_to_table(v)), 0) for v in ALL_VOICE]

                    writer.writerow([
                        name, s["profile_name"],
                        s["start_time"], s["end_time"] or "En curso",
                        duration_sec, clicks, keystrokes,
                        voice_commands, dist_px, dist_cm,
                        sum(g_counts),
                    ] + g_counts + v_counts)

            self.recording_status_label.configure(
                text="✓ Reporte exportado exitosamente.", text_color="#188038")
            logger.info(f"Research data exported to: {file_path}")
        except Exception as e:
            logger.error(f"Error exporting database logs: {e}")
            self.recording_status_label.configure(
                text=f"Error al exportar: {e}", text_color="#D93025")

    def enter(self):
        super().enter()

    def leave(self):
        super().leave()

    def end_active_session(self):
        try:
            if hasattr(self, 'session_id') and self.session_id:
                from src.utils.database import DatabaseManager
                from src.controllers.mouse_controller import MouseController
                stats = MouseController().get_session_stats()
                DatabaseManager().end_research_session(
                    session_id=self.session_id,
                    total_clicks=self.total_clicks,
                    total_keystrokes=self.total_keystrokes,
                    total_voice_commands=self.total_voice_commands,
                    total_distance_px=stats["total_distance_px"],
                    active_duration_seconds=stats["total_session_seconds"]
                )
                logger.info(
                    f"Session closed successfully via end_active_session — dist={stats['total_distance_px']}px, "
                    f"duration={stats['total_session_seconds']}s"
                )
                self.session_id = None
        except Exception as e:
            logger.error(f"Error ending active session: {e}")

    def destroy(self):
        self.end_active_session()
        super().destroy()
