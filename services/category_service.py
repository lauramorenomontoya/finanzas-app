"""
Servicio Especializado para Consolidación y Normalización de Categorías.
Permite depurar categorías duplicadas o redundantes generadas tras importaciones de Notion
y actualizar en cascada todas las transacciones históricas y gastos fijos.
"""

from typing import Dict, Any, List, Tuple, Optional


class CategoryService:
    # Mapeo canónico de normalización de gastos en COP
    EXPENSE_COP_MAPPING = {
        # Restaurantes / Salidas
        "resto/tienda": "Restaurantes / Salidas",
        "resto tienda": "Restaurantes / Salidas",
        "ocio y restaurantes": "Restaurantes / Salidas",
        "brunch gardenia": "Restaurantes / Salidas",
        "restaurantes / salidas": "Restaurantes / Salidas",
        "restaurantes & cafés": "Restaurantes / Salidas",
        
        # Salud & Cuidado Personal
        "cuidado": "Salud & Cuidado Personal",
        "peluquería": "Salud & Cuidado Personal",
        "peluqueria": "Salud & Cuidado Personal",
        "salud y cuidado personal": "Salud & Cuidado Personal",
        "salud & cuidado personal": "Salud & Cuidado Personal",
        "cuidado personal": "Salud & Cuidado Personal",
        
        # Mercado & Supermercado
        "mercado": "Mercado & Supermercado",
        "alimentación / mercado": "Mercado & Supermercado",
        "alimentacion / mercado": "Mercado & Supermercado",
        "mercado & supermercado": "Mercado & Supermercado",
        "supermercado": "Mercado & Supermercado",
        
        # Hogar & Servicios
        "hogar": "Hogar & Servicios",
        "arriendo / hipoteca": "Hogar & Servicios",
        "servicios públicos (luz, agua, gas)": "Hogar & Servicios",
        "servicios publicos (luz, agua, gas)": "Hogar & Servicios",
        "hogar & servicios": "Hogar & Servicios",
        
        # Suscripciones & Apps
        "suscripciones": "Suscripciones & Apps",
        "suscripciones / internet": "Suscripciones & Apps",
        "suscripciones & apps": "Suscripciones & Apps",
        
        # Transporte
        "moto": "Moto & Mantenimiento",
        "moto & mantenimiento": "Moto & Mantenimiento",
        "taxi": "Taxi & Apps",
        "taxi & apps": "Taxi & Apps",
        "transporte público": "Transporte Público",
        "transporte publico": "Transporte Público",
        "transporte / gasolina": "Moto & Mantenimiento",
        
        # Entretenimiento & Ocio
        "entretenimiento": "Entretenimiento & Ocio",
        "entretenimiento & ocio": "Entretenimiento & Ocio",
        
        # Moda & Vestuario
        "moda": "Moda & Vestuario",
        "moda & vestuario": "Moda & Vestuario",
        
        # Regalos & Detalles
        "regalo": "Regalos & Detalles",
        "regalos & detalles": "Regalos & Detalles",
        
        # Otros Gastos
        "otros": "Otros Gastos",
        "otros gastos": "Otros Gastos",
        "otros gastos cop": "Otros Gastos",
        
        # Educación
        "educación": "Educación & Cursos",
        "educacion": "Educación & Cursos",
        "educación / cursos": "Educación & Cursos",
        "educacion / cursos": "Educación & Cursos",
        "educación & cursos": "Educación & Cursos",
        
        # Imprevistos
        "imprevistos / emergencias": "Imprevistos & Emergencias",
        "imprevistos & emergencias": "Imprevistos & Emergencias",
    }

    # Mapeo canónico de normalización de ingresos en COP
    INCOME_COP_MAPPING = {
        "nómina": "Nómina / Salario",
        "nomina": "Nómina / Salario",
        "nómina / salario": "Nómina / Salario",
        
        "negocios personales": "Negocios Personales",
        "negocios personales • bancolombia": "Negocios Personales",
        
        "transferencias": "Transferencias & Reembolsos",
        "transferencias & reembolsos": "Transferencias & Reembolsos",
        
        "honorarios / freelance cop": "Honorarios / Freelance COP",
        "clientes locales cop": "Honorarios / Freelance COP",
        "honorarios / proyectos cop": "Honorarios / Freelance COP",
        "honorarios / consultoría": "Honorarios / Freelance COP",
        "honorarios / consultoria": "Honorarios / Freelance COP",
        "consultoría profesional cop": "Honorarios / Freelance COP",
        "consultoria profesional cop": "Honorarios / Freelance COP",
        "invisible work (iw)": "Honorarios / Freelance COP",
        "proyectos freelance cop": "Honorarios / Freelance COP",
        
        "rendimientos": "Rendimientos & Ahorros COP",
        "rendimientos & ahorros cop": "Rendimientos & Ahorros COP",
        
        "otros ingresos cop": "Otros Ingresos COP",
    }

    # Mapeo canónico de ingresos en USD
    INCOME_USD_MAPPING = {
        "clientes internacionales usd": "Clientes Internacionales USD",
        "sea island creative (sic)": "Sea Island Creative (SIC)",
        "arc (sea island creative (sic))": "Sea Island Creative (SIC)",
        "arq (sea island creative (sic))": "Sea Island Creative (SIC)",
        "wenia (clientes internacionales usd)": "Clientes Internacionales USD",
        "consultoría / freelance usd": "Freelance & Consultoría USD",
        "consultoria / freelance usd": "Freelance & Consultoría USD",
        "freelance usd": "Freelance & Consultoría USD",
        "freelance & consultoría usd": "Freelance & Consultoría USD",
        "rendimientos usd": "Rendimientos USD",
        "otros ingresos usd": "Otros Ingresos USD",
        "arq": "ARQ",
        "arc": "ARQ",
    }


    # Mapeo canónico de egresos directos en USD
    EXPENSE_USD_MAPPING = {
        "software / ia (chatgpt, claude)": "Software / IA (ChatGPT, Claude)",
        "hosting / servidores (aws, vercel)": "Hosting / Servidores (AWS, Vercel)",
        "suscripciones usd": "Suscripciones USD",
        "educación / cursos usd": "Educación / Cursos USD",
        "educacion / cursos usd": "Educación / Cursos USD",
        "otros gastos usd": "Otros Gastos USD",
    }

    # Definición canónica completa de categorías
    CANONICAL_CATEGORIES = [
        # EXPENSE_COP (14)
        ("Restaurantes / Salidas", "EXPENSE_COP", "🍽️", "#f59e0b", 1),
        ("Salud & Cuidado Personal", "EXPENSE_COP", "💊", "#06b6d4", 1),
        ("Moto & Mantenimiento", "EXPENSE_COP", "🛵", "#f97316", 1),
        ("Taxi & Apps", "EXPENSE_COP", "🚕", "#f59e0b", 1),
        ("Hogar & Servicios", "EXPENSE_COP", "🏠", "#f43f5e", 1),
        ("Suscripciones & Apps", "EXPENSE_COP", "📱", "#8b5cf6", 1),
        ("Entretenimiento & Ocio", "EXPENSE_COP", "🎟️", "#6366f1", 1),
        ("Mercado & Supermercado", "EXPENSE_COP", "🛒", "#fb7185", 1),
        ("Regalos & Detalles", "EXPENSE_COP", "🎁", "#ec4899", 1),
        ("Transporte Público", "EXPENSE_COP", "🚌", "#38bdf8", 1),
        ("Moda & Vestuario", "EXPENSE_COP", "👗", "#a855f7", 1),
        ("Educación & Cursos", "EXPENSE_COP", "📚", "#6366f1", 1),
        ("Imprevistos & Emergencias", "EXPENSE_COP", "⚠️", "#d97706", 1),
        ("Otros Gastos", "EXPENSE_COP", "📦", "#94a3b8", 1),

        # INCOME_COP (6)
        ("Nómina / Salario", "INCOME_COP", "👔", "#10b981", 1),
        ("Negocios Personales", "INCOME_COP", "💼", "#38bdf8", 1),
        ("Honorarios / Freelance COP", "INCOME_COP", "💻", "#059669", 1),
        ("Transferencias & Reembolsos", "INCOME_COP", "💳", "#059669", 1),
        ("Rendimientos & Ahorros COP", "INCOME_COP", "📈", "#34d399", 1),
        ("Otros Ingresos COP", "INCOME_COP", "💰", "#6ee7b7", 1),

        # INCOME_USD (5)
        ("Clientes Internacionales USD", "INCOME_USD", "💼", "#38bdf8", 1),
        ("Sea Island Creative (SIC)", "INCOME_USD", "💼", "#38bdf8", 1),
        ("Freelance & Consultoría USD", "INCOME_USD", "🌐", "#0284c7", 1),
        ("Rendimientos USD", "INCOME_USD", "📈", "#60a5fa", 1),
        ("Otros Ingresos USD", "INCOME_USD", "💵", "#38bdf8", 1),

        # EXPENSE_USD (5)
        ("Software / IA (ChatGPT, Claude)", "EXPENSE_USD", "🤖", "#8b5cf6", 1),
        ("Hosting / Servidores (AWS, Vercel)", "EXPENSE_USD", "☁️", "#06b6d4", 1),
        ("Suscripciones USD", "EXPENSE_USD", "💳", "#ec4899", 1),
        ("Educación / Cursos USD", "EXPENSE_USD", "📚", "#f59e0b", 1),
        ("Otros Gastos USD", "EXPENSE_USD", "💸", "#f43f5e", 1),
    ]

    @classmethod
    def normalize_category_name(cls, raw_name: str, cat_type: str = "EXPENSE_COP") -> str:
        """Normaliza cualquier nombre crudo de categoría a su equivalente canónico consolidado."""
        if not raw_name:
            return "Otros Gastos" if "EXPENSE" in cat_type else "Otros Ingresos COP"

        clean = raw_name.strip()
        key = clean.lower()

        if cat_type == "EXPENSE_COP":
            return cls.EXPENSE_COP_MAPPING.get(key, clean)
        elif cat_type == "INCOME_COP":
            return cls.INCOME_COP_MAPPING.get(key, clean)
        elif cat_type == "INCOME_USD":
            return cls.INCOME_USD_MAPPING.get(key, clean)
        elif cat_type == "EXPENSE_USD":
            return cls.EXPENSE_USD_MAPPING.get(key, clean)
        return clean

    @classmethod
    def consolidate_database_categories(cls, db_manager) -> Dict[str, Any]:
        """
        Ejecuta la consolidación atómica y segura de categorías en la base de datos:
        1. Crea backup preventivo de seguridad.
        2. Remapea las categorías en 'cop_transactions', 'usd_transactions' y 'recurring_expenses'.
        3. Reconstruye la tabla 'categories' con el catálogo limpio canónico.
        """
        backup_path = db_manager.create_backup()

        stats = {
            "backup_created": backup_path,
            "cop_transactions_updated": 0,
            "usd_transactions_updated": 0,
            "recurring_updated": 0,
            "categories_total": 0,
            "success": False
        }

        with db_manager._write_lock:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # 1. Actualizar cop_transactions (Gastos)
                for old_key, new_val in cls.EXPENSE_COP_MAPPING.items():
                    cursor.execute("""
                        UPDATE cop_transactions
                        SET category = ?
                        WHERE type = 'EXPENSE' AND LOWER(TRIM(category)) = ? AND category != ?;
                    """, (new_val, old_key, new_val))
                    stats["cop_transactions_updated"] += cursor.rowcount

                # 2. Actualizar cop_transactions (Ingresos)
                for old_key, new_val in cls.INCOME_COP_MAPPING.items():
                    cursor.execute("""
                        UPDATE cop_transactions
                        SET category = ?
                        WHERE type IN ('MANUAL_INCOME', 'TRANSFER_IN') AND LOWER(TRIM(category)) = ? AND category != ?;
                    """, (new_val, old_key, new_val))
                    stats["cop_transactions_updated"] += cursor.rowcount

                # 3. Actualizar recurring_expenses (Gastos Fijos)
                for old_key, new_val in cls.EXPENSE_COP_MAPPING.items():
                    cursor.execute("""
                        UPDATE recurring_expenses
                        SET category = ?
                        WHERE LOWER(TRIM(category)) = ? AND category != ?;
                    """, (new_val, old_key, new_val))
                    stats["recurring_updated"] += cursor.rowcount

                # 4. Actualizar usd_transactions (Plataformas / Categorías)
                for old_key, new_val in cls.INCOME_USD_MAPPING.items():
                    cursor.execute("""
                        UPDATE usd_transactions
                        SET platform = ?
                        WHERE type = 'DEPOSIT' AND LOWER(TRIM(platform)) = ? AND platform != ?;
                    """, (new_val, old_key, new_val))
                    stats["usd_transactions_updated"] += cursor.rowcount

                for old_key, new_val in cls.EXPENSE_USD_MAPPING.items():
                    cursor.execute("""
                        UPDATE usd_transactions
                        SET platform = ?
                        WHERE type = 'EXPENSE' AND LOWER(TRIM(platform)) = ? AND platform != ?;
                    """, (new_val, old_key, new_val))
                    stats["usd_transactions_updated"] += cursor.rowcount

                # 5. Reconstruir la tabla de categorías
                # Obtener categorías personalizadas de usuario que no estén en los mappings
                cursor.execute("SELECT name, type, icon, color, is_system FROM categories;")
                existing_rows = cursor.fetchall()

                canonical_names = {c[0].lower(): c for c in cls.CANONICAL_CATEGORIES}

                # Limpiar tabla de categorías
                cursor.execute("DELETE FROM categories;")

                # Insertar categorías canónicas
                cursor.executemany("""
                    INSERT INTO categories (name, type, icon, color, is_system)
                    VALUES (?, ?, ?, ?, ?);
                """, cls.CANONICAL_CATEGORIES)

                # Preservar cualquier categoría personalizada no-sistema creada por el usuario
                # si no fue parte de la consolidación y está en uso
                for r in existing_rows:
                    r_name = r["name"].strip()
                    r_type = r["type"]
                    if r_name.lower() not in canonical_names and r["is_system"] == 0:
                        # Verificar si tiene transacciones
                        cursor.execute("SELECT COUNT(*) as c FROM cop_transactions WHERE category = ?;", (r_name,))
                        c1 = cursor.fetchone()["c"]
                        cursor.execute("SELECT COUNT(*) as c FROM usd_transactions WHERE platform = ?;", (r_name,))
                        c2 = cursor.fetchone()["c"]
                        if c1 > 0 or c2 > 0:
                            cursor.execute("""
                                INSERT OR IGNORE INTO categories (name, type, icon, color, is_system)
                                VALUES (?, ?, ?, ?, 0);
                            """, (r_name, r_type, r["icon"], r["color"]))

                conn.commit()

                # Conteo final de categorías
                cursor.execute("SELECT COUNT(*) as c FROM categories;")
                stats["categories_total"] = cursor.fetchone()["c"]
                stats["success"] = True

        return stats
