#!/usr/bin/env python3
"""
Punto de entrada para el servidor MCP de FiscAI
"""

import sys
import os
import asyncio

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.main import main
    
    if __name__ == "__main__":
        print("🚀 Iniciando FiscAI MCP Server...")
        main()
        
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    print("💡 Asegúrate de instalar las dependencias con: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error iniciando el servidor: {e}")
    sys.exit(1)