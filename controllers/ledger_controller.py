from typing import List, Dict, Any, Tuple, Optional

class LedgerController:
    """
    Controlador para el Libro Diario (MVC).
    Maneja el registro consolidado de transacciones y su eliminación segura.
    """
    def __init__(self, db_manager):
        self.db = db_manager

    def get_tags(self) -> List[Dict[str, Any]]:
        if hasattr(self.db, "get_tags"):
            return self.db.get_tags()
        return []

    def get_unified_ledger(self, limit: int = 500, module_filter: Optional[str] = None,
                           date_from: Optional[str] = None, date_to: Optional[str] = None,
                           search_query: Optional[str] = None, tag_id: Optional[int] = None) -> List[Dict[str, Any]]:
        return self.db.get_unified_ledger(
            limit=limit,
            module_filter=module_filter,
            date_from=date_from,
            date_to=date_to,
            search_query=search_query,
            tag_id=tag_id
        )

    def delete_transaction(self, table_name: str, record_id: int, force: bool = False) -> Tuple[bool, str, Any]:
        """
        Delega la eliminación a la tabla correspondiente.
        Devuelve (success, mensaje, warning_data).
        """
        if table_name == "usd_transactions":
            return self.db.delete_usd_transaction(record_id, force=force)
        elif table_name == "cop_transactions":
            return self.db.delete_cop_transaction(record_id, force=force)
        elif table_name == "account_transactions":
            return self.db.delete_account_transaction(record_id, force=force)
        elif table_name == "conversions":
            return self.db.delete_conversion(record_id, force=force)
        else:
            return False, "Tipo de tabla desconocido.", None

    def fetch_full_record(self, table_name: str, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene el registro completo con prevención de inyecciones (lista blanca de tablas).
        """
        allowed_tables = {"usd_transactions", "cop_transactions", "account_transactions", "conversions"}
        if table_name not in allowed_tables:
            return None

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?;", (record_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
