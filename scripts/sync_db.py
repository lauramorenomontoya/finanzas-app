#!/usr/bin/env python3
"""
sync_db.py - Sincroniza la base de datos de producción (App Instalada) al entorno local.

Uso:
    python3 sync_db.py
"""

import os
import sys
import shutil
import sqlite3
import datetime

def get_prod_db_path() -> str:
    if sys.platform == "darwin":
        new_path = os.path.expanduser("~/Library/Application Support/Montu/finanzas.db")
        old_path = os.path.expanduser("~/Library/Application Support/ControlFinanciero/finanzas.db")
    elif sys.platform == "win32":
        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        new_path = os.path.join(appdata, "Montu", "finanzas.db")
        old_path = os.path.join(appdata, "ControlFinanciero", "finanzas.db")
    else:
        new_path = os.path.expanduser("~/.local/share/Montu/finanzas.db")
        old_path = os.path.expanduser("~/.local/share/ControlFinanciero/finanzas.db")

    if os.path.exists(new_path):
        return new_path
    if os.path.exists(old_path):
        return old_path
    return new_path

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_dir = os.path.dirname(script_dir)
    local_db = os.path.join(repo_dir, "finanzas.db")
    prod_db = get_prod_db_path()

    print("=" * 60)
    print(" Sincronizador de Base de Datos - Montu")
    print("=" * 60)
    print(f"Origen (App Instalada): {prod_db}")
    print(f"Destino (Repo Local):    {local_db}")

    if not os.path.exists(prod_db):
        print("\n❌ Error: No se encontró la base de datos de la app instalada.")
        sys.exit(1)

    # Crear respaldo del archivo local actual
    backup_dir = os.path.join(repo_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if os.path.exists(local_db):
        backup_file = os.path.join(backup_dir, f"finanzas_local_pre_sync_{timestamp}.db")
        shutil.copy2(local_db, backup_file)
        print(f"\n📦 Respaldo previo creado en:\n   {backup_file}")

    # Sincronización segura usando la SQLite Backup API
    print("\n🔄 Sincronizando datos de forma segura...")
    src_conn = sqlite3.connect(prod_db)
    dst_conn = sqlite3.connect(local_db)
    try:
        with dst_conn:
            src_conn.backup(dst_conn)
    finally:
        dst_conn.close()
        src_conn.close()

    # Validación
    conn = sqlite3.connect(local_db)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM cop_transactions")
    cop_count = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM usd_transactions")
    usd_count = cur.fetchone()[0]
    conn.close()

    print("✅ Sincronización completada exitosamente.")
    print(f"   • Total transacciones COP: {cop_count}")
    print(f"   • Total transacciones USD: {usd_count}")
    print("=" * 60)

if __name__ == "__main__":
    main()
