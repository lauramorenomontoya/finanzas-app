import customtkinter as ctk
from typing import Callable, Optional, Dict, Any
from ui.theme import Theme
from ui.components import EditAccountModal, ConfirmDialog
from core.event_bus import EventBus

class AccountsTab(ctk.CTkFrame):
    def __init__(self, master, controller, toast, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.controller = controller
        self.toast = toast

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        panel = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=Theme.SPACING_MD, border_width=1, border_color=Theme.BORDER_DEFAULT)
        panel.grid(row=0, column=0, sticky="nsew")

        p_header = ctk.CTkFrame(panel, fg_color="transparent")
        p_header.pack(fill="x", padx=Theme.SPACING_LG, pady=(Theme.SPACING_MD, Theme.SPACING_SM))

        ctk.CTkLabel(
            p_header,
            text="🏦 Administración de Cuentas, Bolsillos y Fiducias",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=16, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        btn_new_acc = ctk.CTkButton(
            p_header,
            text="➕ Añadir Cuenta",
            height=32,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS,
            text_color=Theme.TEXT_ON_COLOR,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._handle_create_account
        )
        btn_new_acc.pack(side="right")

        self.accounts_crud_scroll = ctk.CTkScrollableFrame(panel, fg_color="transparent")
        self.accounts_crud_scroll.pack(fill="both", expand=True, padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_MD))

    def refresh_data(self):
        for widget in self.accounts_crud_scroll.winfo_children():
            widget.destroy()

        accounts = self.controller.get_accounts(only_active=False)

        if not accounts:
            ctk.CTkLabel(
                self.accounts_crud_scroll,
                text="No hay cuentas registradas.",
                font=ctk.CTkFont(size=12),
                text_color=Theme.TEXT_MUTED
            ).pack(pady=Theme.SPACING_XL)
            return

        for acc in accounts:
            card = ctk.CTkFrame(self.accounts_crud_scroll, fg_color=Theme.BG_CARD_SUBTLE, corner_radius=Theme.SPACING_SM, border_width=1, border_color=Theme.BORDER_SUBTLE)
            card.pack(fill="x", pady=Theme.SPACING_XS, padx=Theme.SPACING_XS)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=Theme.SPACING_MD, pady=Theme.SPACING_SM)

            left_box = ctk.CTkFrame(inner, fg_color="transparent")
            left_box.pack(side="left", fill="both", expand=True)

            icon = acc.get("icon", "📈")
            active_badge = "" if acc.get("is_active", 1) == 1 else " (Inactiva)"
            ctk.CTkLabel(
                left_box,
                text=f"{icon}  {acc['name']}{active_badge}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=Theme.TEXT_PRIMARY if acc.get("is_active", 1) == 1 else Theme.TEXT_MUTED
            ).pack(anchor="w")

            curr = acc["currency"]
            bal_str = f"${acc['current_balance']:,.2f} USD" if curr == "USD" else f"${acc['current_balance']:,.0f} COP"
            ctk.CTkLabel(
                left_box,
                text=f"Institución: {acc.get('institution', 'N/A')} • Moneda: {curr} • Saldo: {bal_str}",
                font=ctk.CTkFont(size=11),
                text_color=Theme.TEXT_MUTED
            ).pack(anchor="w", pady=(Theme.SPACING_XS, 0))

            btns = ctk.CTkFrame(inner, fg_color="transparent")
            btns.pack(side="right")

            btn_edit = ctk.CTkButton(
                btns,
                text="✏️ Editar",
                width=65,
                height=28,
                corner_radius=Theme.SPACING_XS,
                fg_color=Theme.BG_INPUT,
                hover_color=Theme.BORDER_DEFAULT,
                font=ctk.CTkFont(size=11),
                command=lambda a=acc: self._handle_edit_account(a)
            )
            btn_edit.pack(side="left", padx=Theme.SPACING_XS)

            btn_del = ctk.CTkButton(
                btns,
                text="🗑️",
                width=28,
                height=28,
                corner_radius=Theme.SPACING_XS,
                fg_color="transparent",
                hover_color=Theme.ERROR_HOVER,
                font=ctk.CTkFont(size=11),
                command=lambda aid=acc["id"], name=acc["name"]: self._prompt_delete_account(aid, name)
            )
            btn_del.pack(side="left")

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
        self.toast.show("Cuenta guardada correctamente.", is_error=False)
        self.refresh_data()
        EventBus.publish("DATA_UPDATED")

    def _prompt_delete_account(self, acc_id: int, acc_name: str):
        ConfirmDialog(
            self.winfo_toplevel(),
            title="Eliminar / Archivar Cuenta",
            message=f"¿Deseas eliminar o desactivar la cuenta '{acc_name}'?",
            confirm_text="Eliminar",
            on_confirm=lambda: self._execute_delete_account(acc_id)
        )

    def _execute_delete_account(self, acc_id: int):
        success, msg = self.controller.delete_account(acc_id)
        self.toast.show(msg, is_error=not success)
        if success:
            self.refresh_data()
            EventBus.publish("DATA_UPDATED")
