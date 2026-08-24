"""
Mixin para Gestión Dinámica de Categorías CRUD.
"""

from typing import List, Dict, Any, Optional, Tuple


class CategoryMixin:
    def get_categories(self, cat_type: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if cat_type:
                cursor.execute("""
                    SELECT id, name, type, icon, color, is_system, created_at
                    FROM categories
                    WHERE type = ?
                    ORDER BY name ASC;
                """, (cat_type,))
            else:
                cursor.execute("""
                    SELECT id, name, type, icon, color, is_system, created_at
                    FROM categories
                    ORDER BY type ASC, name ASC;
                """)
            return [dict(row) for row in cursor.fetchall()]

    def get_category_by_id(self, cat_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, type, icon, color, is_system, created_at FROM categories WHERE id = ?;", (cat_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_category(self, name: str, cat_type: str, icon: str = "🏷️", color: str = "#38bdf8") -> Optional[int]:
        name = name.strip()
        if not name:
            return None
        if cat_type not in ("INCOME_USD", "INCOME_COP", "EXPENSE_COP", "EXPENSE_USD"):
            return None

        with self._write_lock:
            with self.get_connection() as conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO categories (name, type, icon, color, is_system)
                        VALUES (?, ?, ?, ?, 0);
                    """, (name, cat_type, icon, color))
                    conn.commit()
                    return cursor.lastrowid
                except Exception:
                    return None

    def update_category(self, cat_id: int, name: str, icon: str, color: str) -> bool:
        name = name.strip()
        if not name:
            return False

        with self._write_lock:
            with self.get_connection() as conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT name, type FROM categories WHERE id = ?;", (cat_id,))
                    cat = cursor.fetchone()
                    if not cat:
                        return False

                    old_name = cat["name"]
                    c_type = cat["type"]

                    cursor.execute("""
                        UPDATE categories
                        SET name = ?, icon = ?, color = ?
                        WHERE id = ?;
                    """, (name, icon, color, cat_id))

                    # Si el nombre cambió, sincronizar en cascada en tablas de transacciones
                    if old_name != name:
                        if c_type == "INCOME_USD":
                            cursor.execute("UPDATE usd_transactions SET platform = ? WHERE platform = ? AND type = 'DEPOSIT';", (name, old_name))
                        elif c_type == "EXPENSE_USD":
                            cursor.execute("UPDATE usd_transactions SET platform = ? WHERE platform = ? AND type = 'EXPENSE';", (name, old_name))
                        elif c_type == "INCOME_COP":
                            cursor.execute("UPDATE cop_transactions SET category = ? WHERE category = ? AND type = 'MANUAL_INCOME';", (name, old_name))
                        elif c_type == "EXPENSE_COP":
                            cursor.execute("UPDATE cop_transactions SET category = ? WHERE category = ? AND type = 'EXPENSE';", (name, old_name))
                            cursor.execute("UPDATE recurring_expenses SET category = ? WHERE category = ?;", (name, old_name))

                    conn.commit()
                    return True
                except Exception:
                    return False

    def delete_category(self, cat_id: int) -> Tuple[bool, str]:
        with self._write_lock:
            with self.get_connection() as conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT name, type, is_system FROM categories WHERE id = ?;", (cat_id,))
                    cat = cursor.fetchone()
                    if not cat:
                        return False, "La categoría no existe."

                    cat_name = cat["name"]
                    c_type = cat["type"]

                    # Comprobar si existen transacciones usando esta categoría
                    usage_count = 0
                    if c_type in ("INCOME_USD", "EXPENSE_USD"):
                        cursor.execute("SELECT COUNT(*) as count FROM usd_transactions WHERE platform = ?;", (cat_name,))
                        usage_count = cursor.fetchone()["count"]
                    else:
                        cursor.execute("SELECT COUNT(*) as count FROM cop_transactions WHERE category = ?;", (cat_name,))
                        usage_count = cursor.fetchone()["count"]

                    if usage_count > 0:
                        return False, f"No se puede eliminar '{cat_name}' porque tiene {usage_count} transacciones asociadas en el historial."

                    cursor.execute("DELETE FROM categories WHERE id = ?;", (cat_id,))
                    conn.commit()
                    return True, f"Categoría '{cat_name}' eliminada correctamente."
                except Exception as e:
                    return False, f"Error al eliminar: {str(e)}"
