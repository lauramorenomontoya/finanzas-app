"""
Controlador de Ingresos (MVC):
Separa la lógica de negocio, validaciones y acceso a datos de la interfaz de usuario IncomesView.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


class IncomeController:
    def __init__(self, db_manager):
        self.db = db_manager

    def add_income(
        self,
        amount_str: str,
        is_usd: bool,
        platform: str,
        category: str,
        date_str: str,
        notes: str,
        selected_tag_ids: Optional[List[int]] = None
    ) -> Tuple[bool, str]:
        """
        Valida los datos de entrada y registra un ingreso en USD o COP.
        """
        if not amount_str or not amount_str.strip():
            return False, "El monto no puede estar vacío."

        # Limpieza y formateo numérico
        raw = amount_str.strip()
        if not is_usd:
            # En COP se eliminan puntos de miles y se reemplaza coma por punto decimal si la hay
            clean_str = raw.replace(".", "").replace(",", ".")
        else:
            clean_str = raw.replace(",", ".")

        try:
            amount = float(clean_str)
            if amount <= 0:
                return False, "Por favor ingresa un monto válido mayor a 0."
        except ValueError:
            return False, "Por favor ingresa un monto numérico válido."

        # Validación de fecha
        try:
            datetime.strptime(date_str.strip(), "%Y-%m-%d")
        except ValueError:
            return False, "Fecha inválida. Usa el formato YYYY-MM-DD o el calendario interactivo."

        # Inserción y persistencia
        try:
            clean_category = category.strip()
            clean_platform = platform.strip()
            clean_notes = notes.strip()

            if is_usd:
                desc_platform = f"{clean_platform} ({clean_category})" if clean_category else clean_platform
                tx_id = self.db.add_usd_deposit(date_str.strip(), desc_platform, amount, clean_notes)
                if selected_tag_ids and tx_id:
                    self.db.set_tags_for_record("usd_transactions", tx_id, selected_tag_ids)
                return True, f"¡Ingreso de +${amount:,.2f} USD guardado en {clean_platform}!"
            else:
                desc_cat = f"{clean_category} • {clean_platform}" if clean_platform else clean_category
                tx_id = self.db.add_cop_income(date_str.strip(), desc_cat, amount, clean_notes)
                if selected_tag_ids and tx_id:
                    self.db.set_tags_for_record("cop_transactions", tx_id, selected_tag_ids)
                return True, f"¡Ingreso de +${amount:,.0f} COP registrado con éxito!"
        except Exception as e:
            return False, f"Error al registrar ingreso: {str(e)}"

    def get_balances(self) -> Dict[str, float]:
        """Devuelve los saldos actuales en USD y COP."""
        return {
            "usd": self.db.get_usd_balance(),
            "cop": self.db.get_cop_balance()
        }

    def get_categories(self, is_usd_or_type) -> List[str]:
        """Obtiene la lista de nombres de categorías según la moneda."""
        if isinstance(is_usd_or_type, bool):
            cat_type = "INCOME_USD" if is_usd_or_type else "INCOME_COP"
        else:
            cat_type = "INCOME_USD" if "USD" in str(is_usd_or_type) else "INCOME_COP"
        return [c["name"] for c in self.db.get_categories(cat_type)]

    def get_incomes(self, limit: int = 50, currency_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene la lista de ingresos aplicando filtros."""
        return self.db.get_all_incomes(limit=limit, currency_filter=currency_filter)

    def delete_income(self, record_id: int, source_table_or_currency: str, force: bool = False) -> Tuple[bool, str, Any]:
        """Elimina una transacción de ingreso con verificación de balance negativo."""
        if source_table_or_currency in ("usd_transactions", "USD"):
            return self.db.delete_usd_transaction(record_id, force=force)
        else:
            return self.db.delete_cop_transaction(record_id, force=force)
