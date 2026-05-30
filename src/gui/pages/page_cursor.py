import logging
import tkinter
from functools import partial

import customtkinter
import numpy as np
from PIL import Image

from src.config_manager import ConfigManager
from src.controllers import MouseController
from src.gui.balloon import Balloon
from src.gui.frames.safe_disposable_frame import SafeDisposableFrame
from src.gui.theme_colors import (
    BG_CARD, BORDER, DANGER_BG, TEXT_PRIMARY, TEXT_SECONDARY,
    ACCENT, SUCCESS, WARNING, get_color
)

logger = logging.getLogger("PageCursor")
HELP_ICON_SIZE = (16, 16)
MAX_HOLD_TRIG = 5000

# ─────────────────────────────────────────────────────────────────────────────
# CURSOR PRESETS
# Each preset is a dict with the keys that will be written to ConfigManager.
# ─────────────────────────────────────────────────────────────────────────────
PRESETS = {
    "🐢  Suave": {
        "spd_up":              6,
        "spd_down":            8,
        "spd_left":            6,
        "spd_right":           6,
        "pointer_smooth":      18,
        "one_euro_min_cutoff": 0.5,
        "one_euro_beta":       0.003,
        "mouse_acceleration":  False,
        "tick_interval_ms":    12,
    },
    "🎯  Normal": {
        "spd_up":              10,
        "spd_down":            15,
        "spd_left":            11,
        "spd_right":           11,
        "pointer_smooth":      12,
        "one_euro_min_cutoff": 1.0,
        "one_euro_beta":       0.007,
        "mouse_acceleration":  True,
        "tick_interval_ms":    10,
    },
    "⚡  Preciso": {
        "spd_up":              18,
        "spd_down":            22,
        "spd_left":            18,
        "spd_right":           18,
        "pointer_smooth":      6,
        "one_euro_min_cutoff": 2.5,
        "one_euro_beta":       0.015,
        "mouse_acceleration":  True,
        "tick_interval_ms":    8,
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _section_label(master, text: str, row: int):
    """Renders a styled section divider label."""
    lbl = customtkinter.CTkLabel(
        master,
        text=text,
        text_color=TEXT_PRIMARY,
        anchor="w",
        font=customtkinter.CTkFont(family="Google Sans", size=13, weight="bold"),
    )
    lbl.grid(row=row, column=0, columnspan=3, padx=16, pady=(18, 2), sticky="w")
    return lbl


def _divider(master, row: int):
    """Thin horizontal separator."""
    sep = customtkinter.CTkFrame(master, height=1, fg_color=BORDER)
    sep.grid(row=row, column=0, columnspan=3, padx=16, pady=(0, 4), sticky="ew")
    return sep


# ─────────────────────────────────────────────────────────────────────────────
# SINGLE SLIDER ROW
# ─────────────────────────────────────────────────────────────────────────────

class SliderRow:
    """Self-contained slider + numeric-entry row that reads/writes ConfigManager."""

    def __init__(
        self,
        master,
        row: int,
        cfg_key: str,
        label_text: str,
        slider_min: float,
        slider_max: float,
        is_float: bool = False,
        float_step: float = 0.05,
        balloon_obj=None,
        balloon_text: str = "",
        help_icon=None,
    ):
        self.master = master
        self.cfg_key = cfg_key
        self.slider_min = slider_min
        self.slider_max = slider_max
        self.is_float = is_float
        self.float_step = float_step
        self._dragging = False

        # ── Label ──────────────────────────────────────────────────────────
        lbl = customtkinter.CTkLabel(
            master,
            text=label_text,
            image=help_icon if balloon_text else None,
            compound="right",
            anchor="w",
            text_color=TEXT_SECONDARY,
            font=customtkinter.CTkFont(family="Google Sans", size=12),
        )
        lbl.grid(row=row, column=0, padx=(24, 6), pady=(6, 2), sticky="w")
        if balloon_obj and balloon_text:
            balloon_obj.register_widget(lbl, balloon_text)

        # ── Slider ─────────────────────────────────────────────────────────
        n_steps = int((slider_max - slider_min) / float_step) if is_float else int(slider_max - slider_min)
        self.slider = customtkinter.CTkSlider(
            master,
            from_=slider_min,
            to=slider_max,
            width=230,
            number_of_steps=n_steps,
            command=self._on_drag,
        )
        self.slider.bind("<ButtonPress-1>",   self._on_press)
        self.slider.bind("<ButtonRelease-1>", self._on_release)
        self.slider.grid(row=row, column=1, padx=(6, 6), pady=(6, 2), sticky="w")

        # ── Numeric entry ──────────────────────────────────────────────────
        self.var = tkinter.StringVar()
        self._trace_fn = partial(self._on_entry_changed)
        self._trace_id = self.var.trace("w", self._trace_fn)
        self.entry = customtkinter.CTkEntry(
            master,
            textvariable=self.var,
            width=64,
            justify="center",
            font=customtkinter.CTkFont(family="Google Sans", size=12),
        )
        self.entry.grid(row=row, column=2, padx=(4, 16), pady=(6, 2), sticky="w")

        # Load current value
        self.load()

    def load(self):
        """Read from ConfigManager and populate UI."""
        raw = ConfigManager().config.get(self.cfg_key, self.slider_min)
        val = float(raw)
        val = max(self.slider_min, min(self.slider_max, val))
        self.slider.set(val)
        self._set_entry_silent(self._fmt(val))

    def _fmt(self, v: float) -> str:
        return f"{v:.2f}" if self.is_float else str(int(round(v)))

    def _set_entry_silent(self, text: str):
        """Set entry value without firing the trace callback."""
        self.var.trace_vdelete("w", self._trace_id)
        self.var.set(text)
        self._trace_id = self.var.trace("w", self._trace_fn)

    def set_value(self, val: float):
        """Programmatically set the slider and entry (used by presets)."""
        val = max(self.slider_min, min(self.slider_max, float(val)))
        self.slider.set(val)
        self._set_entry_silent(self._fmt(val))
        self._commit(val)

    def _on_press(self, _event):
        self._dragging = True

    def _on_drag(self, new_val):
        self._dragging = True
        self._set_entry_silent(self._fmt(float(new_val)))

    def _on_release(self, _event):
        self._dragging = False
        try:
            val = float(self.var.get()) if self.is_float else int(self.var.get())
        except ValueError:
            return
        self._commit(val)

    def _on_entry_changed(self, *_args):
        text = self.var.get()
        try:
            val = float(text) if self.is_float else int(text)
        except ValueError:
            self.entry.configure(fg_color=get_color(DANGER_BG))
            return

        if val < self.slider_min or val > self.slider_max:
            self.entry.configure(fg_color=get_color(DANGER_BG))
            return

        self.entry.configure(fg_color=get_color(BG_CARD))
        self.slider.set(val)
        if not self._dragging:
            self._commit(val)

    def _commit(self, val):
        ConfigManager().set_temp_config(field=self.cfg_key, value=val)
        ConfigManager().apply_config()
        MouseController().calc_smooth_kernel()


# ─────────────────────────────────────────────────────────────────────────────
# INNER SETTINGS FRAME
# ─────────────────────────────────────────────────────────────────────────────

class FrameCursorSettings(SafeDisposableFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(1, weight=1)

        self.help_icon = customtkinter.CTkImage(
            Image.open("assets/images/help.png").resize(HELP_ICON_SIZE),
            size=HELP_ICON_SIZE,
        )
        self.balloon = Balloon(self, image_path="assets/images/balloon.png")

        self._build_ui()

    # ── BUILD ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        row = 0

        # ══════════════════════════════════════════════════════════════════
        # SECTION 1 – Presets
        # ══════════════════════════════════════════════════════════════════
        _section_label(self, "⚡ Configuración rápida", row); row += 1
        _divider(self, row); row += 1

        preset_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        preset_frame.grid(row=row, column=0, columnspan=3, padx=16, pady=(4, 10), sticky="w")
        row += 1

        self._preset_buttons = {}
        for col_idx, (preset_name, _) in enumerate(PRESETS.items()):
            btn = customtkinter.CTkButton(
                preset_frame,
                text=preset_name,
                width=110,
                height=32,
                corner_radius=8,
                fg_color="transparent",
                border_width=1,
                border_color=BORDER,
                text_color=TEXT_PRIMARY,
                hover_color=get_color(BG_CARD),
                font=customtkinter.CTkFont(family="Google Sans", size=12, weight="bold"),
                command=partial(self._apply_preset, preset_name),
            )
            btn.grid(row=0, column=col_idx, padx=4, pady=0)
            self._preset_buttons[preset_name] = btn

        # ══════════════════════════════════════════════════════════════════
        # SECTION 2 – Speed per direction
        # ══════════════════════════════════════════════════════════════════
        _section_label(self, "🎮 Velocidad por dirección", row); row += 1
        _divider(self, row); row += 1

        self._sliders = {}

        speed_rows = [
            ("spd_up",    "↑  Velocidad arriba",    0, 100),
            ("spd_down",  "↓  Velocidad abajo",     0, 100),
            ("spd_left",  "←  Velocidad izquierda", 0, 100),
            ("spd_right", "→  Velocidad derecha",   0, 100),
        ]
        for cfg_key, lbl_text, lo, hi in speed_rows:
            s = SliderRow(
                self, row, cfg_key, lbl_text, lo, hi,
                is_float=False,
                balloon_obj=self.balloon,
                balloon_text="",
                help_icon=None,
            )
            self._sliders[cfg_key] = s
            row += 1

        # ══════════════════════════════════════════════════════════════════
        # SECTION 3 – Adaptive smoothing (1 Euro Filter)
        # ══════════════════════════════════════════════════════════════════
        _section_label(self, "🌀 Suavizado adaptativo (Filtro 1 Euro)", row); row += 1
        _divider(self, row); row += 1

        euro_rows = [
            (
                "one_euro_min_cutoff",
                "Suavizado estático (min_cutoff)",
                0.1, 5.0, True, 0.05,
                "Valor bajo = más suavizado cuando el\ncursor está quieto. "
                "Reduce el temblor.\nRango recomendado: 0.5 – 2.0",
            ),
            (
                "one_euro_beta",
                "Rapidez de respuesta (beta)",
                0.0, 0.05, True, 0.001,
                "Valor alto = menos retraso al mover\nrápido la cabeza. "
                "Aumentar si el cursor\nva lento al moverse. Rango: 0.003 – 0.02",
            ),
        ]
        for cfg_key, lbl_text, lo, hi, is_f, step, tip in euro_rows:
            s = SliderRow(
                self, row, cfg_key, lbl_text, lo, hi,
                is_float=is_f, float_step=step,
                balloon_obj=self.balloon,
                balloon_text=tip,
                help_icon=self.help_icon,
            )
            self._sliders[cfg_key] = s
            row += 1

        # ══════════════════════════════════════════════════════════════════
        # SECTION 4 – Advanced
        # ══════════════════════════════════════════════════════════════════
        _section_label(self, "🔧 Opciones avanzadas", row); row += 1
        _divider(self, row); row += 1

        # Mouse acceleration toggle
        accel_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        accel_frame.grid(row=row, column=0, columnspan=3, padx=24, pady=(8, 4), sticky="w")
        row += 1

        accel_lbl = customtkinter.CTkLabel(
            accel_frame,
            text="Aceleración del cursor",
            text_color=TEXT_SECONDARY,
            image=self.help_icon,
            compound="right",
            font=customtkinter.CTkFont(family="Google Sans", size=12),
        )
        accel_lbl.grid(row=0, column=0, sticky="w", padx=(0, 16))
        self.balloon.register_widget(
            accel_lbl,
            "Amplifica la velocidad para movimientos\ngrandes, "
            "sin afectar movimientos pequeños.\nDesactivar si el cursor se siente impredecible.",
        )

        self._accel_var = tkinter.BooleanVar(
            value=ConfigManager().config.get("mouse_acceleration", True)
        )
        self._accel_switch = customtkinter.CTkSwitch(
            accel_frame,
            text="",
            variable=self._accel_var,
            command=self._on_accel_toggle,
            width=48,
        )
        self._accel_switch.grid(row=0, column=1, sticky="w")

        # pointer_smooth slider
        s = SliderRow(
            self, row,
            "pointer_smooth", "Suavizado de trayectoria (ventana)",
            1, 50, is_float=False,
            balloon_obj=self.balloon,
            balloon_text="Tamaño de la ventana de promedio\n"
                         "aplicada al movimiento del cursor.\n"
                         "Valores altos = más suave pero más lento.",
            help_icon=self.help_icon,
        )
        self._sliders["pointer_smooth"] = s
        row += 1

        s = SliderRow(
            self, row,
            "shape_smooth", "Suavizado de gestos",
            1, 50, is_float=False,
            balloon_obj=self.balloon,
            balloon_text="Reduce el parpadeo en la detección\n"
                         "de gestos faciales (ej. parpadeo, boca).",
            help_icon=self.help_icon,
        )
        self._sliders["shape_smooth"] = s
        row += 1

        s = SliderRow(
            self, row,
            "hold_trigger_ms", "Retardo de activación (ms)",
            1, MAX_HOLD_TRIG, is_float=False,
            balloon_obj=self.balloon,
            balloon_text="Tiempo en milisegundos que debes\n"
                         "mantener un gesto para que se active.\n"
                         "Aumentar para evitar clics accidentales.",
            help_icon=self.help_icon,
        )
        self._sliders["hold_trigger_ms"] = s
        row += 1

        # bottom padding
        customtkinter.CTkLabel(self, text="").grid(row=row, column=0, pady=8)

    # ── PRESETS ────────────────────────────────────────────────────────────

    def _apply_preset(self, preset_name: str):
        preset = PRESETS[preset_name]
        cfg = ConfigManager()

        # Apply all scalar keys
        for key, val in preset.items():
            if key == "mouse_acceleration":
                cfg.set_temp_config(key, val)
            else:
                cfg.set_temp_config(key, val)
        cfg.apply_config()
        MouseController().calc_smooth_kernel()

        # Sync UI
        for key, slider_row in self._sliders.items():
            if key in preset:
                v = preset[key]
                slider_row.set_value(float(v))

        # Sync acceleration toggle
        if "mouse_acceleration" in preset:
            self._accel_var.set(preset["mouse_acceleration"])
            self._update_accel_switch_color()

        # Highlight active preset button
        for name, btn in self._preset_buttons.items():
            if name == preset_name:
                btn.configure(
                    fg_color=get_color(ACCENT),
                    text_color=("white", "white"),
                    border_color=get_color(ACCENT),
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=get_color(TEXT_PRIMARY),
                    border_color=get_color(BORDER),
                )

        logger.info(f"Cursor preset applied: {preset_name}")

    # ── ACCELERATION TOGGLE ────────────────────────────────────────────────

    def _on_accel_toggle(self):
        val = self._accel_var.get()
        ConfigManager().set_temp_config("mouse_acceleration", val)
        ConfigManager().apply_config()
        self._update_accel_switch_color()
        logger.info(f"Mouse acceleration set to {val}")

    def _update_accel_switch_color(self):
        pass  # CTkSwitch handles its own colors via variable binding

    # ── PROFILE RELOAD ─────────────────────────────────────────────────────

    def inner_refresh_profile(self):
        """Reload all slider values from the currently active config."""
        for slider_row in self._sliders.values():
            slider_row.load()
        self._accel_var.set(
            ConfigManager().config.get("mouse_acceleration", True)
        )
        # Clear preset highlight since profile may differ from any preset
        for btn in self._preset_buttons.values():
            btn.configure(
                fg_color="transparent",
                text_color=get_color(TEXT_PRIMARY),
                border_color=get_color(BORDER),
            )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE CURSOR  (top-level page frame)
# ─────────────────────────────────────────────────────────────────────────────

class PageCursor(SafeDisposableFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Title ──────────────────────────────────────────────────────────
        title = customtkinter.CTkLabel(
            self,
            text="Configuración del Cursor",
            text_color=TEXT_PRIMARY,
            anchor="w",
            font=customtkinter.CTkFont(family="Google Sans", size=22, weight="bold"),
        )
        title.grid(row=0, column=0, padx=20, pady=(14, 2), sticky="w")

        # ── Subtitle ───────────────────────────────────────────────────────
        desc_txt = (
            "El cursor se mueve con el movimiento de tu cabeza/nariz. "
            "Usa los presets rápidos o ajusta cada parámetro manualmente "
            "para adaptar el control a tu comodidad."
        )
        desc = customtkinter.CTkLabel(
            self,
            text=desc_txt,
            wraplength=420,
            text_color=TEXT_SECONDARY,
            anchor="w",
            justify=tkinter.LEFT,
            font=customtkinter.CTkFont(family="Google Sans", size=13),
        )
        desc.grid(row=1, column=0, padx=20, pady=(0, 8), sticky="w")

        # ── Scrollable settings area ───────────────────────────────────────
        scroll = customtkinter.CTkScrollableFrame(
            self,
            fg_color=get_color(BG_CARD),
            corner_radius=12,
            border_width=1,
            border_color=get_color(BORDER),
        )
        scroll.grid(row=2, column=0, padx=12, pady=(0, 12), sticky="nsew")
        scroll.grid_columnconfigure(1, weight=1)

        self.inner_frame = FrameCursorSettings(scroll)
        self.inner_frame.grid(row=0, column=0, sticky="nsew")

    def refresh_profile(self):
        self.inner_frame.inner_refresh_profile()
