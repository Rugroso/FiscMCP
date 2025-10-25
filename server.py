#!/usr/bin/env python3
"""
Punto de entrada para deployment de FiscAI MCP Server
Este archivo expone el objeto FastMCP para servicios de hosting
"""

import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path para imports
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

# Cargar variables de entorno si existe .env
try:
    from dotenv import load_dotenv
    env_path = root_dir / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print("✅ Variables de entorno cargadas desde .env")
except ImportError:
    print("ℹ️  python-dotenv no disponible, usando variables del sistema")

# Verificar variables críticas
required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY', 'GEMINI_API_KEY']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    print("❌ Faltan las siguientes variables de entorno:")
    for var in missing_vars:
        print(f"   - {var}")
    print("\n💡 Asegúrate de configurar estas variables en tu plataforma de deployment")
    print("   o crear un archivo .env con los valores necesarios")
    
    # En development, salir. En production, continuar con warning
    if os.getenv('NODE_ENV') != 'production':
        sys.exit(1)
    else:
        print("⚠️  Continuando en modo producción - algunas funciones pueden fallar")

try:
    from src.main import mcp
    print("🚀 FiscAI MCP Server iniciado correctamente")
except Exception as e:
    print(f"❌ Error importando el servidor MCP: {e}")
    raise

# Exportar el objeto mcp para que fastmcp run pueda encontrarlo
__all__ = ['mcp']

# El objeto 'mcp' ya está configurado con todas las herramientas y prompts
# FastMCP lo detectará automáticamente cuando ejecutes: fastmcp run server.py
