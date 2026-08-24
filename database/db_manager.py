"""
Módulo Central de Gestión de Base de Datos SQLite para Control Financiero.
Combina arquitectura modular de Mixins con soporte transaccional, Write-Ahead Logging (WAL)
y control de concurrencia thread-safe.
"""

import sqlite3
import os
import shutil
import threading
from datetime import datetime
from typing import Optional

from database.managers import (
    IncomeMixin,
    ExpenseMixin,
    BalanceMixin,
    ConversionMixin,
    AccountMixin,
    CategoryMixin,
    RecurringMixin,
    AnalyticsMixin,
    LedgerMixin,
    CSVMixin,
    TagsMixin,
)


class DatabaseManager(
    IncomeMixin,
    ExpenseMixin,
    BalanceMixin,
    ConversionMixin,
    AccountMixin,
    CategoryMixin,
    RecurringMixin,
    AnalyticsMixin,
    LedgerMixin,
    CSVMixin,
    TagsMixin,
):
    def __init__(self, db_path: Optional[str] = None):
        """Inicializa la conexión, lock de escritura thread-safe y esquema de datos."""
        self._write_lock = threading.RLock()

        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_path = os.path.join(base_dir, "finanzas.db")
        else:
            self.db_path = db_path

        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Obtiene una conexión configurada con WAL mode, soporte foráneo y filas tipo dict."""
        conn = sqlite3.connect(self.db_path, timeout=15.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def init_db(self) -> None:
        """Crea las tablas necesarias y realiza migraciones automáticas."""
        with self._write_lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 1. Tabla de Movimientos en USD
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS usd_transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        platform TEXT NOT NULL,
                        type TEXT NOT NULL CHECK(type IN ('DEPOSIT', 'TRANSFER_OUT', 'TRANSFER_TO_INVESTMENT', 'TRANSFER_FROM_INVESTMENT', 'EXPENSE')),
                        amount REAL NOT NULL CHECK(amount > 0),
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # 2. Tabla de Movimientos en COP
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cop_transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        category TEXT NOT NULL,
                        type TEXT NOT NULL CHECK(type IN ('TRANSFER_IN', 'EXPENSE', 'MANUAL_INCOME', 'CC_PAYMENT', 'TRANSFER_TO_INVESTMENT', 'TRANSFER_FROM_INVESTMENT')),
                        amount REAL NOT NULL CHECK(amount > 0),
                        is_fixed INTEGER DEFAULT 0 CHECK(is_fixed IN (0, 1)),
                        payment_method TEXT DEFAULT 'DEBIT' CHECK(payment_method IN ('DEBIT', 'CREDIT_CARD', 'CASH')),
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # Migración: Verificar si payment_method existe en cop_transactions
                cursor.execute("PRAGMA table_info(cop_transactions);")
                columns = [row["name"] for row in cursor.fetchall()]
                if "payment_method" not in columns:
                    cursor.execute("ALTER TABLE cop_transactions ADD COLUMN payment_method TEXT DEFAULT 'DEBIT';")

                # 3. Tabla de Conversiones (Puente USD -> COP)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conversions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        usd_amount REAL NOT NULL CHECK(usd_amount > 0),
                        exchange_rate REAL NOT NULL CHECK(exchange_rate > 0),
                        cop_amount REAL NOT NULL CHECK(cop_amount > 0),
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # 4. Tabla de Categorías
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        type TEXT NOT NULL CHECK(type IN ('INCOME_USD', 'INCOME_COP', 'EXPENSE_COP', 'EXPENSE_USD')),
                        icon TEXT DEFAULT '🏷️',
                        color TEXT DEFAULT '#38bdf8',
                        is_system INTEGER DEFAULT 0 CHECK(is_system IN (0, 1)),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # 5. Tabla de Plantilla de Gastos Fijos (Multimoneda)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS recurring_expenses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT NOT NULL,
                        description TEXT NOT NULL,
                        amount REAL NOT NULL CHECK(amount > 0),
                        currency TEXT DEFAULT 'COP' CHECK(currency IN ('COP', 'USD')),
                        due_day INTEGER DEFAULT 1,
                        is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # Migración: Verificar si currency existe en recurring_expenses
                cursor.execute("PRAGMA table_info(recurring_expenses);")
                rec_cols = [row["name"] for row in cursor.fetchall()]
                if "currency" not in rec_cols:
                    cursor.execute("ALTER TABLE recurring_expenses ADD COLUMN currency TEXT DEFAULT 'COP';")

                # 6. Tabla de Cuentas y Fiducias
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        currency TEXT NOT NULL CHECK(currency IN ('COP', 'USD')),
                        account_type TEXT NOT NULL CHECK(account_type IN ('INVERSION_FIDUCIA', 'AHORRO', 'BILLETERA', 'OPERATIVA')),
                        institution TEXT,
                        initial_balance REAL DEFAULT 0.0 CHECK(initial_balance >= 0),
                        color TEXT DEFAULT '#10b981',
                        icon TEXT DEFAULT '📈',
                        is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # 7. Tabla de Movimientos en Cuentas e Inversiones
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS account_transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                        date TEXT NOT NULL,
                        type TEXT NOT NULL CHECK(type IN ('DEPOSIT', 'WITHDRAWAL', 'YIELD', 'TRANSFER_IN', 'TRANSFER_OUT')),
                        amount REAL NOT NULL CHECK(amount > 0),
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # 8. Tablas de Tags / Etiquetas (NUEVO Fase 4)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tags (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        color TEXT DEFAULT '#38bdf8',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS transaction_tags (
                        tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
                        source_table TEXT NOT NULL,
                        record_id INTEGER NOT NULL,
                        PRIMARY KEY (tag_id, source_table, record_id)
                    );
                """)

                # Pre-poblar categorías limpias por defecto si está vacía
                cursor.execute("SELECT COUNT(*) as count FROM categories;")
                if cursor.fetchone()["count"] == 0:
                    default_categories = [
                        ("Clientes Internacionales USD", "INCOME_USD", "💼", "#38bdf8", 1),
                        ("Consultoría / Freelance USD", "INCOME_USD", "🌐", "#0284c7", 1),
                        ("Rendimientos USD", "INCOME_USD", "📈", "#60a5fa", 1),
                        ("Otros Ingresos USD", "INCOME_USD", "💵", "#38bdf8", 1),
                        ("Software / IA (ChatGPT, Claude)", "EXPENSE_USD", "🤖", "#8b5cf6", 1),
                        ("Hosting / Servidores (AWS, Vercel)", "EXPENSE_USD", "☁️", "#06b6d4", 1),
                        ("Suscripciones USD", "EXPENSE_USD", "💳", "#ec4899", 1),
                        ("Educación / Cursos USD", "EXPENSE_USD", "📚", "#f59e0b", 1),
                        ("Otros Gastos USD", "EXPENSE_USD", "💸", "#f43f5e", 1),
                        ("Clientes Locales COP", "INCOME_COP", "🚀", "#10b981", 1),
                        ("Honorarios / Proyectos COP", "INCOME_COP", "💻", "#059669", 1),
                        ("Consultoría Profesional COP", "INCOME_COP", "📑", "#34d399", 1),
                        ("Otros Ingresos COP", "INCOME_COP", "💰", "#6ee7b7", 1),
                        ("Arriendo / Hipoteca", "EXPENSE_COP", "🏠", "#f43f5e", 1),
                        ("Servicios Públicos (Luz, Agua, Gas)", "EXPENSE_COP", "💡", "#e11d48", 1),
                        ("Alimentación / Mercado", "EXPENSE_COP", "🛒", "#fb7185", 1),
                        ("Transporte / Gasolina", "EXPENSE_COP", "🚗", "#f97316", 1),
                        ("Ocio y Restaurantes", "EXPENSE_COP", "🍽️", "#f59e0b", 1),
                        ("Suscripciones / Internet", "EXPENSE_COP", "📱", "#8b5cf6", 1),
                        ("Salud y Cuidado Personal", "EXPENSE_COP", "💊", "#06b6d4", 1),
                        ("Educación / Cursos", "EXPENSE_COP", "📚", "#6366f1", 1),
                        ("Imprevistos / Emergencias", "EXPENSE_COP", "⚠️", "#d97706", 1),
                        ("Otros Gastos COP", "EXPENSE_COP", "📦", "#94a3b8", 1),
                    ]
                    cursor.executemany("""
                        INSERT OR IGNORE INTO categories (name, type, icon, color, is_system)
                        VALUES (?, ?, ?, ?, ?);
                    """, default_categories)

                # Pre-poblar cuentas por defecto si no existen
                cursor.execute("SELECT COUNT(*) as count FROM accounts;")
                if cursor.fetchone()["count"] == 0:
                    default_accounts = [
                        ("Fiducuenta Bancolombia", "COP", "INVERSION_FIDUCIA", "Bancolombia", 0.0, "#10b981", "📈", 1),
                        ("Cajita Nu (13% E.A.)", "COP", "AHORRO", "Nu Colombia", 0.0, "#8b5cf6", "💜", 1),
                        ("Wenia Staking / Vault", "USD", "INVERSION_FIDUCIA", "Wenia", 0.0, "#38bdf8", "🏦", 1),
                        ("Interactive Brokers (Acciones/ETFs)", "USD", "INVERSION_FIDUCIA", "IBKR", 0.0, "#0284c7", "📊", 1),
                    ]
                    cursor.executemany("""
                        INSERT INTO accounts (name, currency, account_type, institution, initial_balance, color, icon, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """, default_accounts)

                # Pre-poblar plantilla de gastos fijos multimoneda si está vacía
                cursor.execute("SELECT COUNT(*) as count FROM recurring_expenses;")
                if cursor.fetchone()["count"] == 0:
                    default_recurring = [
                        ("Arriendo / Hipoteca", "Pago arriendo mensual", 1500000.0, "COP", 1),
                        ("Servicios Públicos (Luz, Agua, Gas)", "Servicios públicos del hogar", 300000.0, "COP", 5),
                        ("Software / IA (ChatGPT, Claude)", "Suscripción ChatGPT Plus", 20.0, "USD", 1),
                        ("Suscripciones / Internet", "Internet fibra óptica y telefonía", 120000.0, "COP", 10),
                        ("Alimentación / Mercado", "Mercado principal mensual", 800000.0, "COP", 1),
                    ]
                    cursor.executemany("""
                        INSERT INTO recurring_expenses (category, description, amount, currency, due_day, is_active)
                        VALUES (?, ?, ?, ?, ?, 1);
                    """, default_recurring)

                # Pre-poblar tags sugeridos si está vacía
                cursor.execute("SELECT COUNT(*) as count FROM tags;")
                if cursor.fetchone()["count"] == 0:
                    default_tags = [
                        ("💼 Proyecto", "#38bdf8"),
                        ("🌟 Prioritario", "#f59e0b"),
                        ("🧾 Facturable", "#10b981"),
                        ("🏠 Hogar", "#8b5cf6"),
                        ("✈️ Viajes", "#ec4899"),
                    ]
                    cursor.executemany("""
                        INSERT OR IGNORE INTO tags (name, color)
                        VALUES (?, ?);
                    """, default_tags)

                conn.commit()

    def create_backup(self) -> Optional[str]:
        """Crea un respaldo de seguridad del archivo SQLite en la carpeta backups/."""
        if not os.path.exists(self.db_path):
            return None

        base_dir = os.path.dirname(self.db_path)
        backup_dir = os.path.join(base_dir, "backups")
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"finanzas_backup_{timestamp}.db"
        backup_filepath = os.path.join(backup_dir, backup_filename)

        try:
            with self._write_lock:
                shutil.copy2(self.db_path, backup_filepath)

            # Mantener máximo los 15 backups más recientes
            backups = sorted(
                [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.startswith("finanzas_backup_")],
                key=os.path.getmtime
            )
            while len(backups) > 15:
                oldest = backups.pop(0)
                try:
                    os.remove(oldest)
                except OSError:
                    pass

            return backup_filepath
        except Exception:
            return None

    def get_last_backup_info(self) -> Optional[str]:
        """Obtiene la fecha del último backup realizado."""
        base_dir = os.path.dirname(self.db_path)
        backup_dir = os.path.join(base_dir, "backups")
        if not os.path.exists(backup_dir):
            return None

        backups = [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.startswith("finanzas_backup_")]
        if not backups:
            return None

        latest = max(backups, key=os.path.getmtime)
        mtime = datetime.fromtimestamp(os.path.getmtime(latest))
        return mtime.strftime("%d/%m/%Y %H:%M")
