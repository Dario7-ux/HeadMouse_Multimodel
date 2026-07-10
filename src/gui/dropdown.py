from functools import partial

import customtkinter
from PIL import Image

from src.config_manager import ConfigManager

ITEM_HEIGHT = 45
ICON_SIZE = (54, 38)
MAX_ROWS = 10
Y_OFFSET = 30

LIGHT_BLUE = ("#FBFBFF", "#2A2B4A")


def mouse_in_widget(mouse_x, mouse_y, widget, expand_x=(0, 0), expand_y=(0, 0)):
    try:
        try:
            scale_factor = widget.winfo_fpixels('1i') / 96.0
        except Exception:
            scale_factor = 1.0

        logical_x = mouse_x / scale_factor
        logical_y = mouse_y / scale_factor

        widget_x1 = widget.winfo_rootx() - expand_x[0]
        widget_y1 = widget.winfo_rooty() - expand_y[0]
        widget_x2 = widget_x1 + widget.winfo_width() + expand_x[0] + expand_x[1]
        widget_y2 = widget_y1 + widget.winfo_height() + expand_y[0] + expand_y[1]
        return widget_x1 <= logical_x <= widget_x2 and widget_y1 <= logical_y <= widget_y2
    except Exception:
        return False


class Dropdown():

    def __init__(self, master, dropdown_items: dict, width, callback: callable):
        self.master_toplevel = master.winfo_toplevel()

        self.float_window = customtkinter.CTkToplevel(master)
        self.float_window.wm_overrideredirect(True)

        self.float_window.lift()
        self.float_window.wm_attributes("-topmost", True)
        
        # Ocultar icono en la barra de tareas
        self.float_window.wm_attributes('-toolwindow', 'True')
        self.float_window.grid_rowconfigure(MAX_ROWS, weight=1)
        self.float_window.grid_columnconfigure(1, weight=1)
        self._displayed = True

        self.width = width
        self.dropdown_keys = list(dropdown_items.keys())

        # Contenedor scrollable para evitar recortes en pantallas pequeñas
        self.scroll_frame = customtkinter.CTkScrollableFrame(
            self.float_window,
            width=width - 2,
            fg_color=LIGHT_BLUE,
            corner_radius=0,
            border_width=0
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=0, pady=0)

        self.divs = self.create_divs(self.scroll_frame, dropdown_items, width)
        self.button_names = [str(v["button"]) for k, v in self.divs.items()]
        self.selected_gesture = list(dropdown_items.keys())[0]

        self.bind_id_release = None
        self.bind_id_motion = None

        self.hide_dropdown()

        self.master_callback = callback

        self.current_user = None
        self.active_widget = None
        self.just_opened = False

    def create_divs(self, master, ges_images: dict, width: int) -> dict:
        import src.shape_list as shape_list
        import os
        divs = {}
        for row, (gesture, image_path) in enumerate(ges_images.items()):
            if not os.path.exists(image_path):
                image_path = "assets/images/dropdowns/None.png"
            image = customtkinter.CTkImage(
                Image.open(image_path).resize(ICON_SIZE), size=ICON_SIZE)

            display_text = shape_list.gesture_translation_map.get(gesture, gesture)

            row_btn = customtkinter.CTkButton(master=master,
                                               width=width,
                                               height=ITEM_HEIGHT,
                                               text=display_text,
                                               border_width=0,
                                               corner_radius=0,
                                               image=image,
                                               hover=True,
                                               fg_color=LIGHT_BLUE,
                                               hover_color=("#E5E5E5", "#3A3B5A"),
                                               text_color_disabled=("#9AA0A6", "#5F6368"),
                                               compound="left",
                                               anchor="nw",
                                               command=partial(self.item_click_callback, gesture))

            row_btn.pack(fill="x",
                         expand=False,
                         padx=0,
                         pady=0)

            divs[gesture] = {"button": row_btn, "image": image}

        return divs

    def mouse_release(self, event):
        """Suelta el ratón y activa el botón."""
        if self.just_opened:
            self.just_opened = False
            return

        # Comprobar qué botón se soltó
        for gesture, div in self.divs.items():
            button = div["button"]
            if button.cget("state") == "disabled":
                continue

            if mouse_in_widget(event.x_root, event.y_root, button):
                self.hide_dropdown()
                self.item_click_callback(gesture)

        return

    def mouse_motion(self, event):
        # Comprobar qué botón se soltó / sobre el que se pasa
        for div in self.divs.values():
            button = div["button"]
            if button.cget("state") == "disabled":
                continue

            if mouse_in_widget(event.x_root, event.y_root, button):
                button.configure(fg_color=("#E5E5E5", "#3A3B5A"))
            else:
                button.configure(fg_color=LIGHT_BLUE)

    def mouse_press(self, event):
        """Si se hace clic fuera del menú desplegable, lo cierra."""
        if not mouse_in_widget(event.x_root, event.y_root, self.float_window):
            if getattr(self, "active_widget", None):
                # Si el clic es en el combobox activo, dejamos que su propio binding lo maneje
                if mouse_in_widget(event.x_root, event.y_root, self.active_widget):
                    return
            self.hide_dropdown()

    def item_click_callback(self, target_gesture: str):
        if not self._displayed:
            return
        self.selected_gesture = target_gesture
        self.hide_dropdown()
        self.master_callback(self.current_user, target_gesture)

        # Desactivar la opción pulsada, excepto la primera
        if target_gesture != self.dropdown_keys[0]:
            self.disable_item(target_gesture)

    def disable_item(self, target_gesture):
        if target_gesture in self.divs:
            self.divs[target_gesture]["button"].configure(state="disabled")

    def enable_item(self, target_gesture):
        if target_gesture in self.divs:
            self.divs[target_gesture]["button"].configure(state="normal")

    def enable_all_except(self, target_gestures: list):
        for div_name in self.divs:
            if div_name in target_gestures:
                self.divs[div_name]["button"].configure(state="disabled")
            else:
                self.divs[div_name]["button"].configure(state="normal")

    def refresh_items(self):
        self.enable_all_except([])

    def register_widget(self, widget, name):
        widget.bind("<ButtonPress-1>", partial(self.show_dropdown, widget,
                                               name))

    def show_dropdown(self, widget, name, event):
        # Cerrar primero el menú desplegable abierto si es otro widget
        if self._displayed:
            if getattr(self, "active_widget", None) == widget:
                self.hide_dropdown()
                return
            else:
                self.hide_dropdown()

        if not self._displayed:
            self.just_opened = True
            self.refresh_items()

            total_height = len(self.divs) * ITEM_HEIGHT + 20
            toplevel = widget.winfo_toplevel()
            try:
                try:
                    scale_factor = widget.winfo_fpixels('1i') / 96.0
                except Exception:
                    scale_factor = 1.0
                logical_screen_height = toplevel.winfo_screenheight() / scale_factor
            except Exception:
                logical_screen_height = 1080
            max_y = toplevel.winfo_rooty() + toplevel.winfo_height()
            limit_y = min(max_y, logical_screen_height)
            
            # Limitar la altura de la ventana desplegable a un máximo de 280px
            # para asegurar que siempre quepa y muestre scrollbar si hay más elementos
            window_height = min(total_height, 280)

            draw_x = widget.winfo_rootx()
            
            # Si el dropdown se sale por el final de la ventana principal o pantalla
            if widget.winfo_rooty() + Y_OFFSET + window_height > (limit_y - 20):
                draw_y = max(0, widget.winfo_rooty() - window_height)
                self.opened_upwards = True
            else:
                draw_y = widget.winfo_rooty() + Y_OFFSET
                self.opened_upwards = False

            self.float_window.wm_geometry(f"{self.width}x{window_height}+{draw_x}+{draw_y}")
            self.float_window.deiconify()
            self.float_window.update_idletasks()
            self.float_window.lift()

            self.active_widget = widget

            # Usar bind_all en caso de mantener presionado sobre la etiqueta o lienzo
            self.bind_id_release = self.float_window.bind_all(
                "<ButtonRelease-1>", self.mouse_release)
            self.bind_id_motion = self.float_window.bind_all(
                "<B1-Motion>", self.mouse_motion)
            self.bind_id_motion_normal = self.float_window.bind_all(
                "<Motion>", self.mouse_motion)
            self.bind_id_press = self.float_window.bind_all(
                "<ButtonPress-1>", self.mouse_press)
            self.float_window.wm_attributes('-disabled', False)

            # Establecer el usuario actual
            self.current_user = name
            self._displayed = True

    def hide_dropdown(self, event=None):
        if event is not None and self._displayed:
            try:
                # If the event is a Leave event from the parent widget,
                # only hide the dropdown if the mouse is NOT inside the dropdown window.
                exp_y = (Y_OFFSET + 20, Y_OFFSET + 20)
                if mouse_in_widget(event.x_root, event.y_root, self.float_window, expand_y=exp_y):
                    return
            except Exception:
                pass

        if self._displayed:
            # Eliminar enlaces de eventos y desactivar completamente la ventana
            self.float_window.unbind_all("<ButtonRelease-1>")
            self.float_window.unbind_all("<B1-Motion>")
            self.float_window.unbind_all("<Motion>")
            self.float_window.unbind_all("<ButtonPress-1>")
            self.float_window.wm_attributes('-disabled', True)

            self.active_widget = None
            self._displayed = False

            # Restablecer el color
            for div in self.divs.values():
                button = div["button"]
                button.configure(fg_color=LIGHT_BLUE)

            self.float_window.withdraw()
