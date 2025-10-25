#!/usr/bin/env python3
"""
Script para ejecutar el servidor HTTP de FiscAI MCP
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == "__main__":
    try:
        from src.http_server import app, config
        import uvicorn
        
        print("🚀 Iniciando FiscAI MCP - Servidor HTTP")
        print(f"📡 Accede a: http://localhost:{config.PORT}")
        print(f"📚 Documentación interactiva: http://localhost:{config.PORT}/docs")
        print(f"🔍 Health check: http://localhost:{config.PORT}/health")
        print(f"📋 Lista de herramientas: http://localhost:{config.PORT}/tools")
        print("\n" + "="*60)
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=config.PORT,
            log_level="info"
        )
    except ImportError as e:
        print(f"❌ Error importando módulos: {e}")
        print("💡 Asegúrate de instalar las dependencias con: pip install fastapi uvicorn[standard]")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error iniciando el servidor HTTP: {e}")
        sys.exit(1)
