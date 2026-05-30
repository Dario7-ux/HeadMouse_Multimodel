from functools import partial
import tkinter as tk

import customtkinter

from src.config_manager import ConfigManager
from src.gui.frames.safe_disposable_frame import SafeDisposableFrame
from src.gui.theme_colors import (
    MENU_BG, MENU_BTN_HOVER, MENU_BTN_ACTIVE,
    MENU_BTN_TEXT, MENU_BTN_ACTIVE_TEXT, MENU_DIVIDER,
    ACCENT, TEXT_PRIMARY, TEXT_SECONDARY, BG_CARD
)

# Elementos del menú: (page_key, emoji, label)
MENU_ITEMS = [
    ("page_home", "🏠", "Inicio"),
    ("page_camera", "📷", "Cámara"),
    ("page_cursor", "🖱️", "Cursor"),
    ("page_gestures", "✋", "Gestos"),
    ("page_keyboard", "⌨️", "Teclado"),
    ("page_voice", "🎤", "Voz"),
]


class FrameMenu(SafeDisposableFrame):

    def __init__(self, master, master_callback: callable, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_rowconfigure(len(MENU_ITEMS) + 3, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_propagate(False)
        self.configure(fg_color=MENU_BG)

        self.master_callback = master_callback
        self.current_active = None

        # ── Botón selector de perfil ──
        profile_btn = customtkinter.CTkButton(
            master=self,
            textvariable=ConfigManager().curr_profile_name,
            height=36,
            width=220,
            corner_radius=10,
            border_width=1,
            border_color=MENU_DIVIDER,
            fg_color=BG_CARD,
            hover_color=MENU_BTN_HOVER,
            text_color=TEXT_PRIMARY,
            font=customtkinter.CTkFont(family="Google Sans", size=13),
            anchor="w",
            command=partial(self.master_callback, "show_profile_switcher"))

        profile_btn.grid(row=0,
                         column=0,
                         padx=15,
                         pady=(15, 10),
                         sticky="nw")

        # ── Botones de navegación ──
        self.btns = {}
        for idx, (page_key, emoji, label) in enumerate(MENU_ITEMS):
            btn = customtkinter.CTkButton(
                master=self,
                text=f"  {emoji}  {label}",
                anchor="w",
                height=40,
                width=220,
                corner_radius=10,
                border_width=0,
                font=customtkinter.CTkFont(family="Google Sans", size=14),
                fg_color="transparent",
                text_color=MENU_BTN_TEXT,
                hover_color=MENU_BTN_HOVER,
                command=partial(
                    self.master_callback,
                    function_name="change_page",
                    args={"target": page_key}))

            btn.grid(row=idx + 1,
                     column=0,
                     padx=15,
                     pady=2,
                     sticky="nw")
            self.btns[page_key] = btn

        # ── Separador ──
        separator = customtkinter.CTkFrame(
            master=self,
            height=1,
            fg_color=MENU_DIVIDER,
            corner_radius=0)
        separator.grid(row=len(MENU_ITEMS) + 1,
                       column=0,
                       padx=25,
                       pady=8,
                       sticky="ew")

        # ── Interruptor de Escritura por Voz ──
        self.voice_write_var = tk.BooleanVar()
        self.voice_write_var.set(ConfigManager().get_voice_config().get("auto_type", True))
        
        self.voice_write_switch = customtkinter.CTkSwitch(
            master=self,
            text="✍️  Escritura por Voz",
            variable=self.voice_write_var,
            font=customtkinter.CTkFont(family="Google Sans", size=13, weight="bold"),
            text_color=TEXT_PRIMARY,
            command=self._on_voice_write_toggle
        )
        self.voice_write_switch.grid(row=len(MENU_ITEMS) + 2,
                                     column=0,
                                     padx=25,
                                     pady=(10, 2),
                                     sticky="nw")

    def _on_voice_write_toggle(self):
        new_state = self.voice_write_var.get()
        ConfigManager().update_voice_config({"auto_type": new_state})
        self.logger.info(f"Voice writing auto-type toggled to {new_state} from sidebar switch")

    def refresh_voice_write_switch(self):
        """Actualiza el estado del interruptor desde la configuración de la BD (p. ej., si se actualiza desde la página de ajustes de Voz)."""
        if hasattr(self, "voice_write_var"):
            self.voice_write_var.set(ConfigManager().get_voice_config().get("auto_type", True))

    def set_tab_active(self, tab_name: str):
        """Resalta el botón de menú activo y restablece los demás."""
        for key, btn in self.btns.items():
            if key == tab_name:
                btn.configure(
                    fg_color=MENU_BTN_ACTIVE,
                    text_color=MENU_BTN_ACTIVE_TEXT)
                self.current_active = key
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=MENU_BTN_TEXT)
