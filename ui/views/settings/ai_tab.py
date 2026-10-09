"""
Pestaña de Conexión con Asistentes de IA (MCP) para Montu.
Permite vincular la base de datos con Google Antigravity, Claude Desktop o Cursor en 1-clic.
"""

import os
import customtkinter as ctk
from typing import Optional, Dict, Any
from ui.theme import Theme
from services.ai_connection_service import AIConnectionService


class AITab(ctk.CTkFrame):
    def __init__(self, master, controller, toast, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.controller = controller
        self.toast = toast

        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=52, uniform="settings_ai")
        self.grid_columnconfigure(1, weight=48, uniform="settings_ai")
        self.grid_rowconfigure(0, weight=1)

        # ----------------------------------------------------
        # Panel Izquierdo: Estado y Conexión Automática
        # ----------------------------------------------------
        left_panel = ctk.CTkFrame(
            self,
            fg_color=Theme.BG_CARD,
            corner_radius=Theme.SPACING_MD,
            border_width=1,
            border_color=Theme.BORDER_DEFAULT
        )
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, Theme.SPACING_SM))

        # Cabecera Izquierda
        header_box = ctk.CTkFrame(left_panel, fg_color="transparent")
        header_box.pack(fill="x", padx=Theme.SPACING_LG, pady=(Theme.SPACING_LG, Theme.SPACING_SM))

        ctk.CTkLabel(
            header_box,
            text="🤖 Conexión con tu IA Favorita (MCP)",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=16, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_box,
            text="Conecta tu base de datos para registrar gastos y consultar balances mediante lenguaje natural.",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12),
            text_color=Theme.TEXT_MUTED,
            wraplength=420,
            justify="left"
        ).pack(anchor="w", pady=(Theme.SPACING_XS, 0))

        # Botón Grande de 1-Clic
        action_box = ctk.CTkFrame(left_panel, fg_color="transparent")
        action_box.pack(fill="x", padx=Theme.SPACING_LG, pady=(Theme.SPACING_SM, Theme.SPACING_MD))

        self.btn_connect_all = ctk.CTkButton(
            action_box,
            text="⚡ Conectar con mi IA con 1-Clic",
            height=42,
            corner_radius=Theme.SPACING_SM,
            fg_color=Theme.INFO,
            hover_color=Theme.INFO_HOVER,
            text_color=Theme.TEXT_ON_COLOR,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_connect_all_click
        )
        self.btn_connect_all.pack(fill="x")

        # Separador
        sep = ctk.CTkFrame(left_panel, height=1, fg_color=Theme.BORDER_DEFAULT)
        sep.pack(fill="x", padx=Theme.SPACING_LG, pady=(Theme.SPACING_XS, Theme.SPACING_MD))

        # Subtítulo de Clientes Detectados
        ctk.CTkLabel(
            left_panel,
            text="ESTADO DE ASISTENTES DETECTADOS:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", padx=Theme.SPACING_LG, pady=(0, Theme.SPACING_SM))

        # Scroll de Clientes
        self.clients_scroll = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        self.clients_scroll.pack(fill="both", expand=True, padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_MD))

        # ----------------------------------------------------
        # Panel Derecho: Guía de Uso & Prompts Recomendados
        # ----------------------------------------------------
        right_panel = ctk.CTkFrame(
            self,
            fg_color=Theme.BG_CARD,
            corner_radius=Theme.SPACING_MD,
            border_width=1,
            border_color=Theme.BORDER_DEFAULT
        )
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(Theme.SPACING_SM, 0))

        right_header = ctk.CTkFrame(right_panel, fg_color="transparent")
        right_header.pack(fill="x", padx=Theme.SPACING_LG, pady=(Theme.SPACING_LG, Theme.SPACING_SM))

        ctk.CTkLabel(
            right_header,
            text="💡 ¿Qué puedes pedirle a tu IA?",
            font=ctk.CTkFont(family=Theme.FONT_DISPLAY, size=15, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            right_header,
            text="Una vez conectada, puedes hablarle directamente a tu IA como a un contador personal:",
            font=ctk.CTkFont(family=Theme.FONT_TEXT, size=12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", pady=(Theme.SPACING_XS, 0))

        # Prompts de Ejemplo
        prompts_scroll = ctk.CTkScrollableFrame(right_panel, fg_color="transparent")
        prompts_scroll.pack(fill="both", expand=True, padx=Theme.SPACING_MD, pady=(0, Theme.SPACING_MD))

        examples = [
            (
                "💸 Registrar un Gasto",
                "\"Gasté 35 mil en almuerzo con amigos pagado con débito hoy\"",
                "La IA infiere automáticamente la categoría, fecha y descuenta el saldo en tu base de datos."
            ),
            (
                "📊 Consultar Balances",
                "\"¿Cuál es mi liquidez actual en USD y COP y cómo va mi mes?\"",
                "Consulta saldos de Bóveda USD, cuentas COP y TRM en tiempo real."
            ),
            (
                "📥 Registrar Ingresos",
                "\"Registra un depósito de $850 USD recibido en Wenia\"",
                "Añade fondos a tu Bóveda USD y actualiza tu patrimonio consolidado."
            ),
            (
                "🎯 Presupuesto & Metas",
                "\"¿Cómo va mi presupuesto de este mes? ¿En qué categoría he gastado más?\"",
                "Calcula el porcentaje de ejecución de cada categoría vs tu meta mensual."
            ),
            (
                "🔍 Análisis Personalizado",
                "\"¿Cuánto he gastado en transporte en los últimos 3 meses?\"",
                "Ejecuta consultas analíticas seguras de solo lectura sobre tu historial."
            )
        ]

        for title, prompt_text, desc in examples:
            card = ctk.CTkFrame(
                prompts_scroll,
                fg_color=Theme.BG_CARD_SUBTLE,
                corner_radius=Theme.SPACING_SM,
                border_width=1,
                border_color=Theme.BORDER_DEFAULT
            )
            card.pack(fill="x", pady=(0, Theme.SPACING_SM), padx=Theme.SPACING_XS)

            # Título y botón copiar
            top_line = ctk.CTkFrame(card, fg_color="transparent")
            top_line.pack(fill="x", padx=Theme.SPACING_MD, pady=(Theme.SPACING_SM, 0))

            ctk.CTkLabel(
                top_line,
                text=title,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=Theme.TEXT_PRIMARY
            ).pack(side="left")

            btn_copy = ctk.CTkButton(
                top_line,
                text="Copiar",
                width=55,
                height=22,
                corner_radius=4,
                fg_color="transparent",
                border_width=1,
                border_color=Theme.BORDER_DEFAULT,
                text_color=Theme.TEXT_SECONDARY,
                font=ctk.CTkFont(size=10),
                command=lambda p=prompt_text: self._copy_to_clipboard(p)
            )
            btn_copy.pack(side="right")

            # Texto del Prompt
            prompt_lbl = ctk.CTkLabel(
                card,
                text=prompt_text,
                font=ctk.CTkFont(family=Theme.FONT_TEXT, size=11, slant="italic"),
                text_color=Theme.ACCENT_BLUE,
                wraplength=340,
                justify="left"
            )
            prompt_lbl.pack(anchor="w", padx=Theme.SPACING_MD, pady=(Theme.SPACING_XS, 0))

            # Explicación
            desc_lbl = ctk.CTkLabel(
                card,
                text=desc,
                font=ctk.CTkFont(family=Theme.FONT_TEXT, size=10),
                text_color=Theme.TEXT_MUTED,
                wraplength=340,
                justify="left"
            )
            desc_lbl.pack(anchor="w", padx=Theme.SPACING_MD, pady=(2, Theme.SPACING_SM))

    def _copy_to_clipboard(self, text: str):
        clean = text.strip('"')
        self.clipboard_clear()
        self.clipboard_append(clean)
        self.toast.show("Prompt copiado al portapapeles", is_error=False)

    def _on_connect_all_click(self):
        self.btn_connect_all.configure(state="disabled", text="⏳ Configurando...")
        self.update_idletasks()

        ok, msg, connected = AIConnectionService.connect_all_detected()
        self.btn_connect_all.configure(state="normal", text="⚡ Conectar con mi IA con 1-Clic")

        if ok:
            self.toast.show(msg, is_error=False)
        else:
            self.toast.show(msg, is_error=True)

        self.refresh_data()

    def _connect_single(self, client_id: str):
        ok, msg = AIConnectionService.connect_client(client_id)
        self.toast.show(msg, is_error=not ok)
        self.refresh_data()

    def refresh_data(self):
        """Actualiza la lista y tarjetas de estado de los clientes."""
        for widget in self.clients_scroll.winfo_children():
            widget.destroy()

        clients = AIConnectionService.get_clients_metadata()

        for c in clients:
            card = ctk.CTkFrame(
                self.clients_scroll,
                fg_color=Theme.BG_CARD_SUBTLE,
                corner_radius=Theme.SPACING_SM,
                border_width=1,
                border_color=Theme.BORDER_DEFAULT
            )
            card.pack(fill="x", pady=(0, Theme.SPACING_SM), padx=Theme.SPACING_XS)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=Theme.SPACING_MD, pady=Theme.SPACING_MD)

            # Icono y Nombre
            icon_lbl = ctk.CTkLabel(row, text=c["icon"], font=ctk.CTkFont(size=20))
            icon_lbl.pack(side="left", padx=(0, Theme.SPACING_SM))

            name_box = ctk.CTkFrame(row, fg_color="transparent")
            name_box.pack(side="left", fill="both", expand=True)

            ctk.CTkLabel(
                name_box,
                text=c["name"],
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=Theme.TEXT_PRIMARY
            ).pack(anchor="w")

            status_text = "Archivo: " + os.path.basename(c["config_path"])
            ctk.CTkLabel(
                name_box,
                text=status_text,
                font=ctk.CTkFont(size=10),
                text_color=Theme.TEXT_MUTED
            ).pack(anchor="w")

            # Badge de Estado
            if c["is_connected"]:
                badge = ctk.CTkLabel(
                    row,
                    text="✅ Conectado",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=Theme.SUCCESS
                )
                badge.pack(side="right")
            elif c["is_installed"]:
                btn = ctk.CTkButton(
                    row,
                    text="Conectar",
                    width=80,
                    height=28,
                    corner_radius=6,
                    fg_color=Theme.INFO,
                    hover_color=Theme.INFO_HOVER,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    command=lambda cid=c["id"]: self._connect_single(cid)
                )
                btn.pack(side="right")
            else:
                btn = ctk.CTkButton(
                    row,
                    text="Habilitar",
                    width=80,
                    height=28,
                    corner_radius=6,
                    fg_color="transparent",
                    border_width=1,
                    border_color=Theme.BORDER_DEFAULT,
                    text_color=Theme.TEXT_MUTED,
                    font=ctk.CTkFont(size=11),
                    command=lambda cid=c["id"]: self._connect_single(cid)
                )
                btn.pack(side="right")
