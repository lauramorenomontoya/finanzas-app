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
    BudgetMixin,
    DebtMixin,
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
    BudgetMixin,
    DebtMixin,
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
        """Obtiene una conexión configurada con WAL mode, alto rendimiento en memoria y soporte foráneo."""
        conn = sqlite3.connect(self.db_path, timeout=15.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA cache_size = -64000;")
        conn.execute("PRAGMA temp_store = MEMORY;")
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
                        recurring_id INTEGER REFERENCES recurring_expenses(id) ON DELETE SET NULL,
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
                        recurring_id INTEGER REFERENCES recurring_expenses(id) ON DELETE SET NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # Ejecutar migraciones automáticas de esquema para tablas existentes
                self._run_schema_migrations(conn)

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

                # 11. Tabla de Deudas y Préstamos
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS debts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        creditor TEXT NOT NULL,
                        total_amount REAL NOT NULL CHECK(total_amount > 0),
                        currency TEXT DEFAULT 'COP' CHECK(currency IN ('COP', 'USD')),
                        start_date TEXT NOT NULL,
                        due_date TEXT,
                        notes TEXT,
                        status TEXT DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'PAID')),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # 12. Tabla de Abonos a Deudas
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS debt_payments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        debt_id INTEGER NOT NULL REFERENCES debts(id) ON DELETE CASCADE,
                        date TEXT NOT NULL,
                        amount REAL NOT NULL CHECK(amount > 0),
                        notes TEXT,
                        transaction_id INTEGER REFERENCES cop_transactions(id) ON DELETE SET NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                cursor.execute("CREATE INDEX IF NOT EXISTS idx_debts_status ON debts(status);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_debt_payments_debt_id ON debt_payments(debt_id);")

                # Migración: Verificar si recurring_id existe en cop_transactions y usd_transactions
                cursor.execute("PRAGMA table_info(cop_transactions);")
                cop_cols = [row["name"] for row in cursor.fetchall()]
                if "recurring_id" not in cop_cols:
                    cursor.execute("ALTER TABLE cop_transactions ADD COLUMN recurring_id INTEGER REFERENCES recurring_expenses(id) ON DELETE SET NULL;")

                cursor.execute("PRAGMA table_info(usd_transactions);")
                usd_cols = [row["name"] for row in cursor.fetchall()]
                if "recurring_id" not in usd_cols:
                    cursor.execute("ALTER TABLE usd_transactions ADD COLUMN recurring_id INTEGER REFERENCES recurring_expenses(id) ON DELETE SET NULL;")

                # Índices para acelerar consultas por fecha y tipo
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cop_date_type ON cop_transactions(date, type);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cop_cat ON cop_transactions(category);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cop_recurring ON cop_transactions(recurring_id);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_usd_date_type ON usd_transactions(date, type);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_usd_recurring ON usd_transactions(recurring_id);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_acc_date_type ON account_transactions(date, type);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_tags ON transaction_tags(source_table, record_id);")

                # Pre-poblar categorías limpias por defecto si está vacía
                cursor.execute("SELECT COUNT(*) as count FROM categories;")
                if cursor.fetchone()["count"] == 0:
                    from services.category_service import CategoryService
                    cursor.executemany("""
                        INSERT OR IGNORE INTO categories (name, type, icon, color, is_system)
                        VALUES (?, ?, ?, ?, ?);
                    """, CategoryService.CANONICAL_CATEGORIES)


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

        # Inicializar tablas de presupuesto y metas
        self._init_budget_tables()

    def _run_schema_migrations(self, conn: sqlite3.Connection) -> None:
        """Verifica y actualiza constraints CHECK en tablas SQLite existentes."""
        cursor = conn.cursor()

        # 1. Migración para usd_transactions
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='usd_transactions';")
        usd_row = cursor.fetchone()
        if usd_row and "TRANSFER_TO_INVESTMENT" not in (usd_row[0] or ""):
            cursor.execute("PRAGMA foreign_keys = OFF;")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usd_transactions_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('DEPOSIT', 'TRANSFER_OUT', 'TRANSFER_TO_INVESTMENT', 'TRANSFER_FROM_INVESTMENT', 'EXPENSE')),
                    amount REAL NOT NULL CHECK(amount > 0),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                INSERT INTO usd_transactions_new (id, date, platform, type, amount, notes, created_at)
                SELECT id, date, platform, type, amount, notes, created_at FROM usd_transactions;
            """)
            cursor.execute("DROP TABLE usd_transactions;")
            cursor.execute("ALTER TABLE usd_transactions_new RENAME TO usd_transactions;")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_usd_date_type ON usd_transactions(date, type);")
            cursor.execute("PRAGMA foreign_keys = ON;")

        # 2. Migración para cop_transactions
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='cop_transactions';")
        cop_row = cursor.fetchone()
        if cop_row and "TRANSFER_TO_INVESTMENT" not in (cop_row[0] or ""):
            cursor.execute("PRAGMA foreign_keys = OFF;")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cop_transactions_new (
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
            cursor.execute("PRAGMA table_info(cop_transactions);")
            cols = [r["name"] for r in cursor.fetchall()]
            if "payment_method" in cols:
                cursor.execute("""
                    INSERT INTO cop_transactions_new (id, date, category, type, amount, is_fixed, payment_method, notes, created_at)
                    SELECT id, date, category, type, amount, is_fixed, COALESCE(payment_method, 'DEBIT'), notes, created_at FROM cop_transactions;
                """)
            else:
                cursor.execute("""
                    INSERT INTO cop_transactions_new (id, date, category, type, amount, is_fixed, payment_method, notes, created_at)
                    SELECT id, date, category, type, amount, is_fixed, 'DEBIT', notes, created_at FROM cop_transactions;
                """)
            cursor.execute("DROP TABLE cop_transactions;")
            cursor.execute("ALTER TABLE cop_transactions_new RENAME TO cop_transactions;")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cop_date_type ON cop_transactions(date, type);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cop_cat ON cop_transactions(category);")
            cursor.execute("PRAGMA foreign_keys = ON;")

        # 3. Migración para categories
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='categories';")
        cat_row = cursor.fetchone()
        if cat_row and "EXPENSE_USD" not in (cat_row[0] or ""):
            cursor.execute("PRAGMA foreign_keys = OFF;")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    type TEXT NOT NULL CHECK(type IN ('INCOME_USD', 'INCOME_COP', 'EXPENSE_COP', 'EXPENSE_USD')),
                    icon TEXT DEFAULT '🏷️',
                    color TEXT DEFAULT '#38bdf8',
                    is_system INTEGER DEFAULT 0 CHECK(is_system IN (0, 1)),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                INSERT INTO categories_new (id, name, type, icon, color, is_system, created_at)
                SELECT id, name, type, icon, color, is_system, created_at FROM categories;
            """)
            cursor.execute("DROP TABLE categories;")
            cursor.execute("ALTER TABLE categories_new RENAME TO categories;")
            cursor.execute("PRAGMA foreign_keys = ON;")

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
