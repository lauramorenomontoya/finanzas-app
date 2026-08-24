"""
Componente TagSelector: Selector interactivo de etiquetas (chips de color) para formularios.
Permite seleccionar múltiples tags y crear nuevas etiquetas al instante.
"""

import customtkinter as ctk
from typing import List, Optional
from ui.theme import Theme


class TagSelector(ctk.CTkFrame):
    def __init__(self, master, db_manager, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db = db_manager
        self.selected_tag_ids: List[int] = []
        self.tag_buttons: dict = {}

        self._build_ui()

    def _build_ui(self):
        self.chips_container = ctk.CTkFrame(self, fg_color="transparent")
        self.chips_container.pack(fill="x")
        self.refresh_tags()

    def refresh_tags(self):
        for w in self.chips_container.winfo_children():
            w.destroy()

        self.tag_buttons.clear()
        tags = self.db.get_tags()

        row_frame = ctk.CTkFrame(self.chips_container, fg_color="transparent")
        row_frame.pack(fill="x", pady=2)

        for tag in tags:
            tag_id = tag["id"]
            name = tag["name"]
            color = tag.get("color", "#38bdf8")
            is_selected = tag_id in self.selected_tag_ids

            btn = ctk.CTkButton(
                row_frame,
                text=f"{name}",
                height=26,
                corner_radius=13,
                fg_color=color if is_selected else Theme.BG_CARD_SUBTLE,
                hover_color=color,
                text_color="#ffffff" if is_selected else Theme.TEXT_PRIMARY,
                border_width=1,
                border_color=color if is_selected else Theme.BORDER_SUBTLE,
                font=ctk.CTkFont(size=11, weight="bold" if is_selected else "normal"),
                command=lambda t_id=tag_id: self._toggle_tag(t_id)
            )
            btn.pack(side="left", padx=3, pady=2)
            self.tag_buttons[tag_id] = (btn, color, name)

        # Botón para añadir nueva etiqueta
        btn_add = ctk.CTkButton(
            row_frame,
            text="+ Tag",
            height=26,
            width=50,
            corner_radius=13,
            fg_color="transparent",
            hover_color=Theme.BG_CARD_SUBTLE,
            text_color=Theme.ACCENT_BLUE,
            border_width=1,
            border_color=Theme.ACCENT_BLUE,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._prompt_new_tag
        )
        btn_add.pack(side="left", padx=3, pady=2)

    def _toggle_tag(self, tag_id: int):
        if tag_id in self.selected_tag_ids:
            self.selected_tag_ids.remove(tag_id)
        else:
            self.selected_tag_ids.append(tag_id)
        self._update_chip_styles()

    def _update_chip_styles(self):
        for tag_id, (btn, color, _) in self.tag_buttons.items():
            is_selected = tag_id in self.selected_tag_ids
            btn.configure(
                fg_color=color if is_selected else Theme.BG_CARD_SUBTLE,
                text_color="#ffffff" if is_selected else Theme.TEXT_PRIMARY,
                border_color=color if is_selected else Theme.BORDER_SUBTLE,
                font=ctk.CTkFont(size=11, weight="bold" if is_selected else "normal")
            )

    def _prompt_new_tag(self):
        dialog = ctk.CTkInputDialog(text="Nombre de la nueva etiqueta (ej: 💡 Innovación):", title="Nueva Etiqueta")
        name = dialog.get_input()
        if name and name.strip():
            # Asignar un color aleatorio o rotativo
            palette = ["#38bdf8", "#10b981", "#8b5cf6", "#f59e0b", "#ec4899", "#06b6d4"]
            color = palette[len(self.tag_buttons) % len(palette)]
            new_id = self.db.add_tag(name.strip(), color)
            if new_id:
                self.selected_tag_ids.append(new_id)
                self.refresh_tags()

    def get_selected_tag_ids(self) -> List[int]:
        return list(self.selected_tag_ids)

    def set_selected_tag_ids(self, tag_ids: List[int]):
        self.selected_tag_ids = list(tag_ids)
        self._update_chip_styles()

    def clear(self):
        self.selected_tag_ids.clear()
        self._update_chip_styles()
