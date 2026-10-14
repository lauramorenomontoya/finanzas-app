"""
Componente Visual de Selección de Fecha (DatePicker & Calendario Interactivo).
Proporciona un widget elegante en CustomTkinter con selector de mes/año, cuadrícula interactiva de días y botón 'Hoy'.
"""

import calendar
from datetime import datetime, date
from typing import Optional, Callable
import customtkinter as ctk
from ui.theme import Theme


class CalendarPopup(ctk.CTkToplevel):
    def __init__(self, parent_widget, initial_date: Optional[str] = None, on_select: Optional[Callable[[str], None]] = None):
        super().__init__(parent_widget)
        self.on_select = on_select
        self.parent_widget = parent_widget

        # Parsear fecha inicial
        try:
            if initial_date:
                self.selected_date = datetime.strptime(initial_date, "%Y-%m-%d").date()
            else:
                self.selected_date = date.today()
        except Exception:
            self.selected_date = date.today()

        self.view_year = self.selected_date.year
        self.view_month = self.selected_date.month

        self.title("Seleccionar Fecha")
        self.geometry("310x330")
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_CARD)

        self.transient(parent_widget.winfo_toplevel())
        self.grab_set()

        # Posicionar cerca del widget padre
        try:
            x = parent_widget.winfo_rootx()
            y = parent_widget.winfo_rooty() + parent_widget.winfo_height() + 5
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

        self._build_ui()
        self._render_calendar()

    def _build_ui(self):
        # 1. Cabecera con controles de mes y año
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=Theme.SPACING_SM, pady=(Theme.SPACING_SM, Theme.SPACING_XS))

        btn_prev = ctk.CTkButton(
            header,
            text="◀",
            width=30,
            height=28,
            corner_radius=Theme.SPACING_XS,
            fg_color=Theme.BG_INPUT,
            hover_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._prev_month
        )
        btn_prev.pack(side="left")

        self.lbl_month_year = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=13, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        self.lbl_month_year.pack(side="left", fill="x", expand=True)

        btn_next = ctk.CTkButton(
            header,
            text="▶",
            width=30,
            height=28,
            corner_radius=Theme.SPACING_XS,
            fg_color=Theme.BG_INPUT,
            hover_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._next_month
        )
        btn_next.pack(side="right")

        # 2. Encabezados de días de la semana
        days_header = ctk.CTkFrame(self, fg_color="transparent")
        days_header.pack(fill="x", padx=Theme.SPACING_SM, pady=(2, Theme.SPACING_XS))
        days_header.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)

        day_names = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"]
        for idx, d_name in enumerate(day_names):
            ctk.CTkLabel(
                days_header,
                text=d_name,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=Theme.TEXT_MUTED
            ).grid(row=0, column=idx, pady=Theme.SPACING_XS)

        # 3. Cuadrícula de días
        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True, padx=Theme.SPACING_SM, pady=(0, Theme.SPACING_XS))
        self.grid_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)

        # 4. Barra inferior con 'Hoy' y 'Cerrar'
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=Theme.SPACING_SM, pady=(0, Theme.SPACING_SM))

        btn_today = ctk.CTkButton(
            footer,
            text="📅 Hoy",
            height=26,
            corner_radius=Theme.SPACING_XS,
            fg_color=Theme.INFO,
            hover_color=Theme.INFO_HOVER,
            text_color=Theme.TEXT_ON_COLOR,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._select_today
        )
        btn_today.pack(side="left", fill="x", expand=True, padx=(0, Theme.SPACING_XS))

        btn_close = ctk.CTkButton(
            footer,
            text="Cerrar",
            height=26,
            corner_radius=Theme.SPACING_XS,
            fg_color=Theme.BG_INPUT,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_SECONDARY,
            font=ctk.CTkFont(size=11),
            command=self.destroy
        )
        btn_close.pack(side="right", padx=(Theme.SPACING_XS, 0))

    def _prev_month(self):
        if self.view_month == 1:
            self.view_month = 12
            self.view_year -= 1
        else:
            self.view_month -= 1
        self._render_calendar()

    def _next_month(self):
        if self.view_month == 12:
            self.view_month = 1
            self.view_year += 1
        else:
            self.view_month += 1
        self._render_calendar()

    def _render_calendar(self):
        month_names = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        self.lbl_month_year.configure(text=f"{month_names[self.view_month - 1]} {self.view_year}")

        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        cal = calendar.monthcalendar(self.view_year, self.view_month)
        today = date.today()

        for r_idx, week in enumerate(cal):
            for c_idx, day in enumerate(week):
                if day == 0:
                    continue

                d_obj = date(self.view_year, self.view_month, day)
                is_selected = (d_obj == self.selected_date)
                is_today = (d_obj == today)

                if is_selected:
                    bg_color = "#0284c7"
                    hover_color = "#0369a1"
                    txt_color = "#ffffff"
                    border_color = "#38bdf8"
                    b_width = 1
                elif is_today:
                    bg_color = "#1e293b"
                    hover_color = "#334155"
                    txt_color = "#38bdf8"
                    border_color = "#38bdf8"
                    b_width = 1
                else:
                    bg_color = "transparent"
                    hover_color = Theme.BORDER_DEFAULT
                    txt_color = Theme.TEXT_PRIMARY
                    border_color = "#38bdf8"
                    b_width = 0

                btn_day = ctk.CTkButton(
                    self.grid_frame,
                    text=str(day),
                    width=32,
                    height=28,
                    corner_radius=Theme.SPACING_XS,
                    fg_color=bg_color,
                    hover_color=hover_color,
                    text_color=txt_color,
                    border_color=border_color,
                    border_width=b_width,
                    font=ctk.CTkFont(size=11, weight="bold" if (is_selected or is_today) else "normal"),
                    command=lambda d=day: self._select_day(d)
                )
                btn_day.grid(row=r_idx, column=c_idx, padx=Theme.SPACING_XS, pady=Theme.SPACING_XS)

    def _select_day(self, day: int):
        chosen = date(self.view_year, self.view_month, day)
        date_str = chosen.strftime("%Y-%m-%d")
        if self.on_select:
            self.on_select(date_str)
        self.destroy()

    def _select_today(self):
        today_str = date.today().strftime("%Y-%m-%d")
        if self.on_select:
            self.on_select(today_str)
        self.destroy()


class DatePickerWidget(ctk.CTkFrame):
    """
    Widget visual reutilizable que combina una caja de texto de fecha con un botón 📅
    que despliega un calendario interactivo.
    """
    def __init__(
        self,
        master,
        initial_date: Optional[str] = None,
        height: int = 34,
        on_date_changed: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", height=height, **kwargs)
        self.on_date_changed = on_date_changed

        default_date = initial_date or datetime.now().strftime("%Y-%m-%d")

        # Entrada de Texto
        self.entry = ctk.CTkEntry(
            self,
            height=height,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=13)
        )
        self.entry.insert(0, default_date)
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, Theme.SPACING_XS))

        # Botón de Calendario
        self.btn_cal = ctk.CTkButton(
            self,
            text="📅",
            width=38,
            height=height,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.BG_INPUT,
            hover_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=14),
            command=self._open_calendar
        )
        self.btn_cal.pack(side="right")

    def _open_calendar(self):
        current_val = self.get().strip()
        CalendarPopup(
            self,
            initial_date=current_val,
            on_select=self._on_calendar_selected
        )

    def _on_calendar_selected(self, chosen_date: str):
        self.set_date(chosen_date)
        if self.on_date_changed:
            self.on_date_changed(chosen_date)

    def get(self) -> str:
        return self.entry.get().strip()

    def get_date(self) -> str:
        return self.get()

    def set_date(self, date_str: str):
        self.entry.delete(0, "end")
        self.entry.insert(0, date_str.strip())

    def delete(self, first, last=None):
        self.entry.delete(first, last)

    def insert(self, index, string):
        self.entry.insert(index, string)
