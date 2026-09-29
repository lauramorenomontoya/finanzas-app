"""
Vista del Puente de Conversión (USD ➔ COP) para Control Financiero.
Permite retirar dólares de la Bóveda USD aplicando una tasa de cambio,
descontándolos de USD y acreditando los pesos automáticamente en el Presupuesto COP.
Incluye Edición ✏️ y Eliminación 🗑️ con Seguridad de Saldo Inteligente.
"""

import customtkinter as ctk
from datetime import datetime
from typing import Callable, Optional, Dict, Any
from ui.components import (
    ToastNotification,
    ConfirmDialog,
    BalanceWarningDialog,
    EditTransactionModal,
    EmptyState
)
from services.currency_service import CurrencyService
from ui.theme import Theme


class ConversionView(ctk.CTkFrame):
    def __init__(self, master, db_manager, on_data_changed: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db = db_manager
        self.on_data_changed = on_data_changed
        self.display_limit = 20

        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        # 1. Cabecera con Toast
        self.toast = ToastNotification(self)

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(20, 16))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="🔄 Puente de Conversión (USD ➔ COP)",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=24, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Retira fondos de tu Bóveda USD e inyéctalos a tu Presupuesto COP a la tasa pactada",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=13),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # 2. Contenedor de Dos Columnas (Formulario Interactivo + Historial de Conversiones)
        content_grid = ctk.CTkFrame(self, fg_color="transparent")
        content_grid.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        content_grid.grid_columnconfigure(0, weight=50, uniform="conv_cols")  # Formulario y Calculadora
        content_grid.grid_columnconfigure(1, weight=50, uniform="conv_cols")  # Historial
        content_grid.grid_rowconfigure(0, weight=1)


        # PANEL IZQUIERDO: Formulario de Conversión Inteligente
        form_panel = ctk.CTkFrame(content_grid, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        form_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Mini tarjeta de saldo disponible en USD dentro del formulario
        self.usd_status_box = ctk.CTkFrame(form_panel, fg_color=Theme.USD_BANNER_BG, corner_radius=10, border_width=1, border_color=Theme.USD_BANNER_BORDER)
        self.usd_status_box.pack(fill="x", padx=20, pady=(20, 14))

        status_row = ctk.CTkFrame(self.usd_status_box, fg_color="transparent")
        status_row.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(
            status_row,
            text="🏦 Saldo actual en Bóveda USD:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.USD_BANNER_TEXT
        ).pack(side="left")

        self.lbl_available_usd = ctk.CTkLabel(
            status_row,
            text="$0.00 USD",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=14, weight="bold"),
            text_color=Theme.ACCENT_BLUE
        )
        self.lbl_available_usd.pack(side="right")

        # Campo: Monto USD a Retirar
        ctk.CTkLabel(
            form_panel,
            text="Monto a retirar en Dólares ($ USD):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", padx=20, pady=(0, 4))

        self.usd_entry = ctk.CTkEntry(
            form_panel,
            placeholder_text="Ej: 300.00",
            height=38,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=14)
        )
        self.usd_entry.pack(fill="x", padx=20, pady=(0, 12))
        self.usd_entry.bind("<KeyRelease>", self._on_input_changed)

        # Campo: Tasa de Cambio (COP por USD) con botón de consulta en vivo
        rate_header = ctk.CTkFrame(form_panel, fg_color="transparent")
        rate_header.pack(fill="x", padx=20, pady=(0, 4))

        ctk.CTkLabel(
            rate_header,
            text="Tasa de Cambio (COP por 1 USD):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(side="left")

        self.btn_live_rate = ctk.CTkButton(
            rate_header,
            text="🌐 Tasa en Vivo",
            height=24,
            width=100,
            corner_radius=6,
            fg_color=Theme.BG_CARD_SUBTLE,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.ACCENT_BLUE,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._fetch_live_rate
        )
        self.btn_live_rate.pack(side="right")

        self.rate_entry = ctk.CTkEntry(
            form_panel,
            placeholder_text="Ej: 3100",
            height=38,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=14)
        )
        self.rate_entry.pack(fill="x", padx=20, pady=(0, 12))
        self.rate_entry.bind("<KeyRelease>", self._on_input_changed)

        # Campo: Fecha con DatePickerWidget
        ctk.CTkLabel(
            form_panel,
            text="Fecha de Conversión:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", padx=20, pady=(0, 4))

        from ui.components.date_picker import DatePickerWidget
        self.date_entry = DatePickerWidget(form_panel, height=38)
        self.date_entry.pack(fill="x", padx=20, pady=(0, 12))

        # Tarjeta de Vista Previa del Cálculo en Vivo
        self.preview_card = ctk.CTkFrame(form_panel, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=10, border_width=1, border_color=Theme.BORDER_SUBTLE)
        self.preview_card.pack(fill="x", padx=20, pady=(4, 16))

        preview_inner = ctk.CTkFrame(self.preview_card, fg_color="transparent")
        preview_inner.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(
            preview_inner,
            text="💰 PREVISUALIZACIÓN DE MONTO A RECIBIR:",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        self.lbl_preview_cop = ctk.CTkLabel(
            preview_inner,
            text="$0 COP",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=22, weight="bold"),
            text_color=Theme.ACCENT_GREEN
        )
        self.lbl_preview_cop.pack(anchor="w", pady=(2, 0))

        self.lbl_preview_detail = ctk.CTkLabel(
            preview_inner,
            text="Ingresa el monto y la tasa para ver el cálculo.",
            font=ctk.CTkFont(size=11),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_preview_detail.pack(anchor="w")

        # Campo: Notas / Destino bancario
        self.notes_entry = ctk.CTkEntry(
            form_panel,
            placeholder_text="Destino (ej: Retiro Wenia/Arq ➔ Cuenta Bancolombia)",
            height=36,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=12)
        )
        self.notes_entry.insert(0, "Retiro Wenia ➔ Bancolombia")
        self.notes_entry.pack(fill="x", padx=20, pady=(0, 16))

        # Botón de Confirmación
        self.btn_convert = ctk.CTkButton(
            form_panel,
            text="⚡ Ejecutar Conversión y Transferir a COP",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=42,
            corner_radius=10,
            fg_color="#6366f1",
            hover_color="#4f46e5",
            text_color="#ffffff",
            command=self._handle_convert
        )
        self.btn_convert.pack(fill="x", padx=20, pady=(0, 20))

        # PANEL DERECHO: Historial de Conversiones
        history_panel = ctk.CTkFrame(content_grid, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        history_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        hist_header = ctk.CTkFrame(history_panel, fg_color="transparent")
        hist_header.pack(fill="x", padx=20, pady=(18, 12))

        ctk.CTkLabel(
            hist_header,
            text="📜 Historial de Conversiones",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=16, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        self.lbl_conv_count = ctk.CTkLabel(
            hist_header,
            text="0 conversiones",
            font=ctk.CTkFont(size=12),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_conv_count.pack(side="right")

        self.history_scroll = ctk.CTkScrollableFrame(history_panel, fg_color="transparent")
        self.history_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def _on_input_changed(self, event=None):
        usd_str = self.usd_entry.get().strip().replace(",", ".")
        rate_str = self.rate_entry.get().strip().replace(",", ".")

        try:
            usd_val = float(usd_str) if usd_str else 0.0
            rate_val = float(rate_str) if rate_str else 0.0
            current_balance = self.db.get_usd_balance()

            if usd_val > 0 and rate_val > 0:
                cop_val = usd_val * rate_val
                self.lbl_preview_cop.configure(text=f"${cop_val:,.0f} COP")

                if usd_val > current_balance:
                    self.lbl_preview_detail.configure(
                        text=f"⚠️ Excede tu saldo disponible en Bóveda (${current_balance:,.2f} USD)",
                        text_color="#f43f5e"
                    )
                    self.btn_convert.configure(state="disabled", fg_color="#475569")
                else:
                    self.lbl_preview_detail.configure(
                        text=f"${usd_val:,.2f} USD × ${rate_val:,.2f} COP/USD",
                        text_color="#a7f3d0"
                    )
                    self.btn_convert.configure(state="normal", fg_color="#6366f1")
            else:
                self.lbl_preview_cop.configure(text="$0 COP")
                self.lbl_preview_detail.configure(
                    text="Ingresa el monto y la tasa para ver el cálculo.",
                    text_color="#64748b"
                )
                self.btn_convert.configure(state="normal", fg_color="#6366f1")
        except ValueError:
            self.lbl_preview_cop.configure(text="$0 COP")
            self.lbl_preview_detail.configure(text="Valores numéricos inválidos.", text_color="#f43f5e")

    def _fetch_live_rate(self):
        self.btn_live_rate.configure(text="⏳ Consultando...", state="disabled")
        CurrencyService.fetch_rate_async(self._on_live_rate_fetched)

    def _on_live_rate_fetched(self, rate: Optional[float]):
        def update_ui():
            self.btn_live_rate.configure(text="🌐 Tasa en Vivo", state="normal")
            if rate is not None and rate > 0:
                self.rate_entry.delete(0, "end")
                self.rate_entry.insert(0, f"{rate:.2f}")
                self._on_input_changed()
                self.toast.show(f"Tasa de cambio actualizada: ${rate:,.2f} COP por 1 USD", is_error=False)
            else:
                self.toast.show("No se pudo obtener la tasa en vivo automática. Puedes ingresarla manualmente.", is_error=True)

        self.after(0, update_ui)

    def _handle_convert(self):
        usd_str = self.usd_entry.get().strip().replace(",", ".")
        rate_str = self.rate_entry.get().strip().replace(",", ".")
        date_str = self.date_entry.get().strip()
        notes = self.notes_entry.get().strip()

        try:
            usd_amount = float(usd_str)
            exchange_rate = float(rate_str)
        except ValueError:
            self.toast.show("Ingresa números válidos para el monto USD y la tasa.", is_error=True)
            return

        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            self.toast.show("La fecha debe tener el formato YYYY-MM-DD.", is_error=True)
            return

        success, msg = self.db.execute_conversion(date_str, usd_amount, exchange_rate, notes=notes)
        if success:
            self.toast.show(msg, is_error=False)
            self.usd_entry.delete(0, "end")
            self.rate_entry.delete(0, "end")
            self.notes_entry.delete(0, "end")
            self._on_input_changed()
            self.refresh_data()
            if self.on_data_changed:
                self.on_data_changed()
        else:
            self.toast.show(msg, is_error=True)

    def refresh_data(self):
        """Actualiza el saldo disponible de la bóveda y el historial de conversiones."""
        usd_balance = self.db.get_usd_balance()
        self.lbl_available_usd.configure(text=f"${usd_balance:,.2f} USD")

        for widget in self.history_scroll.winfo_children():
            widget.destroy()

        total_count = self.db.get_conversions_count()
        conversions = self.db.get_conversions(limit=self.display_limit)

        if total_count > len(conversions):
            self.lbl_conv_count.configure(text=f"Mostrando {len(conversions)} de {total_count}")
        else:
            self.lbl_conv_count.configure(text=f"{total_count} conversiones")

        if not conversions:
            EmptyState(
                self.history_scroll,
                icon="🔄",
                title="Sin conversiones registradas",
                message="Usa el formulario superior para monetizar dólares hacia tu cuenta en COP."
            ).pack(fill="x", padx=10, pady=30)
            return

        for conv in conversions:
            card = ctk.CTkFrame(self.history_scroll, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=10, border_width=1, border_color=Theme.BORDER_SUBTLE)
            card.pack(fill="x", pady=4, padx=2)

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=14, pady=(10, 2))

            ctk.CTkLabel(
                top_row,
                text=f"🔄 -${conv['usd_amount']:,.2f} USD  ➔  +${conv['cop_amount']:,.0f} COP",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=Theme.TEXT_PRIMARY
            ).pack(side="left")

            # Fila inferior con fecha, tasa, notas y botones ✏️ y 🗑️
            bottom_row = ctk.CTkFrame(card, fg_color="transparent")
            bottom_row.pack(fill="x", padx=14, pady=(0, 10))

            info_text = f"{conv['date']} • Tasa: ${conv['exchange_rate']:,.2f} COP/USD"
            if conv["notes"]:
                info_text += f" • {conv['notes']}"

            ctk.CTkLabel(
                bottom_row,
                text=info_text,
                font=ctk.CTkFont(size=11),
                text_color=Theme.TEXT_MUTED
            ).pack(side="left")

            btn_box = ctk.CTkFrame(bottom_row, fg_color="transparent")
            btn_box.pack(side="right")

            # Botón Editar
            btn_edit = ctk.CTkButton(
                btn_box,
                text="✏️",
                width=24,
                height=20,
                fg_color="transparent",
                hover_color=Theme.BORDER_DEFAULT,
                font=ctk.CTkFont(size=11),
                command=lambda c=conv: self._handle_edit_conv(c)
            )
            btn_edit.pack(side="left", padx=1)

            # Botón Eliminar
            btn_del = ctk.CTkButton(
                btn_box,
                text="🗑️",
                width=24,
                height=20,
                fg_color="transparent",
                hover_color="#450a0a",
                font=ctk.CTkFont(size=11),
                command=lambda c=conv: self._prompt_delete_conv(c)
            )
            btn_del.pack(side="left", padx=1)

        if len(conversions) < total_count:
            btn_load_more = ctk.CTkButton(
                self.history_scroll,
                text=f"⬇️ Cargar más conversiones (+20)...",
                height=32,
                corner_radius=8,
                fg_color="#1e293b",
                hover_color="#334155",
                text_color="#818cf8",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=self._load_more
            )
            btn_load_more.pack(fill="x", pady=10, padx=2)

    def _load_more(self):
        self.display_limit += 20
        self.refresh_data()

    def _handle_edit_conv(self, conv: Dict[str, Any]):
        EditTransactionModal(
            self.winfo_toplevel(),
            self.db,
            source_table="conversions",
            record=conv,
            on_success=self._on_action_success
        )

    def _prompt_delete_conv(self, conv: Dict[str, Any]):
        ConfirmDialog(
            self.winfo_toplevel(),
            title="Confirmar Eliminación de Conversión",
            message=f"¿Deseas eliminar la conversión del {conv['date']} (-${conv['usd_amount']:,.2f} USD ➔ +${conv['cop_amount']:,.0f} COP)?\n\nEsto devolverá los dólares a la Bóveda USD y descontará los pesos del Presupuesto COP.",
            confirm_text="Eliminar",
            on_confirm=lambda: self._execute_delete_conv(conv["id"], force=False)
        )

    def _execute_delete_conv(self, conv_id: int, force: bool = False):
        success, msg, warn_data = self.db.delete_conversion(conv_id, force=force)
        if success:
            self.toast.show(msg, is_error=False)
            self._on_action_success()
        elif msg == "WARNING_NEGATIVE_BALANCE" and warn_data:
            BalanceWarningDialog(
                self.winfo_toplevel(),
                warning_data=warn_data,
                on_force_confirm=lambda: self._execute_delete_conv(conv_id, force=True)
            )
        else:
            self.toast.show(msg, is_error=True)

    def _on_action_success(self):
        self.refresh_data()
        if self.on_data_changed:
            self.on_data_changed()
