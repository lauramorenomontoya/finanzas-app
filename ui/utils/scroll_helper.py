"""
Módulo de compatibilidad de desplazamiento.
CustomTkinter maneja el desplazamiento en macOS de forma nativa y segura mediante <MouseWheel>.
"""


class ScrollHelper:
    @classmethod
    def enable_smooth_scrolling(cls):
        """No-op seguro: evita monkey-patching duplicado y desbordamientos en Tcl 9."""
        pass

