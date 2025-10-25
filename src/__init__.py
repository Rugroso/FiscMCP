"""
FiscAI MCP Server - Servidor MCP para asesoramiento fiscal mexicano
"""

__version__ = "1.0.0"
__author__ = "FiscAI Team"
__description__ = "Servidor MCP con herramientas fiscales para México usando FastMCP"

from .main import main
from .config import config
from .gemini import gemini_client
from .supabase_client import supabase_client

__all__ = [
    "main",
    "config", 
    "gemini_client",
    "supabase_client"
]