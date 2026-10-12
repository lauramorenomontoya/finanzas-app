"""
ui/components/segmented_button.py - CTkSegmentedButton con contraste optimizado y tokens Dark Finance.
Asegura que el texto de la pestaña activa tenga alto contraste (obsidiana oscuro sobre fondo brillante),
y que las pestañas inactivas mantengan el texto salvia/secundario sin azules fuera de paleta.
"""

from typing import Optional, Union, Tuple
import customtkinter as ctk
from ui.theme import Theme


class StyledSegmentedButton(ctk.CTkSegmentedButton):
    def __init__(
        self,
        master,
        selected_color: Optional[Union[str, Tuple[str, str]]] = None,
        selected_hover_color: Optional[Union[str, Tuple[str, str]]] = None,
        unselected_color: Optional[Union[str, Tuple[str, str]]] = None,
        unselected_hover_color: Optional[Union[str, Tuple[str, str]]] = None,
        selected_text_color: str = "#111713",
        unselected_text_color: Optional[Union[str, Tuple[str, str]]] = None,
        corner_radius: int = Theme.SPACING_SM,
        height: int = 32,
        **kwargs
    ):
        sel_col = selected_color or Theme.ACCENT
        sel_hov = selected_hover_color or Theme.SUCCESS_HOVER
        unsel_col = unselected_color or Theme.BG_CARD_SUBTLE
        unsel_hov = unselected_hover_color or Theme.BG_CARD
        unsel_txt = unselected_text_color or Theme.TEXT_SECONDARY

        super().__init__(
            master,
            selected_color=sel_col,
            selected_hover_color=sel_hov,
            unselected_color=unsel_col,
            unselected_hover_color=unsel_hov,
            corner_radius=corner_radius,
            height=height,
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=11, weight="bold"),
            **kwargs
        )
        self._selected_text_color = selected_text_color
        self._unselected_text_color = unsel_txt

        # Aplicar contraste a las pestañas iniciales
        self._apply_contrast_to_all()

    def _apply_contrast_to_all(self):
        for val, btn in self._buttons_dict.items():
            if val == self._current_value:
                btn.configure(text_color=self._selected_text_color)
            else:
                btn.configure(text_color=self._unselected_text_color)

    def _select_button_by_value(self, value: str):
        super()._select_button_by_value(value)
        if value in self._buttons_dict:
            self._buttons_dict[value].configure(text_color=self._selected_text_color)

    def _unselect_button_by_value(self, value: str):
        super()._unselect_button_by_value(value)
        if value in self._buttons_dict:
            self._buttons_dict[value].configure(text_color=self._unselected_text_color)

    def set(self, value: str, from_variable_callback: bool = False):
        super().set(value, from_variable_callback=from_variable_callback)
        self._apply_contrast_to_all()

    def configure(self, **kwargs):
        if "selected_text_color" in kwargs:
            self._selected_text_color = kwargs.pop("selected_text_color")
        if "unselected_text_color" in kwargs:
            self._unselected_text_color = kwargs.pop("unselected_text_color")
        super().configure(**kwargs)
        self._apply_contrast_to_all()

