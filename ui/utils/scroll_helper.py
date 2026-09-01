"""
Módulo de Soporte de Desplazamiento Suave (Apple Trackpad, Magic Mouse & Universal Mouse Controller):
Permite que el deslizamiento (slide) con dos dedos en el trackpad (vertical y lateral)
y el desplazamiento táctil del Magic Mouse funcionen de forma 100% fluida en toda la aplicación.
"""

import sys
import customtkinter as ctk
import tkinter as tk


class ScrollHelper:
    _initialized = False

    @classmethod
    def enable_smooth_scrolling(cls):
        """
        Configura y optimiza globalmente el comportamiento de scroll en CustomTkinter
        para responder con total precisión a gestos de iMac Trackpad, MacBook Trackpad
        y Magic Mouse en macOS (además de Windows y Linux).
        """
        if cls._initialized:
            return
        cls._initialized = True

        # 1. Calibrar incrementos en el canvas base
        def enhanced_set_scroll_increments(self):
            if sys.platform == "darwin":
                # En macOS, incrementos ajustados para respuesta táctil natural
                self._parent_canvas.configure(xscrollincrement=2, yscrollincrement=4)
            elif sys.platform.startswith("win"):
                self._parent_canvas.configure(xscrollincrement=1, yscrollincrement=1)
            else:
                self._parent_canvas.configure(xscrollincrement=15, yscrollincrement=15)

        ctk.CTkScrollableFrame._set_scroll_increments = enhanced_set_scroll_increments

        # 2. Detección jerárquica precisa del contenedor bajo el cursor
        def smart_check_if_valid_scroll(self, widget, x_root=None, y_root=None):
            if widget is None:
                return False

            target = widget
            # En macOS Cocoa, event.widget suele ser la ventana principal ('.');
            # obtenemos el widget exacto bajo las coordenadas globales del cursor.
            if x_root is not None and y_root is not None and hasattr(widget, "winfo_containing"):
                try:
                    hovered = widget.winfo_containing(x_root, y_root)
                    if hovered is not None:
                        target = hovered
                except Exception:
                    pass

            # Subir por el árbol de padres buscando si pertenece a este CTkScrollableFrame
            curr = target
            while curr is not None:
                if curr == self or curr == self._parent_canvas or curr == self._parent_frame:
                    return True
                if isinstance(curr, ctk.CTkScrollableFrame):
                    return curr._parent_canvas == self._parent_canvas
                # Ignorar widgets que tienen su propio scroll interno
                if isinstance(curr, (ctk.CTkScrollbar, ctk.CTkSlider, ctk.CTkTextbox)):
                    return False
                curr = getattr(curr, "master", None)

            return False

        ctk.CTkScrollableFrame._check_if_valid_scroll = smart_check_if_valid_scroll

        # 3. Manejador universal de eventos de rueda, trackpad y Magic Mouse
        def enhanced_mouse_wheel_all(self, event):
            x = getattr(event, "x_root", None)
            y = getattr(event, "y_root", None)
            w = getattr(event, "widget", None)

            if not smart_check_if_valid_scroll(self, w, x, y):
                return

            # Detectar desplazamiento horizontal (Slide lateral con trackpad o tecla Shift presionada)
            is_horizontal = (
                getattr(self, "_shift_pressed", False)
                or getattr(self, "_orientation", "vertical") == "horizontal"
            )
            if hasattr(event, "state") and (event.state & 0x1):  # Shift mask
                is_horizontal = True

            delta = getattr(event, "delta", 0)

            if sys.platform == "darwin":
                # En macOS con Magic Mouse / Trackpad:
                # delta positivo = deslizamiento hacia arriba (subir)
                # delta negativo = deslizamiento hacia abajo (bajar)
                if abs(delta) < 1 and delta != 0:
                    scroll_delta = 1 if delta > 0 else -1
                else:
                    scroll_delta = int(delta)

                if is_horizontal:
                    if self._parent_canvas.xview() != (0.0, 1.0):
                        self._parent_canvas.xview_scroll(-1 * scroll_delta, "units")
                else:
                    if self._parent_canvas.yview() != (0.0, 1.0):
                        self._parent_canvas.yview_scroll(-1 * scroll_delta, "units")

            elif sys.platform.startswith("win"):
                step = int(-1 * (delta / 120)) if delta != 0 else 0
                if step == 0 and delta != 0:
                    step = -1 if delta > 0 else 1

                if is_horizontal:
                    if self._parent_canvas.xview() != (0.0, 1.0):
                        self._parent_canvas.xview_scroll(step * 2, "units")
                else:
                    if self._parent_canvas.yview() != (0.0, 1.0):
                        self._parent_canvas.yview_scroll(step * 2, "units")

            else:
                # Linux / X11
                num = getattr(event, "num", 0)
                step = -1 if num in (4, 6) else 1
                if is_horizontal or num in (6, 7):
                    if self._parent_canvas.xview() != (0.0, 1.0):
                        self._parent_canvas.xview_scroll(step * 2, "units")
                else:
                    if self._parent_canvas.yview() != (0.0, 1.0):
                        self._parent_canvas.yview_scroll(step * 2, "units")

        ctk.CTkScrollableFrame._mouse_wheel_all = enhanced_mouse_wheel_all

        # 4. Asegurar que Shift-MouseWheel también esté enlazado en todos los ScrollableFrames
        original_init = ctk.CTkScrollableFrame.__init__

        def enhanced_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            # Enlazar soporte para slide horizontal en trackpad de Mac
            if sys.platform == "darwin":
                self.bind_all("<Shift-MouseWheel>", self._mouse_wheel_all, add=True)
                self.bind_all("<Option-MouseWheel>", self._mouse_wheel_all, add=True)

        ctk.CTkScrollableFrame.__init__ = enhanced_init
