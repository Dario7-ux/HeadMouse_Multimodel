import logging
import tkinter as tk

import customtkinter

import src.gui.frames as frames
import src.gui.pages as pages
from src.gui.bot_overlay import BotOverlay
from src.config_manager import ConfigManager
from src.controllers import MouseController
from src.utils import get_resource_path

customtkinter.set_appearance_mode("system")
customtkinter.set_default_color_theme(get_resource_path("assets/themes/google_theme.json"))

logger = logging.getLogger("MainGUi")


class MainGui():
    def __init__(self, tk_root):
        logger.info("Init MainGui")
        super().__init__()
        self.tk_root = tk_root

        # Get screen dimensions dynamically to occupy the entire screen space
        screen_width = self.tk_root.winfo_screenwidth()
        screen_height = self.tk_root.winfo_screenheight()
        
        self.tk_root.geometry(f"{screen_width}x{screen_height}+0+0")
        self.tk_root.title(f"FocuzVoz {ConfigManager().version}")
        self.tk_root.iconbitmap(get_resource_path("assets/images/icon.ico"))
        self.tk_root.resizable(width=True, height=True)
        # Use a safe minsize that fits 768p and 800p screens
        self.tk_root.minsize(960, 640)
        
        try:
            self.tk_root.state("zoomed")
        except Exception:
            pass

        self.tk_root.grid_rowconfigure(1, weight=1)
        self.tk_root.grid_columnconfigure(1, weight=1)

        # Crear el frame del menú y asignar callbacks
        self.frame_menu = frames.FrameMenu(self.tk_root,
                                           self.root_function_callback,
                                           height=700,
                                           width=260,
                                           logger_name="frame_menu")
        self.frame_menu.grid(row=0,
                             column=0,
                             padx=0,
                             pady=0,
                             sticky="nsew",
                             columnspan=1,
                             rowspan=3)

        # Crear el frame de vista previa (dentro del menú, abajo)
        self.frame_preview = frames.FrameCamPreview(self.frame_menu,
                                                    self.cam_preview_callback,
                                                    logger_name="frame_preview")
        # Colocar en la parte inferior del menú usando la fila con peso
        menu_bottom_row = len(self.frame_menu.btns) + 5
        self.frame_menu.grid_rowconfigure(menu_bottom_row, weight=1)
        self.frame_preview.grid(row=menu_bottom_row,
                                column=0,
                                padx=5,
                                pady=(10, 5),
                                sticky="sew",
                                columnspan=1)
        self.frame_preview.enter()

        # Crear todas las páginas del asistente y posicionarlas en la cuadrícula.
        self.pages = {
            "page_home":
                pages.PageHome(master=self.tk_root,
                               logger_name="page_home",
                               root_callback=self.root_function_callback),
            "page_camera":
                pages.PageSelectCamera(
                    master=self.tk_root,
                    logger_name="page_camera",
                ),
            "page_cursor":
                pages.PageCursor(
                    master=self.tk_root,
                    logger_name="page_cursor",
                ),
            "page_gestures":
                pages.PageSelectGestures(
                    master=self.tk_root,
                    logger_name="page_gestures",
                ),
            "page_keyboard":
                pages.PageKeyboard(
                    master=self.tk_root,
                    logger_name="page_keyboard",
                ),
            "page_voice":
                pages.PageVoice(
                    master=self.tk_root,
                    root_callback=self.root_function_callback,
                    logger_name="page_voice",
                )
        }

        self.page_names = list(self.pages.keys())
        self.curr_page_name = None
        for name, page in self.pages.items():
            page.grid(row=0,
                      column=1,
                      padx=5,
                      pady=5,
                      sticky="nsew",
                      rowspan=2,
                      columnspan=1)

        self.change_page("page_home")

        # UI del Perfil
        self.frame_profile_switcher = frames.FrameProfileSwitcher(
            self.tk_root, main_gui_callback=self.root_function_callback)
        self.frame_profile_editor = frames.FrameProfileEditor(
            self.tk_root, main_gui_callback=self.root_function_callback)

        # ── Botón flotante para alternar tema (arriba a la derecha) ──
        current_mode = customtkinter.get_appearance_mode()
        theme_emoji = "☀️" if current_mode == "Dark" else "🌙"
        
        self.theme_btn = customtkinter.CTkButton(
            master=self.tk_root,
            text=theme_emoji,
            width=36,
            height=36,
            corner_radius=18,
            fg_color="transparent",
            hover_color=("gray85", "gray25"),
            text_color=("black", "white"),
            font=customtkinter.CTkFont(size=18),
            command=self.toggle_theme
        )
        self.theme_btn.place(relx=1.0, rely=0.0, anchor="ne", x=-20, y=20)
        self.theme_btn.lift()

        # Bot Overlay
        self.bot_overlay = BotOverlay()

    def toggle_theme(self):
        """Alterna entre el modo de apariencia claro y oscuro."""
        current = customtkinter.get_appearance_mode()
        new_mode = "Dark" if current == "Light" else "Light"
        customtkinter.set_appearance_mode(new_mode)
        logger.info(f"Theme toggled to {new_mode}")
        
        # Actualizar el icono emoji
        emoji = "☀️" if new_mode == "Dark" else "🌙"
        self.theme_btn.configure(text=emoji)
        self.theme_btn.lift()

    def root_function_callback(self, function_name, args: dict = {}, **kwargs):
        logger.info(f"root_function_callback {function_name} with {args}")

        # Cerrar aplicación
        if function_name == "close_app":
            if hasattr(self, "close_all"):
                self.close_all()
            else:
                self.del_main_gui()
            return

        # Navegación básica de páginas
        elif function_name == "change_page":
            self.change_page(args["target"])
            self.frame_menu.set_tab_active(tab_name=args["target"])

        # Alternar tema
        elif function_name == "toggle_theme":
            self.toggle_theme()

        # Perfiles
        elif function_name == "show_profile_switcher":
            self.frame_profile_switcher.enter()
        elif function_name == "show_profile_editor":
            self.frame_profile_editor.enter()

        elif function_name == "refresh_profiles":
            logger.info("refresh_profile")
            self.pages["page_gestures"].refresh_profile()
            self.pages["page_camera"].refresh_profile()
            self.pages["page_cursor"].refresh_profile()
            self.pages["page_keyboard"].refresh_profile()

        elif function_name == "refresh_voice_write":
            try:
                self.frame_menu.refresh_voice_write_switch()
            except Exception:
                pass

    def cam_preview_callback(self, function_name, args: dict, **kwargs):
        logger.info(f"cam_preview_callback {function_name} with {args}")

        if function_name == "toggle_switch":
            self.set_mediapipe_mouse_enable(new_state=args["switch_status"])

    def set_mediapipe_mouse_enable(self, new_state: bool):
        if new_state:
            MouseController().set_active(True)
        else:
            MouseController().set_active(False)

    def change_page(self, target_page_name: str):

        if self.curr_page_name == target_page_name:
            return

        # Sincronizar el interruptor de voz de la barra lateral en caso de que haya cambiado en otro lugar
        try:
            self.frame_menu.refresh_voice_write_switch()
        except Exception:
            pass

        for name, page in self.pages.items():
            if name == target_page_name:
                page.grid()
                self.pages[target_page_name].enter()
                self.curr_page_name = target_page_name
                try:
                    self.theme_btn.lift()
                except Exception:
                    pass

            else:
                page.grid_remove()
                page.leave()

    def del_main_gui(self):
        logger.info("Deleting MainGui instance")
        # try:
        self.frame_preview.leave()
        self.frame_preview.destroy()
        self.frame_menu.leave()
        self.frame_menu.destroy()
        for page in self.pages.values():
            page.leave()
            page.destroy()

        if hasattr(self, 'bot_overlay'):
            self.bot_overlay.destroy()

        self.tk_root.quit()
        self.tk_root.destroy()
