"""
Configuración para el servidor MCP de FiscAI
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración centralizada para FiscAI MCP Server"""
    
    # Configuración del servidor
    PORT: int = int(os.getenv('PORT', '8000'))
    NODE_ENV: str = os.getenv('NODE_ENV', 'development')
    
    # Supabase
    SUPABASE_URL: str = os.getenv('SUPABASE_URL', '')
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
    
    # Gemini AI
    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL: str = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')
    
    # Configuración de embeddings
    EMBED_DIM: int = int(os.getenv('EMBED_DIM', '768'))
    SIMILARITY_THRESHOLD: float = float(os.getenv('SIMILARITY_THRESHOLD', '0.7'))
    
    @classmethod
    def validate_required_vars(cls) -> None:
        """Validar que las variables requeridas estén configuradas"""
        required_vars = [
            'SUPABASE_URL',
            'SUPABASE_SERVICE_ROLE_KEY',
            'GEMINI_API_KEY'
        ]
        
        missing_vars = []
        for var_name in required_vars:
            if not getattr(cls, var_name):
                missing_vars.append(var_name)
        
        if missing_vars:
            print("❌ Faltan las siguientes variables de entorno:")
            for var in missing_vars:
                print(f"   - {var}")
            raise ValueError(f"Variables de entorno faltantes: {', '.join(missing_vars)}")
        
        print("✅ Configuración cargada correctamente")

# Instancia global de configuración
config = Config()

# Validar configuración al importar
if __name__ != "__main__":
    config.validate_required_vars()
