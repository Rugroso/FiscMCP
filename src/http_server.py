"""
Servidor HTTP para probar las herramientas MCP vía REST API
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn

from .config import config
from .gemini import gemini_client
from .supabase_client import supabase_client

app = FastAPI(
    title="FiscAI MCP Server - HTTP API",
    description="API REST para probar las herramientas MCP de FiscAI",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de Request
class FiscalAdviceRequest(BaseModel):
    actividad: str
    ingresos_anuales: float
    estado: str

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "guest"
    conversation_id: Optional[str] = None

class RiskAnalysisRequest(BaseModel):
    actividad: str
    ingresos_anuales: float
    estado: str
    situacion_actual: str

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5

class UserContextRequest(BaseModel):
    user_id: str

# Health Check
@app.get("/")
async def root():
    """Endpoint de verificación básica"""
    return {
        "status": "online",
        "service": "FiscAI MCP Server",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "tools": "/tools",
            "fiscal_advice": "/api/fiscal-advice",
            "chat": "/api/chat",
            "risk_analysis": "/api/risk-analysis",
            "search": "/api/search",
            "user_context": "/api/user-context"
        }
    }

@app.get("/health")
async def health_check():
    """Verificar el estado de salud del servidor y conexiones"""
    health_status = {
        "status": "healthy",
        "services": {}
    }
    
    # Verificar Supabase
    try:
        await supabase_client.get_user_context("test-user")
        health_status["services"]["supabase"] = "connected"
    except Exception as e:
        health_status["services"]["supabase"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Verificar Gemini
    try:
        await gemini_client.generate_embedding("test")
        health_status["services"]["gemini"] = "connected"
    except Exception as e:
        health_status["services"]["gemini"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Verificar configuración
    try:
        config.validate_required_vars()
        health_status["services"]["config"] = "valid"
    except Exception as e:
        health_status["services"]["config"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    return health_status

@app.get("/tools")
async def list_tools():
    """Listar todas las herramientas MCP disponibles"""
    return {
        "tools": [
            {
                "name": "get_fiscal_advice",
                "description": "Obtener recomendaciones fiscales personalizadas",
                "endpoint": "/api/fiscal-advice"
            },
            {
                "name": "chat_with_fiscal_assistant",
                "description": "Chatear con Juan Pablo, el asistente fiscal IA",
                "endpoint": "/api/chat"
            },
            {
                "name": "analyze_fiscal_risk",
                "description": "Analizar riesgos fiscales",
                "endpoint": "/api/risk-analysis"
            },
            {
                "name": "search_fiscal_documents",
                "description": "Buscar documentos fiscales relevantes",
                "endpoint": "/api/search"
            },
            {
                "name": "get_user_fiscal_context",
                "description": "Obtener contexto fiscal del usuario",
                "endpoint": "/api/user-context"
            }
        ]
    }

@app.post("/api/fiscal-advice")
async def get_fiscal_advice(request: FiscalAdviceRequest):
    """Obtener recomendaciones fiscales personalizadas"""
    try:
        # Generar prompt
        prompt = f"""Como experto fiscal mexicano, proporciona recomendaciones específicas para:
        
Actividad: {request.actividad}
Ingresos anuales: ${request.ingresos_anuales:,.2f} MXN
Estado: {request.estado}

Incluye:
1. Régimen fiscal recomendado
2. Obligaciones fiscales principales
3. Deducciones aplicables
4. Plazos importantes
5. Consejos específicos para optimizar su situación fiscal
"""
        
        response = await gemini_client.chat_with_assistant(prompt)
        
        return {
            "success": True,
            "data": {
                "advice": response,
                "input": request.dict()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_with_assistant(request: ChatRequest):
    """Chatear con Juan Pablo, el asistente fiscal"""
    try:
        # Obtener contexto del usuario
        user_context = await supabase_client.get_user_context(request.user_id)
        
        # Construir prompt con contexto
        context_str = ""
        if user_context:
            context_str = f"\nContexto del usuario: {user_context}"
        
        prompt = f"""Eres Juan Pablo, un asistente fiscal mexicano amigable y experto.
{context_str}

Usuario pregunta: {request.message}

Responde de manera clara, profesional y útil."""
        
        response = await gemini_client.chat_with_assistant(prompt)
        
        # Guardar en historial
        await supabase_client.save_chat_message(
            request.user_id,
            request.message,
            response
        )
        
        return {
            "success": True,
            "data": {
                "response": response,
                "user_id": request.user_id,
                "conversation_id": request.conversation_id
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/risk-analysis")
async def analyze_risk(request: RiskAnalysisRequest):
    """Analizar riesgos fiscales"""
    try:
        prompt = f"""Analiza los riesgos fiscales para:

Actividad: {request.actividad}
Ingresos: ${request.ingresos_anuales:,.2f} MXN
Estado: {request.estado}
Situación: {request.situacion_actual}

Proporciona:
1. Nivel de riesgo (Bajo/Medio/Alto)
2. Riesgos identificados
3. Recomendaciones para mitigar riesgos
4. Acciones inmediatas sugeridas
"""
        
        response = await gemini_client.analyze_fiscal_risk(prompt)
        
        return {
            "success": True,
            "data": {
                "analysis": response,
                "input": request.dict()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search")
async def search_documents(request: SearchRequest):
    """Buscar documentos fiscales usando búsqueda semántica"""
    try:
        # Generar embedding de la consulta
        query_embedding = await gemini_client.generate_embedding(request.query)
        
        # Buscar documentos similares
        results = await supabase_client.search_similar_documents(
            query_embedding,
            limit=request.limit
        )
        
        return {
            "success": True,
            "data": {
                "query": request.query,
                "results": results,
                "count": len(results)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user-context")
async def get_user_context(request: UserContextRequest):
    """Obtener contexto fiscal del usuario"""
    try:
        context = await supabase_client.get_user_context(request.user_id)
        
        return {
            "success": True,
            "data": {
                "user_id": request.user_id,
                "context": context
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Iniciando servidor HTTP de FiscAI MCP...")
    print(f"📡 Servidor corriendo en: http://localhost:{config.PORT}")
    print(f"📚 Documentación en: http://localhost:{config.PORT}/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=config.PORT,
        log_level="info"
    )
