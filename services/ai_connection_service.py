"""
Servicio de Conexión Automática con Asistentes de IA (MCP).
Permite configurar en 1-clic el servidor MCP de Control Financiero
en Google Antigravity, Claude Desktop y Cursor (macOS y Windows).
"""

import os
import sys
import json
import shutil
from typing import Dict, Any, List, Tuple, Optional


class AIConnectionService:
    @staticmethod
    def get_data_dir() -> str:
        """Obtiene el directorio de datos persistentes del sistema."""
        if sys.platform == "darwin":
            path = os.path.expanduser("~/Library/Application Support/ControlFinanciero")
        elif sys.platform == "win32":
            path = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "ControlFinanciero")
        else:
            path = os.path.expanduser("~/.local/share/ControlFinanciero")
        os.makedirs(path, exist_ok=True)
        return path

    @classmethod
    def get_installed_mcp_script_path(cls) -> str:
        """Ruta fija donde se aloja mcp_server.py para uso de los asistentes."""
        return os.path.join(cls.get_data_dir(), "mcp_server.py")

    @classmethod
    def deploy_mcp_server_script(cls) -> str:
        """Copia mcp_server.py al directorio del sistema del usuario."""
        dest_path = cls.get_installed_mcp_script_path()
        
        # Buscar el archivo mcp_server.py en el proyecto actual
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        source_path = os.path.join(current_dir, "mcp_server.py")
        
        if os.path.exists(source_path):
            shutil.copy2(source_path, dest_path)
            try:
                os.chmod(dest_path, 0o755)
            except Exception:
                pass
        return dest_path

    @staticmethod
    def get_python_command() -> str:
        """Determina el comando de Python apropiado para invocar el script."""
        # Si el entorno actual tiene un ejecutable específico, usarlo o python3/python
        if sys.platform == "win32":
            return "python"
        return "python3"

    @classmethod
    def get_clients_metadata(cls) -> List[Dict[str, Any]]:
        """Devuelve los clientes de IA soportados con sus rutas de configuración."""
        if sys.platform == "darwin":
            antigravity_path = os.path.expanduser("~/.gemini/config/mcp_config.json")
            claude_path = os.path.expanduser("~/Library/Application Support/Claude/claude_desktop_config.json")
            cursor_path = os.path.expanduser("~/.cursor/mcp.json")
        elif sys.platform == "win32":
            user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
            app_data = os.environ.get("APPDATA", user_profile)
            antigravity_path = os.path.join(user_profile, ".gemini", "config", "mcp_config.json")
            claude_path = os.path.join(app_data, "Claude", "claude_desktop_config.json")
            cursor_path = os.path.join(user_profile, ".cursor", "mcp.json")
        else:
            antigravity_path = os.path.expanduser("~/.gemini/config/mcp_config.json")
            claude_path = os.path.expanduser("~/.config/Claude/claude_desktop_config.json")
            cursor_path = os.path.expanduser("~/.cursor/mcp.json")

        clients = [
            {
                "id": "antigravity",
                "name": "Google Antigravity",
                "icon": "⚡",
                "config_path": antigravity_path,
                "dir_path": os.path.dirname(antigravity_path)
            },
            {
                "id": "claude",
                "name": "Claude Desktop",
                "icon": "🧠",
                "config_path": claude_path,
                "dir_path": os.path.dirname(claude_path)
            },
            {
                "id": "cursor",
                "name": "Cursor / VS Code",
                "icon": "💻",
                "config_path": cursor_path,
                "dir_path": os.path.dirname(cursor_path)
            }
        ]

        # Comprobar estado de cada cliente
        for client in clients:
            cfg_file = client["config_path"]
            dir_exists = os.path.exists(client["dir_path"])
            file_exists = os.path.exists(cfg_file)
            
            is_connected = False
            if file_exists:
                try:
                    with open(cfg_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    mcp_servers = data.get("mcpServers", {})
                    if "ControlFinanciero" in mcp_servers:
                        is_connected = True
                except Exception:
                    pass

            client["is_installed"] = dir_exists or file_exists
            client["is_connected"] = is_connected

        return clients

    @classmethod
    def connect_client(cls, client_id: str) -> Tuple[bool, str]:
        """Conecta un cliente específico agregando el servidor MCP de Control Financiero."""
        clients = {c["id"]: c for c in cls.get_clients_metadata()}
        if client_id not in clients:
            return False, f"Cliente '{client_id}' no reconocido."

        client = clients[client_id]
        mcp_script = cls.deploy_mcp_server_script()
        python_cmd = cls.get_python_command()

        cfg_file = client["config_path"]
        os.makedirs(client["dir_path"], exist_ok=True)

        config_data = {"mcpServers": {}}
        if os.path.exists(cfg_file):
            try:
                with open(cfg_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                if "mcpServers" not in config_data or not isinstance(config_data["mcpServers"], dict):
                    config_data["mcpServers"] = {}
            except Exception:
                config_data = {"mcpServers": {}}

        # Inyectar servidor ControlFinanciero
        config_data["mcpServers"]["ControlFinanciero"] = {
            "command": python_cmd,
            "args": [mcp_script]
        }

        try:
            with open(cfg_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            return True, f"¡{client['name']} configurado exitosamente!"
        except Exception as e:
            return False, f"Error al escribir archivo: {str(e)}"

    @classmethod
    def connect_all_detected(cls) -> Tuple[bool, str, List[str]]:
        """
        Conecta todos los clientes detectados o presentes en la computadora.
        Si ninguno está instalado, configura al menos Antigravity y Claude Desktop.
        """
        clients = cls.get_clients_metadata()
        connected = []
        errors = []

        # Determinar qué clientes configurar (los instalados o los principales)
        target_clients = [c for c in clients if c["is_installed"]]
        if not target_clients:
            # Si aún no tiene carpetas creadas, preconfigurar Antigravity y Claude
            target_clients = [c for c in clients if c["id"] in ("antigravity", "claude")]

        for c in target_clients:
            ok, msg = cls.connect_client(c["id"])
            if ok:
                connected.append(c["name"])
            else:
                errors.append(f"{c['name']}: {msg}")

        if connected:
            summary = f"Conectado exitosamente con: {', '.join(connected)}."
            if errors:
                summary += f" (Advertencias: {'; '.join(errors)})"
            return True, summary, connected
        else:
            return False, f"No se pudo configurar: {'; '.join(errors)}", []
