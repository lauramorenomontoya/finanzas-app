"""
Mixin para Gestión de Tags / Etiquetas Personalizadas en Transacciones.
"""

from typing import List, Dict, Any, Optional


class TagsMixin:
    def get_tags(self) -> List[Dict[str, Any]]:
        """Obtiene todas las etiquetas ordenadas alfabéticamente."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, color, created_at FROM tags ORDER BY name ASC;")
            return [dict(row) for row in cursor.fetchall()]

    def add_tag(self, name: str, color: str = "#38bdf8") -> Optional[int]:
        """Crea una nueva etiqueta."""
        name = name.strip()
        if not name:
            return None

        with self._write_lock:
            with self.get_connection() as conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO tags (name, color)
                        VALUES (?, ?);
                    """, (name, color))
                    conn.commit()
                    return cursor.lastrowid
                except Exception:
                    return None

    def delete_tag(self, tag_id: int) -> bool:
        """Elimina una etiqueta y sus asociaciones en cascada."""
        with self._write_lock:
            with self.get_connection() as conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM tags WHERE id = ?;", (tag_id,))
                    conn.commit()
                    return cursor.rowcount > 0
                except Exception:
                    return False

    def get_tags_for_record(self, source_table: str, record_id: int) -> List[Dict[str, Any]]:
        """Obtiene las etiquetas asignadas a un registro específico."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.id, t.name, t.color
                FROM tags t
                JOIN transaction_tags tt ON t.id = tt.tag_id
                WHERE tt.source_table = ? AND tt.record_id = ?
                ORDER BY t.name ASC;
            """, (source_table, record_id))
            return [dict(row) for row in cursor.fetchall()]

    def set_tags_for_record(self, source_table: str, record_id: int, tag_ids: List[int]) -> bool:
        """Asigna una lista de etiquetas a un registro reemplazando las anteriores."""
        with self._write_lock:
            with self.get_connection() as conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM transaction_tags WHERE source_table = ? AND record_id = ?;", (source_table, record_id))
                    for t_id in tag_ids:
                        cursor.execute("""
                            INSERT OR IGNORE INTO transaction_tags (tag_id, source_table, record_id)
                            VALUES (?, ?, ?);
                        """, (t_id, source_table, record_id))
                    conn.commit()
                    return True
                except Exception:
                    return False

    def get_all_tags_with_counts(self) -> List[Dict[str, Any]]:
        """Obtiene las etiquetas con la cantidad de transacciones asociadas."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.id, t.name, t.color, COUNT(tt.tag_id) AS count
                FROM tags t
                LEFT JOIN transaction_tags tt ON t.id = tt.tag_id
                GROUP BY t.id
                ORDER BY count DESC, t.name ASC;
            """)
            return [dict(row) for row in cursor.fetchall()]
