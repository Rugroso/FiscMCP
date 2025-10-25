#!/usr/bin/env python3
"""
Punto de entrada para deployment de FiscAI MCP Server
Este archivo expone el objeto FastMCP para servicios de hosting
"""

from src.main import mcp

# Exportar el objeto mcp para que fastmcp run pueda encontrarlo
__all__ = ['mcp']

# El objeto 'mcp' ya está configurado con todas las herramientas y prompts
# FastMCP lo detectará automáticamente cuando ejecutes: fastmcp run server.py
