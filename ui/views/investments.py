"""
Vista de Cuentas e Inversiones (Fiducias, Bolsillos de Ahorro y Fondos USD/COP).
Permite gestionar múltiples cuentas, transferir fondos entre presupuesto e inversiones,
y registrar rendimientos e intereses generados, con soporte para Edición ✏️ y Eliminación 🗑️.
"""

import customtkinter as ctk
from datetime import datetime
from typing import Callable, Optional, Dict, Any
from ui.theme import Theme
from ui.components import (
    ToastNotification,
    StatCard,
    AccountActionModal,
    EditAccountModal,
    ConfirmDialog,
    EditTransactionModal,
    EmptyState
)
from controllers.investment_controller import InvestmentController
from core.event_bus import EventBus

class InvestmentsView(ctk.CTkFrame):
    def __init__(self, master, db_manager, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.controller = InvestmentController(db_manager)

        self._build_ui()

    def _build_ui(self):
        # 1. Toast
        self.toast = ToastNotification(self)

        # 2. Cabecera
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=Theme.SPACING_LG, pady=(Theme.SPACING_LG, Theme.SPACING_MD))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="📈 Cuentas e Inversiones",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=24, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Gestiona tus fiducias, cajitas de ahorro, billeteras y registro de rendimientos/intereses.",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=13),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # Botón Nueva Cuenta
        btn_new_acc = ctk.CTkButton(
            header_frame,
            text="➕ Nueva Cuenta / Fiducia",
            height=36,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.INFO,
            hover_color=Theme.INFO_HOVER,
            text_color=Theme.TEXT_ON_COLOR,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._handle_create_account
        )
        btn_new_acc.pack(side="right")

        # 3. Fila de Tarjetas de Resumen
        summary_container = ctk.CTkFrame(self, fg_color="transparent")
        summary_container.pack(fill="x", padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_MD))
        summary_container.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="inv_stat_cards")

        self.card_cop_invested = StatCard(
            summary_container,
            title="Invertido en COP",
            value="$0 COP",
            subtitle="Fiducias y cajitas COP",
            icon="🇨🇴",
            accent_color=Theme.ACCENT_COP,
            value_color=Theme.ACCENT_COP,
            bg_color=Theme.BG_CARD,
            border_color=Theme.BORDER_DEFAULT
        )
        self.card_cop_invested.grid(row=0, column=0, padx=(0, Theme.SPACING_SM), sticky="nsew")

        self.card_usd_invested = StatCard(
            summary_container,
            title="Invertido en USD",
            value="$0.00 USD",
            subtitle="Fondos y billeteras USD",
            icon="💵",
            accent_color=Theme.ACCENT_USD,
            value_color=Theme.ACCENT_USD,
            bg_color=Theme.BG_CARD,
            border_color=Theme.BORDER_DEFAULT
        )
        self.card_usd_invested.grid(row=0, column=1, padx=Theme.SPACING_XS, sticky="nsew")

        self.card_cop_yields = StatCard(
            summary_container,
            title="Rendimientos COP",
            value="+$0 COP",
            subtitle="Intereses acumulados",
            icon="📈",
            accent_color=Theme.ACCENT_COP,
            value_color=Theme.ACCENT_COP,
            bg_color=Theme.BG_CARD,
            border_color=Theme.BORDER_DEFAULT
        )
        self.card_cop_yields.grid(row=0, column=2, padx=Theme.SPACING_XS, sticky="nsew")

        self.card_usd_yields = StatCard(
            summary_container,
            title="Rendimientos USD",
            value="+$0.00 USD",
            subtitle="Ganancias en dólares",
            icon="📊",
            accent_color=Theme.ACCENT_USD,
            value_color=Theme.ACCENT_USD,
            bg_color=Theme.BG_CARD,
            border_color=Theme.BORDER_DEFAULT
        )
        self.card_usd_yields.grid(row=0, column=3, padx=(Theme.SPACING_SM, 0), sticky="nsew")

        # 4. Selector de Filtro de Cuentas (Todas / COP / USD)
        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.pack(fill="x", padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_SM))

        self.currency_filter = ctk.CTkSegmentedButton(
            filter_bar,
            values=["Todas las Cuentas", "🇨🇴 Cuentas COP", "💵 Cuentas USD"],
            height=32,
            command=lambda _: self._refresh_accounts_grid()
        )
        self.currency_filter.set("Todas las Cuentas")
        self.currency_filter.pack(side="left")

        # 5. Contenedor Dividido: Grid de Cuentas (Arriba) + Historial de Rendimientos/Aportes (Abajo)
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.pack(fill="both", expand=True, padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_LG))
        main_content.grid_rowconfigure(0, weight=6)
        main_content.grid_rowconfigure(1, weight=4)
        main_content.grid_columnconfigure(0, weight=1)

        # Panel de Cuentas (Scrollable)
        accounts_panel = ctk.CTkFrame(main_content, fg_color=Theme.BG_CARD, corner_radius=Theme.SPACING_MD, border_width=1, border_color=Theme.BORDER_DEFAULT)
        accounts_panel.grid(row=0, column=0, sticky="nsew", pady=(0, Theme.SPACING_SM))

        acc_header = ctk.CTkFrame(accounts_panel, fg_color="transparent")
        acc_header.pack(fill="x", padx=Theme.SPACING_MD, pady=(Theme.SPACING_MD, Theme.SPACING_SM))

        ctk.CTkLabel(
            acc_header,
            text="🏦 Cuentas, Fiducias y Bolsillos Activos",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=15, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        self.accounts_scroll = ctk.CTkScrollableFrame(accounts_panel, fg_color="transparent")
        self.accounts_scroll.pack(fill="both", expand=True, padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_MD))

        # Panel Inferior: Historial de Transacciones de Inversión
        history_panel = ctk.CTkFrame(main_content, fg_color=Theme.BG_CARD, corner_radius=Theme.SPACING_MD, border_width=1, border_color=Theme.BORDER_DEFAULT)
        history_panel.grid(row=1, column=0, sticky="nsew")

        hist_header = ctk.CTkFrame(history_panel, fg_color="transparent")
        hist_header.pack(fill="x", padx=Theme.SPACING_MD, pady=(Theme.SPACING_SM, Theme.SPACING_XS))

        ctk.CTkLabel(
            hist_header,
            text="📜 Historial de Rendimientos, Aportes y Retiros",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=14, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        self.history_scroll = ctk.CTkScrollableFrame(history_panel, fg_color="transparent", height=130)
        self.history_scroll.pack(fill="both", expand=True, padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_SM))

    def _handle_create_account(self):
        EditAccountModal(
            self.winfo_toplevel(),
            self.controller.db,
            account=None,
            on_success=self._on_account_saved
        )

    def _handle_edit_account(self, account: Dict[str, Any]):
        EditAccountModal(
            self.winfo_toplevel(),
            self.controller.db,
            account=account,
            on_success=self._on_account_saved
        )

    def _on_account_saved(self):
        self.toast.show("Cuenta actualizada exitosamente.", is_error=False)
        EventBus.publish("DATA_UPDATED")

    def _open_account_action(self, account: Dict[str, Any], action_type: str):
        AccountActionModal(
            self.winfo_toplevel(),
            self.controller.db,
            account=account,
            initial_action=action_type,
            on_success=self._on_action_success
        )

    def _on_action_success(self):
        self.toast.show("Movimiento registrado con éxito.", is_error=False)
        EventBus.publish("DATA_UPDATED")

    def refresh_data(self):
        """Actualiza todas las métricas, tarjetas y listas."""
        summary = self.controller.get_investments_summary()

        self.card_cop_invested.update_value(
            f"${summary['total_cop_invested']:,.0f} COP",
            f"{len([a for a in summary['accounts'] if a['currency'] == 'COP'])} cuentas activas",
            new_color=Theme.ACCENT_COP
        )
        self.card_usd_invested.update_value(
            f"${summary['total_usd_invested']:,.2f} USD",
            f"{len([a for a in summary['accounts'] if a['currency'] == 'USD'])} cuentas activas",
            new_color=Theme.ACCENT_USD
        )
        self.card_cop_yields.update_value(
            f"+${summary['total_cop_yields']:,.0f} COP",
            "Intereses acumulados",
            new_color=Theme.ACCENT_COP
        )
        self.card_usd_yields.update_value(
            f"+${summary['total_usd_yields']:,.2f} USD",
            "Ganancias acumuladas",
            new_color=Theme.ACCENT_USD
        )

        self._refresh_accounts_grid()
        self._refresh_history_list()

    def _refresh_accounts_grid(self):
        for widget in self.accounts_scroll.winfo_children():
            widget.destroy()

        choice = self.currency_filter.get()
        curr = None
        if "COP" in choice:
            curr = "COP"
        elif "USD" in choice:
            curr = "USD"

        accounts = self.controller.get_accounts(currency=curr, only_active=True)

        if not accounts:
            EmptyState(
                self.accounts_scroll,
                icon="🏦",
                title="Sin cuentas registradas",
                message="Crea una cuenta, fiducia o bolsillo para monitorear tu patrimonio.",
                action_text="+ Nueva Cuenta",
                action_command=self._handle_create_account,
                action_variant="primary"
            ).pack(fill="x", padx=Theme.SPACING_SM, pady=Theme.SPACING_LG)
            return

        for acc in accounts:
            currency = acc["currency"]
            bal = acc["current_balance"]
            bal_str = f"${bal:,.2f} USD" if currency == "USD" else f"${bal:,.0f} COP"
            yields_str = f"+${acc['total_yields']:,.2f} USD" if currency == "USD" else f"+${acc['total_yields']:,.0f} COP"
            icon = acc.get("icon", "📈")

            card = ctk.CTkFrame(self.accounts_scroll, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.BORDER_SUBTLE)
            card.pack(fill="x", pady=Theme.SPACING_XS, padx=Theme.SPACING_XS)

            # Contenedor principal de la tarjeta de cuenta
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=Theme.SPACING_MD, pady=Theme.SPACING_SM)

            # Columna Izquierda: Información de la cuenta
            info_col = ctk.CTkFrame(inner, fg_color="transparent")
            info_col.pack(side="left", fill="both", expand=True)

            title_row = ctk.CTkFrame(info_col, fg_color="transparent")
            title_row.pack(anchor="w")

            ctk.CTkLabel(
                title_row,
                text=f"{icon}  {acc['name']}",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=Theme.TEXT_PRIMARY
            ).pack(side="left")

            ctk.CTkLabel(
                title_row,
                text=f"[{acc['currency']}]",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=Theme.ACCENT_GREEN if currency == "COP" else Theme.ACCENT_BLUE
            ).pack(side="left", padx=(Theme.SPACING_SM, 0))

            sub_text = f"{acc.get('institution', 'Personal')} • Rendimientos: {yields_str}"
            ctk.CTkLabel(
                info_col,
                text=sub_text,
                font=ctk.CTkFont(size=11),
                text_color=Theme.TEXT_MUTED
            ).pack(anchor="w", pady=(Theme.SPACING_XS, 0))

            # Columna Central: Saldo actual
            bal_col = ctk.CTkFrame(inner, fg_color="transparent")
            bal_col.pack(side="left", padx=Theme.SPACING_MD)

            ctk.CTkLabel(
                bal_col,
                text=bal_str,
                font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=17, weight="bold"),
                text_color=Theme.ACCENT_GREEN if currency == "COP" else Theme.ACCENT_BLUE
            ).pack(anchor="e")

            # Columna Derecha: Botones de Acción Rápida
            btns_col = ctk.CTkFrame(inner, fg_color="transparent")
            btns_col.pack(side="right")

            btn_yield = ctk.CTkButton(
                btns_col,
                text="📈 +Rendimiento",
                width=100,
                height=30,
                corner_radius=Theme.SPACING_XS,
                fg_color=Theme.SUCCESS,
                hover_color=Theme.SUCCESS,
                text_color=Theme.TEXT_ON_COLOR,
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda a=acc: self._open_account_action(a, "YIELD")
            )
            btn_yield.pack(side="left", padx=Theme.SPACING_XS)

            btn_deposit = ctk.CTkButton(
                btns_col,
                text="📥 Aportar",
                width=75,
                height=30,
                corner_radius=Theme.SPACING_XS,
                fg_color=Theme.INFO,
                hover_color=Theme.INFO_HOVER,
                text_color=Theme.TEXT_ON_COLOR,
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda a=acc: self._open_account_action(a, "TRANSFER_TO")
            )
            btn_deposit.pack(side="left", padx=Theme.SPACING_XS)

            btn_withdraw = ctk.CTkButton(
                btns_col,
                text="📤 Retirar",
                width=75,
                height=30,
                corner_radius=Theme.SPACING_XS,
                fg_color=Theme.ERROR,
                hover_color=Theme.ERROR_HOVER,
                text_color=Theme.TEXT_ON_COLOR,
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda a=acc: self._open_account_action(a, "TRANSFER_FROM")
            )
            btn_withdraw.pack(side="left", padx=Theme.SPACING_XS)

            btn_edit = ctk.CTkButton(
                btns_col,
                text="⚙️",
                width=30,
                height=30,
                corner_radius=Theme.SPACING_XS,
                fg_color=Theme.BG_INPUT,
                hover_color=Theme.BORDER_DEFAULT,
                font=ctk.CTkFont(size=12),
                command=lambda a=acc: self._handle_edit_account(a)
            )
            btn_edit.pack(side="left", padx=(Theme.SPACING_XS, 0))

    def _refresh_history_list(self):
        for widget in self.history_scroll.winfo_children():
            widget.destroy()

        transactions = self.controller.get_account_transactions(limit=25)

        if not transactions:
            EmptyState(
                self.history_scroll,
                icon="📈",
                title="Sin movimientos registrados",
                message="Los aportes, retiros y rendimientos que registres aparecerán aquí.",
                compact=True
            ).pack(fill="x", padx=Theme.SPACING_SM, pady=Theme.SPACING_MD)
            return

        for tx in transactions:
            t_type = tx["type"]
            curr = tx["currency"]
            amt = tx["amount"]
            amt_str = f"+${amt:,.2f} USD" if curr == "USD" else f"+${amt:,.0f} COP"
            accent = Theme.ACCENT_GREEN

            if t_type == "YIELD":
                badge = "📈 Rendimiento / Intereses"
                accent = Theme.ACCENT_GREEN
            elif t_type in ("DEPOSIT", "TRANSFER_IN"):
                badge = "📥 Aporte a Cuenta"
                accent = Theme.ACCENT_BLUE
            else:
                badge = "📤 Retiro de Cuenta"
                amt_str = f"-${amt:,.2f} USD" if curr == "USD" else f"-${amt:,.0f} COP"
                accent = Theme.ACCENT_ROSE

            card = ctk.CTkFrame(self.history_scroll, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.BORDER_SUBTLE)
            card.pack(fill="x", pady=Theme.SPACING_XS, padx=Theme.SPACING_XS)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=Theme.SPACING_SM, pady=Theme.SPACING_XS)

            ctk.CTkLabel(
                row,
                text=f"{tx['date']} • {tx['account_name']} [{badge}]",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=Theme.TEXT_PRIMARY
            ).pack(side="left")

            btn_box = ctk.CTkFrame(row, fg_color="transparent")
            btn_box.pack(side="right")

            ctk.CTkLabel(
                btn_box,
                text=amt_str,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=accent
            ).pack(side="left", padx=(0, Theme.SPACING_SM))

            btn_edit = ctk.CTkButton(
                btn_box,
                text="✏️",
                width=24,
                height=20,
                fg_color="transparent",
                hover_color=Theme.BORDER_DEFAULT,
                font=ctk.CTkFont(size=11),
                command=lambda t=tx: self._handle_edit_tx(t)
            )
            btn_edit.pack(side="left", padx=Theme.SPACING_XS)

            btn_del = ctk.CTkButton(
                btn_box,
                text="🗑️",
                width=24,
                height=20,
                fg_color="transparent",
                hover_color=Theme.ERROR_HOVER,
                font=ctk.CTkFont(size=11),
                command=lambda t=tx: self._prompt_delete_tx(t)
            )
            btn_del.pack(side="left", padx=Theme.SPACING_XS)

    def _handle_edit_tx(self, tx: Dict[str, Any]):
        EditTransactionModal(
            self.winfo_toplevel(),
            self.controller.db,
            source_table="account_transactions",
            record=tx,
            on_success=self._on_action_success
        )

    def _prompt_delete_tx(self, tx: Dict[str, Any]):
        ConfirmDialog(
            self.winfo_toplevel(),
            title="Eliminar Movimiento de Inversión",
            message=f"¿Deseas eliminar el movimiento de {tx['account_name']} del {tx['date']}?",
            confirm_text="Eliminar",
            on_confirm=lambda: self._execute_delete_tx(tx["id"])
        )

    def _execute_delete_tx(self, tx_id: int):
        success, msg, _ = self.controller.delete_account_transaction(tx_id)
        if success:
            self.toast.show("Movimiento eliminado con éxito.", is_error=False)
            self._on_action_success()
        else:
            self.toast.show(msg, is_error=True)
