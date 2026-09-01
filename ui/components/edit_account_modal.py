"""
Modal para Crear o Editar Cuentas y Bolsillos de Inversión (Fiducias, Ahorro, USD).
Diseño responsivo con pie fijo de botones y cuerpo desplazable.
"""

import customtkinter as ctk
from typing import Callable, Optional, Dict, Any
from ui.theme import Theme


class EditAccountModal(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        db_manager,
        account: Optional[Dict[str, Any]] = None,
        on_success: Callable[[], None] = None
    ):
        super().__init__(parent)
        self.db = db_manager
        self.account = account
        self.on_success = on_success
        self.is_edit = account is not None

        title_str = "Editar Cuenta / Fiducia" if self.is_edit else "Nueva Cuenta / Fiducia"
        self.title(title_str)
        self.geometry("500x600")
        self.minsize(460, 480)
        self.resizable(True, True)
        self.configure(fg_color=Theme.BG_WINDOW)

        self.transient(parent)
        self.grab_set()
        self._center_window(parent)

        self._build_ui()

    def _center_window(self, parent):
        self.update_idletasks()
        try:
            parent_x = parent.winfo_rootx()
            parent_y = parent.winfo_rooty()
            parent_w = parent.winfo_width()
            parent_h = parent.winfo_height()
            x = parent_x + (parent_w - 500) // 2
            y = parent_y + (parent_h - 600) // 2
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

    def _build_ui(self):
        main_frame = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=14, border_width=1, border_color=Theme.BORDER_DEFAULT)
        main_frame.pack(fill="both", expand=True, padx=16, pady=16)

        # 1. Encabezado Fijo Superior
        header = ctk.CTkFrame(main_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 10))

        title_text = "✏️ Editar Cuenta o Fiducia" if self.is_edit else "➕ Nueva Cuenta o Fiducia"
        ctk.CTkLabel(
            header,
            text=title_text,
            font=ctk.CTkFont(family="SF Pro Display", size=18, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Administra fiducias, cajitas de ahorro, billeteras USD o cuentas de inversión.",
            font=ctk.CTkFont(family="SF Pro Text", size=12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", pady=(2, 0))

        # 2. Pie Fijo Inferior con Botones (SIEMPRE VISIBLE)
        footer = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=20, pady=(0, 16))

        self.lbl_error = ctk.CTkLabel(footer, text="", font=ctk.CTkFont(size=11), text_color=Theme.ACCENT_ROSE)
        self.lbl_error.pack(anchor="w", pady=(0, 6))

        btn_row = ctk.CTkFrame(footer, fg_color="transparent")
        btn_row.pack(fill="x")

        btn_cancel = ctk.CTkButton(
            btn_row,
            text="Cancelar",
            font=ctk.CTkFont(size=12),
            height=38,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            hover_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_SECONDARY,
            command=self.destroy
        )
        btn_cancel.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_save = ctk.CTkButton(
            btn_row,
            text="💾 Guardar Cuenta",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            corner_radius=8,
            fg_color="#0284c7",
            hover_color="#0369a1",
            text_color="#ffffff",
            command=self._handle_save
        )
        btn_save.pack(side="right", fill="x", expand=True, padx=(8, 0))

        # 3. Cuerpo Desplazable Central
        scroll_body = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll_body.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        # Campo Nombre
        ctk.CTkLabel(scroll_body, text="Nombre de la Cuenta / Fiducia:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=6, pady=(0, 4))
        self.name_entry = ctk.CTkEntry(
            scroll_body,
            placeholder_text="Ej: Fiducuenta Bancolombia / Cajita Nu / Arc USD",
            height=36,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=13)
        )
        if self.is_edit:
            self.name_entry.insert(0, self.account["name"])
        self.name_entry.pack(fill="x", padx=6, pady=(0, 12))

        # Fila: Moneda y Tipo
        row_type = ctk.CTkFrame(scroll_body, fg_color="transparent")
        row_type.pack(fill="x", padx=6, pady=(0, 12))
        row_type.grid_columnconfigure((0, 1), weight=1)

        # Moneda
        col_curr = ctk.CTkFrame(row_type, fg_color="transparent")
        col_curr.grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkLabel(col_curr, text="Moneda:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        self.curr_combo = ctk.CTkComboBox(
            col_curr,
            values=["COP", "USD"],
            height=36,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            dropdown_fg_color=Theme.BG_CARD
        )
        if self.is_edit:
            self.curr_combo.set(self.account["currency"])
            self.curr_combo.configure(state="disabled")
        else:
            self.curr_combo.set("COP")
        self.curr_combo.pack(fill="x")

        # Tipo de Cuenta
        col_kind = ctk.CTkFrame(row_type, fg_color="transparent")
        col_kind.grid(row=0, column=1, padx=(6, 0), sticky="ew")
        ctk.CTkLabel(col_kind, text="Tipo de Cuenta:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        self.type_combo = ctk.CTkComboBox(
            col_kind,
            values=["Fiducia / Inversión", "Ahorro / Rendimiento", "Billetera Digital", "Operativa"],
            height=36,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            dropdown_fg_color=Theme.BG_CARD
        )
        if self.is_edit:
            t_map = {"INVERSION_FIDUCIA": "Fiducia / Inversión", "AHORRO": "Ahorro / Rendimiento", "BILLETERA": "Billetera Digital", "OPERATIVA": "Operativa"}
            self.type_combo.set(t_map.get(self.account["account_type"], "Fiducia / Inversión"))
        else:
            self.type_combo.set("Fiducia / Inversión")
        self.type_combo.pack(fill="x")

        # Campo Institución
        ctk.CTkLabel(scroll_body, text="Institución / Banco / Plataforma:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=6, pady=(0, 4))
        self.inst_entry = ctk.CTkEntry(
            scroll_body,
            placeholder_text="Ej: Bancolombia, Nu, Wenia, Lulo, IBKR",
            height=36,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=13)
        )
        if self.is_edit:
            self.inst_entry.insert(0, self.account.get("institution", "") or "")
        self.inst_entry.pack(fill="x", padx=6, pady=(0, 12))

        # Fila: Ícono y Saldo Inicial
        row_icon_bal = ctk.CTkFrame(scroll_body, fg_color="transparent")
        row_icon_bal.pack(fill="x", padx=6, pady=(0, 12))
        row_icon_bal.grid_columnconfigure(0, weight=3)
        row_icon_bal.grid_columnconfigure(1, weight=7)

        # Ícono
        col_ico = ctk.CTkFrame(row_icon_bal, fg_color="transparent")
        col_ico.grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkLabel(col_ico, text="Emoji:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        self.icon_entry = ctk.CTkEntry(
            col_ico,
            height=36,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=13)
        )
        self.icon_entry.insert(0, self.account.get("icon", "📈") if self.is_edit else "📈")
        self.icon_entry.pack(fill="x")

        # Saldo Inicial
        col_bal = ctk.CTkFrame(row_icon_bal, fg_color="transparent")
        col_bal.grid(row=0, column=1, padx=(6, 0), sticky="ew")
        ctk.CTkLabel(col_bal, text="Saldo Inicial:", font=ctk.CTkFont(size=12, weight="bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        self.bal_entry = ctk.CTkEntry(
            col_bal,
            placeholder_text="0",
            height=36,
            corner_radius=8,
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_DEFAULT,
            font=ctk.CTkFont(size=13)
        )
        if self.is_edit:
            self.bal_entry.insert(0, str(self.account.get("initial_balance", 0.0)))
            self.bal_entry.configure(state="disabled")
        else:
            self.bal_entry.insert(0, "0")
        self.bal_entry.pack(fill="x")

    def _handle_save(self):
        name = self.name_entry.get().strip()
        curr = self.curr_combo.get().strip()
        type_str = self.type_combo.get().strip()
        institution = self.inst_entry.get().strip()
        icon = self.icon_entry.get().strip() or "📈"
        bal_raw = self.bal_entry.get().strip().replace(".", "").replace(",", ".")

        if not name:
            self.lbl_error.configure(text="⚠️ Ingresa un nombre para la cuenta.")
            return

        type_code = "INVERSION_FIDUCIA"
        if "Ahorro" in type_str:
            type_code = "AHORRO"
        elif "Billetera" in type_str:
            type_code = "BILLETERA"
        elif "Operativa" in type_str:
            type_code = "OPERATIVA"

        try:
            init_bal = float(bal_raw) if bal_raw else 0.0
            if init_bal < 0:
                raise ValueError()
        except ValueError:
            self.lbl_error.configure(text="⚠️ El saldo inicial debe ser un número mayor o igual a 0.")
            return

        try:
            if self.is_edit:
                self.db.update_account(
                    account_id=self.account["id"],
                    name=name,
                    account_type=type_code,
                    institution=institution,
                    color="#10b981" if curr == "COP" else "#38bdf8",
                    icon=icon
                )
            else:
                self.db.create_account(
                    name=name,
                    currency=curr,
                    account_type=type_code,
                    institution=institution,
                    initial_balance=init_bal,
                    color="#10b981" if curr == "COP" else "#38bdf8",
                    icon=icon
                )

            if self.on_success:
                self.on_success()
            self.destroy()

        except Exception as e:
            self.lbl_error.configure(text=f"⚠️ Error al guardar cuenta: {str(e)}")
