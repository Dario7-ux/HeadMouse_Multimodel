"""Constantes centralizadas de colores de tema para la interfaz de usuario de FocuzVoz.

Todos los colores se definen como tuplas (modo_claro, modo_oscuro).
Usa get_color() para recuperar el color correcto basado en el modo de apariencia actual.
"""

import customtkinter


# ─────────────────────── Fondos ────────────────────────
BG_PRIMARY = ("#FFFFFF", "#1A1B2E")        # Fondo de la ventana principal
BG_SECONDARY = ("#F4F6FA", "#232442")      # Barra lateral / paneles secundarios
BG_CARD = ("#FFFFFF", "#2A2B4A")           # Tarjetas, popups, divs
BG_HOVER = ("#E8F0FE", "#3A3B5A")          # Estado al pasar el cursor
BG_SELECTED = ("#D0E1F9", "#4A3B8A")       # Estado seleccionado / activo
BG_INPUT = ("#F9F9FA", "#2A2B4A")          # Fondo de campos de entrada

# ─────────────────────── Colores de Acento ──────────────────────
ACCENT = ("#1A73E8", "#00D4FF")            # Acento primario (deslizadores, activo)
ACCENT_HOVER = ("#174EA6", "#00B8D4")      # Acento al pasar el cursor
ACCENT_ALT = ("#4285F4", "#7C3AED")        # Acento secundario (botones)
ACCENT_ALT_HOVER = ("#357ABD", "#6D28D9")  # Acento secundario al pasar el cursor
ACCENT_TRACK = ("#D2E3FC", "#1A1B2E")      # Fondo de la barra del deslizador

# ─────────────────────── Colores de Texto ────────────────────────
TEXT_PRIMARY = ("#202124", "#E8EAED")       # Texto principal
TEXT_SECONDARY = ("#5F6368", "#9AA0A6")     # Texto de descripción
TEXT_ACCENT = ("#1A73E8", "#00D4FF")        # Enlaces, texto resaltado
TEXT_TITLE = ("#202124", "#FFFFFF")         # Títulos de página
TEXT_ON_ACCENT = ("#FFFFFF", "#FFFFFF")     # Texto sobre fondo de acento

# ─────────────────────── Colores de Interruptores ──────────────────────
SWITCH_ON = ("#34A853", "#00D4FF")         # Interruptor activado
SWITCH_OFF = ("#444746", "#5F6368")        # Interruptor desactivado
SWITCH_BUTTON = ("#8F8F8F", "#B0B0B0")     # Botón del interruptor
SWITCH_BUTTON_HOVER = ("#666666", "#FFFFFF")

# ─────────────────────── Bordes / Separadores ─────────────────
BORDER = ("#DADCE0", "#3A3B5A")            # Bordes sutiles
BORDER_INPUT = ("#979DA2", "#5F6368")      # Bordes de campos de entrada

# ─────────────────────── Colores de Estado ──────────────────────
DANGER = ("#EA4335", "#FF6B6B")            # Errores, eliminación
DANGER_BG = ("#ee9e9d", "#5C2020")         # Fondo de error
SUCCESS = ("#34A853", "#69F0AE")           # Éxito, validación
SUCCESS_BG = ("#a6eacf", "#1B5E20")        # Fondo de éxito
WARNING = ("#F9AB00", "#FFD54F")           # Advertencia
INFO = ("#4285F4", "#64B5F6")              # Información

# ─────────────────────── Colores Específicos del Menú ──────────────────────
MENU_BG = ("#F4F6FA", "#0F1023")           # Fondo de la barra lateral de menú
MENU_BTN_HOVER = ("#E8F0FE", "#2A2B4A")    # Botón del menú al pasar el cursor
MENU_BTN_ACTIVE = ("#D0E1F9", "#3A2B6A")   # Botón del menú activo/seleccionado
MENU_BTN_ACTIVE_TEXT = ("#1A73E8", "#00D4FF")
MENU_BTN_TEXT = ("#444746", "#B0B0B0")     # Texto del botón del menú
MENU_DIVIDER = ("#DADCE0", "#2A2B4A")      # Línea divisoria del menú

# ─────────────────────── Colores del Perfil ─────────────────────
PROFILE_DIV_DEFAULT = ("#FFFFFF", "#2A2B4A")
PROFILE_DIV_HOVER = ("#E8F0FE", "#3A3B5A")
PROFILE_DIV_SELECTED = ("#D0E1F9", "#4A3B8A")

# ─────────────────────── Lienzo / Vista Previa ───────────────────
CANVAS_BG = ("#F4F6FA", "#1A1B2E")
PREVIEW_BORDER = ("#DADCE0", "#3A3B5A")


def get_color(color_tuple):
    """Obtiene el color apropiado basado en el modo de apariencia actual.
    
    Args:
        color_tuple: Tupla de (color_claro, color_oscuro)
    
    Returns:
        La cadena de color para el modo actual
    """
    mode = customtkinter.get_appearance_mode()
    if mode == "Dark":
        return color_tuple[1]
    return color_tuple[0]
