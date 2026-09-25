"""
Módulo de compatibilidad de desplazamiento seguro para CustomTkinter en macOS y Windows.
Soporta Tk 9.0 (TouchpadScroll) decodificando deltas empaquetados de 32 bits para evitar desbordamiento C
y optimiza la sensibilidad para ratones externos tradicionales (MouseWheel).
"""

import sys
import tkinter
import customtkinter as ctk
from customtkinter.windows.widgets.ctk_scrollable_frame import CTkScrollableFrame


class ScrollHelper:
    _installed = False

    @classmethod
    def enable_smooth_scrolling(cls):
        if cls._installed:
            return
        cls._installed = True

        orig_mouse_wheel_all = CTkScrollableFrame._mouse_wheel_all

        def _safe_mouse_wheel_all(self, event):
            try:
                if not self._check_if_valid_scroll(event.widget):
                    return

                raw_delta = int(getattr(event, "delta", 0))

                # En Tk 9.0 para macOS, TouchpadScroll envía un entero empaquetado de 32 bits (X e Y)
                # Si se pasa crudo a C yview, desborda la memoria de Tkinter (alloc: invalid block).
                if abs(raw_delta) > 1000:
                    raw = raw_delta & 0xFFFFFFFF
                    delta_y = raw & 0xFFFF
                    if delta_y >= 0x8000:
                        delta_y -= 0x10000
                    # Limitar a rango seguro para Tcl/Tk C
                    delta_y = max(-30, min(30, delta_y))
                    if delta_y != 0 and hasattr(self, "_parent_canvas") and self._parent_canvas:
                        if self._parent_canvas.yview() != (0.0, 1.0):
                            self._parent_canvas.yview("scroll", delta_y, "units")
                    return

                # MouseWheel estándar (ratones con rueda o Windows/Linux)
                delta = max(-30, min(30, raw_delta))
                if sys.platform == "darwin" and abs(delta) <= 3:
                    delta = delta * 4

                if delta != 0 and hasattr(self, "_parent_canvas") and self._parent_canvas:
                    if self._parent_canvas.yview() != (0.0, 1.0):
                        self._parent_canvas.yview("scroll", -delta, "units")
            except Exception:
                pass

        CTkScrollableFrame._mouse_wheel_all = _safe_mouse_wheel_all

        # Enlazar <TouchpadScroll> de Tk 9.0 usando el mismo patrón nativo de CustomTkinter
        orig_init = CTkScrollableFrame.__init__

        def _patched_init(self, *args, **kwargs):
            orig_init(self, *args, **kwargs)
            try:
                self.bind_all("<TouchpadScroll>", self._mouse_wheel_all, add=True)
            except Exception:
                pass

        CTkScrollableFrame.__init__ = _patched_init
