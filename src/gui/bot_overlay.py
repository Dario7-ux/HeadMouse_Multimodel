import logging
import tkinter as tk
import customtkinter
from src.config_manager import ConfigManager
import src.shape_list as shape_list

logger = logging.getLogger("BotOverlay")

class BotOverlay(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("FocuzVoz Bot")
        
        # Make the window always on top
        self.attributes('-topmost', True)
        # Remove standard window decorations for a floating widget feel
        self.overrideredirect(True)
        
        # Window transparency for Windows
        try:
            self._fg_color = "#000001"
            self.configure(fg_color="#000001")
            self.config(bg="#000001")
            self.wm_attributes("-transparentcolor", "#000001")
        except Exception as e:
            logger.warning(f"Could not enable window transparency: {e}")

        # Position the bot in the bottom right corner
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Initial size (collapsed)
        self.collapsed_width = 60
        self.collapsed_height = 60
        self.expanded_width = 440
        self.expanded_height = min(700, screen_height - 80)
        
        x_pos = screen_width - self.collapsed_width - 20
        y_pos = screen_height - self.collapsed_height - 60
        self.geometry(f"{self.collapsed_width}x{self.collapsed_height}+{x_pos}+{y_pos}")
        
        # Dragging variables
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._drag_start_root_x = 0
        self._drag_start_root_y = 0
        self._has_dragged = False
        
        self.is_expanded = False
        
        # Container frame (transparent in collapsed state for round window effect)
        self.main_frame = customtkinter.CTkFrame(self, corner_radius=30, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True)
        
        # Bot icon using CTkLabel (avoids CustomTkinter's CTkButton dragging block issue)
        from PIL import Image
        from src.utils import get_resource_path
        self.logo_img = customtkinter.CTkImage(
            light_image=Image.open(get_resource_path("assets/images/boot.png")),
            dark_image=Image.open(get_resource_path("assets/images/boot.png")),
            size=(54, 54)
        )

        self.bot_icon_lbl = customtkinter.CTkLabel(
            self.main_frame, text="", image=self.logo_img, width=60, height=60
        )
        self.bot_icon_lbl.place(relx=0.5, rely=0.5, anchor="center")
        
        # Bind dragging and release to the label and frame
        self.bot_icon_lbl.bind("<ButtonPress-1>", self.start_drag)
        self.bot_icon_lbl.bind("<B1-Motion>", self.do_drag)
        self.bot_icon_lbl.bind("<ButtonRelease-1>", self.end_drag)
        
        self.main_frame.bind("<ButtonPress-1>", self.start_drag)
        self.main_frame.bind("<B1-Motion>", self.do_drag)
        
        # Expanded content (hidden initially)
        self.content_frame = customtkinter.CTkFrame(self.main_frame, fg_color="transparent", corner_radius=15)
        
    def _set_appearance_mode(self, mode):
        super()._set_appearance_mode(mode)
        try:
            self._fg_color = "#000001"
            self.configure(fg_color="#000001")
            self.config(bg="#000001")
        except Exception:
            pass

    def start_drag(self, event):
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        self._win_start_x = self.winfo_x()
        self._win_start_y = self.winfo_y()
        self._has_dragged = False

    def do_drag(self, event):
        dx = event.x_root - self._drag_start_x
        dy = event.y_root - self._drag_start_y
        if dx*dx + dy*dy > 25:  # > 5 pixels threshold
            self._has_dragged = True
            
        new_x = self._win_start_x + dx
        new_y = self._win_start_y + dy
        self.geometry(f"+{new_x}+{new_y}")
        
    def end_drag(self, event):
        if not getattr(self, "_has_dragged", False):
            self.toggle_expand()
        
    def toggle_expand(self):
        if self.is_expanded:
            self.collapse()
        else:
            self.expand()
            
    def expand(self):
        self.is_expanded = True
        
        # Hide the collapsed bot icon label
        self.bot_icon_lbl.place_forget()
        
        # Store collapsed position
        self.collapsed_x = self.winfo_x()
        self.collapsed_y = self.winfo_y()
        
        # Modern background card (supporting Light and Dark modes)
        self.main_frame.configure(corner_radius=20, fg_color=("#F8F9FA", "#18191C"))
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Expand intelligently based on the bot's position relative to the screen center
        if self.collapsed_x + self.collapsed_width / 2 < screen_width / 2:
            new_x = self.collapsed_x
        else:
            new_x = self.collapsed_x + self.collapsed_width - self.expanded_width
            
        if self.collapsed_y + self.collapsed_height / 2 < screen_height / 2:
            new_y = self.collapsed_y
        else:
            new_y = self.collapsed_y + self.collapsed_height - self.expanded_height
        
        # Clamp bounds
        new_x = max(10, min(screen_width - self.expanded_width - 10, new_x))
        new_y = max(10, min(screen_height - self.expanded_height - 60, new_y))
        
        self.geometry(f"{self.expanded_width}x{self.expanded_height}+{new_x}+{new_y}")
        
        self.build_content()
        self.content_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
    def collapse(self):
        self.is_expanded = False
        self.content_frame.pack_forget()
        
        self.main_frame.configure(corner_radius=30, fg_color="transparent")
        
        # Restore the collapsed bot icon label
        self.bot_icon_lbl.place(relx=0.5, rely=0.5, anchor="center")
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        if not hasattr(self, 'collapsed_x'):
            self.collapsed_x = screen_width - self.collapsed_width - 20
            self.collapsed_y = screen_height - self.collapsed_height - 60
            
        new_x = max(10, min(screen_width - self.collapsed_width - 10, self.collapsed_x))
        new_y = max(10, min(screen_height - self.collapsed_height - 60, self.collapsed_y))
        
        self.geometry(f"{self.collapsed_width}x{self.collapsed_height}+{new_x}+{new_y}")
        
    def build_content(self):
        # Clear existing
        for w in self.content_frame.winfo_children():
            w.destroy()
            
        # Header title
        header_frame = customtkinter.CTkFrame(self.content_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 5))
        
        lbl_title = customtkinter.CTkLabel(
            header_frame, text="Guía de Referencia", 
            font=customtkinter.CTkFont(family="Google Sans", size=18, weight="bold"),
            text_color=("#1A1A1A", "#FFFFFF")
        )
        lbl_title.pack(side="left", anchor="w")
        
        # Close button in the header (looks incredibly clean and is never covered)
        self.close_btn = customtkinter.CTkButton(
            header_frame, text="✕", width=28, height=28, corner_radius=14,
            font=customtkinter.CTkFont(size=12, weight="bold"),
            fg_color=("#E0E0E0", "#2B2D31"), hover_color=("#D0D0D0", "#3F4146"), text_color=("#333333", "#FFFFFF"),
            command=self.collapse
        )
        self.close_btn.pack(side="right", anchor="e", padx=5)
        
        # Bind dragging to the header frame and title
        header_frame.bind("<ButtonPress-1>", self.start_drag)
        header_frame.bind("<B1-Motion>", self.do_drag)
        lbl_title.bind("<ButtonPress-1>", self.start_drag)
        lbl_title.bind("<B1-Motion>", self.do_drag)
        
        lbl_subtitle = customtkinter.CTkLabel(
            self.content_frame, text="Comandos y gestos activos", 
            font=customtkinter.CTkFont(family="Google Sans", size=11),
            text_color="gray"
        )
        lbl_subtitle.pack(anchor="w", pady=(0, 5))
        
        # Voice Commands Card
        vc_card = customtkinter.CTkFrame(self.content_frame, corner_radius=12, fg_color=("#FFFFFF", "#202225"))
        vc_card.pack(fill="x", pady=(0, 5), padx=2)
        
        vc_header = customtkinter.CTkFrame(vc_card, fg_color="transparent")
        vc_header.pack(fill="x", padx=15, pady=(8, 2))
        
        vc_lbl = customtkinter.CTkLabel(vc_header, text="🎤 Comandos de Voz", text_color="#1A73E8", font=customtkinter.CTkFont(family="Google Sans", size=13, weight="bold"))
        vc_lbl.pack(anchor="w")
        
        # Bot Overlay Voice Commands (formatted like the main page)
        commands_list_frame = customtkinter.CTkFrame(vc_card, fg_color="transparent")
        commands_list_frame.pack(fill="x", padx=15, pady=(0, 8))

        def add_category(title, commands, color):
            cat_header = customtkinter.CTkFrame(commands_list_frame, fg_color="transparent")
            cat_header.pack(fill="x", pady=(6, 2))
            
            cat_lbl = customtkinter.CTkLabel(
                cat_header, text=title, text_color=color,
                font=customtkinter.CTkFont(family="Google Sans", size=11, weight="bold")
            )
            cat_lbl.pack(side="left")
            
            chevron_lbl = customtkinter.CTkLabel(
                cat_header, text="^", text_color="#A0A0A0",
                font=customtkinter.CTkFont(family="Google Sans", size=12, weight="bold")
            )
            chevron_lbl.pack(side="right")
            
            for i, cmd in enumerate(commands):
                cmd_row = customtkinter.CTkFrame(commands_list_frame, fg_color=("#F1F3F4", "#1E232D") if i % 2 == 0 else "transparent", corner_radius=6)
                cmd_row.pack(fill="x", pady=1)
                
                cmd_lbl = customtkinter.CTkLabel(
                    cmd_row, text=f"🎤 {cmd}", text_color=("#1A1A1A", "#FFFFFF"),
                    font=customtkinter.CTkFont(family="Google Sans", size=11, weight="bold")
                )
                cmd_lbl.pack(anchor="w", padx=10, pady=2)

        add_category("🖱️ CLICS DE RATÓN", [
            '"click" / "clic" ➔ Clic derecho',
            '"click izquierdo" ➔ Clic izquierdo',
            '"doble click" ➔ Doble clic derecho',
            '"doble click izquierdo" ➔ Doble clic izquierdo'
        ], "#E8711A")

        add_category("⌨️ DICTADO Y ESCRITURA", [
            '"escribir" ➔ "Activar escritura" ➔ Activar dictado',
            '"silencio" / "no escribir" ➔ Pausar dictado',
            '"borrar" / "deshacer" ➔ Borrar segmento',
            '"borrar todo" / "limpiar" ➔ Limpiar todo'
        ], "#8E44AD")

        add_category("🚀 ATAJOS Y SESIÓN", [
            '"abrir navegador" ➔ "Abrir internet" ➔ Google Chrome',
            '"abrir word" ➔ Microsoft Word',
            '"abrir bloc de notas" ➔ Bloc de notas',
            '"Focuzvoz finish" ➔ Cerrar programa'
        ], "#E8A01A")
        

