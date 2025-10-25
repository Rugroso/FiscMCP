#!/usr/bin/env python3
"""
Servidor MCP para FiscAI usando FastMCP
Implementa todas las herramientas fiscales necesarias
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Importar nuestros módulos
from .config import config
from .gemini import gemini_client
from .supabase_client import supabase_client

# Crear instancia del servidor FastMCP
mcp = FastMCP("FiscAI MCP Server", version="1.0.0")

# ====== MODELOS DE DATOS ======

class FiscalAdviceRequest(BaseModel):
    """Modelo para solicitud de consejo fiscal"""
    actividad: str = Field(..., description="Actividad económica o tipo de negocio")
    ingresos_anuales: Optional[int] = Field(None, description="Ingresos anuales estimados en pesos mexicanos")
    estado: Optional[str] = Field(None, description="Estado de la República Mexicana")
    regimen_actual: Optional[str] = Field(None, description="Régimen fiscal actual si lo tiene")
    tiene_rfc: Optional[bool] = Field(None, description="Si ya tiene RFC")
    contexto_adicional: Optional[str] = Field(None, description="Contexto adicional sobre la situación fiscal")

class ChatRequest(BaseModel):
    """Modelo para solicitud de chat"""
    message: str = Field(..., description="Mensaje del usuario para el asistente fiscal")
    user_id: Optional[str] = Field(None, description="ID del usuario para mantener contexto")
    session_id: Optional[str] = Field(None, description="ID de sesión para el chat")

class RiskAnalysisRequest(BaseModel):
    """Modelo para análisis de riesgo"""
    has_rfc: bool = Field(..., description="Si tiene RFC registrado")
    has_efirma: Optional[bool] = Field(None, description="Si tiene e.firma activa")
    emite_cfdi: Optional[bool] = Field(None, description="Si emite facturas CFDI")
    declara_mensual: Optional[bool] = Field(None, description="Si presenta declaraciones mensuales")
    ingresos_anuales: Optional[int] = Field(None, description="Ingresos anuales en pesos")
    actividad: Optional[str] = Field(None, description="Actividad económica")
    regimen_fiscal: Optional[str] = Field(None, description="Régimen fiscal actual")

class SearchDocumentsRequest(BaseModel):
    """Modelo para búsqueda de documentos"""
    query: str = Field(..., description="Consulta para buscar documentos similares")
    limit: Optional[int] = Field(5, description="Número máximo de documentos a retornar")

class UserContextRequest(BaseModel):
    """Modelo para obtener contexto del usuario"""
    user_id: str = Field(..., description="ID del usuario")

# ====== HERRAMIENTAS MCP ======

@mcp.tool()
async def get_fiscal_advice(request: FiscalAdviceRequest) -> Dict[str, Any]:
    """
    Obtener recomendaciones fiscales personalizadas para un negocio mexicano.
    
    Proporciona análisis detallado del régimen fiscal más conveniente,
    pasos de formalización, obligaciones y estimación de costos.
    """
    try:
        # Convertir a diccionario para compatibilidad
        profile_data = request.dict()
        
        # Buscar casos similares
        similar_cases = await supabase_client.find_similar_fiscal_cases(profile_data)
        
        # Crear respuesta base
        base_recommendation = {
            'profile': profile_data,
            'recommendation': f"Análisis fiscal preliminar para {request.actividad}",
            'timestamp': datetime.now().isoformat()
        }
        
        # Enriquecer con Gemini
        enhanced_recommendation = await gemini_client.enhance_recommendation(
            base_recommendation,
            similar_cases,
            profile_data
        )
        
        return {
            'success': True,
            'data': enhanced_recommendation,
            'message': f"Recomendación fiscal generada para {request.actividad}"
        }
        
    except Exception as error:
        return {
            'success': False,
            'error': str(error),
            'message': "Error generando recomendación fiscal"
        }

@mcp.tool()
async def chat_with_fiscal_assistant(request: ChatRequest) -> Dict[str, Any]:
    """
    Chatear con Juan Pablo, el asistente fiscal experto en México.
    
    Proporciona respuestas contextualizadas sobre temas fiscales,
    mantiene historial de conversación y referencia documentos relevantes.
    """
    try:
        user_context = None
        chat_history = []
        
        # Obtener contexto del usuario si está disponible
        if request.user_id:
            user_context = await supabase_client.get_user_context(request.user_id)
            chat_history = await supabase_client.get_chat_history(request.user_id, 5)
        
        # Generar embedding para encontrar documentos relevantes
        embedding = await gemini_client.generate_embedding(request.message)
        relevant_docs = await supabase_client.search_similar_documents(embedding, 3)
        
        # Obtener respuesta del asistente
        response = await gemini_client.chat_with_assistant(
            request.message,
            user_context,
            chat_history,
            relevant_docs
        )
        
        # Guardar mensaje si hay user_id
        if request.user_id:
            await supabase_client.save_chat_message(
                request.user_id,
                request.message,
                response,
                {'session_id': request.session_id}
            )
        
        return {
            'success': True,
            'data': {
                'response': response,
                'context_used': bool(user_context),
                'docs_referenced': len(relevant_docs)
            },
            'message': "Respuesta del asistente fiscal generada"
        }
        
    except Exception as error:
        return {
            'success': False,
            'error': str(error),
            'message': "Error en el chat con el asistente"
        }

@mcp.tool()
async def analyze_fiscal_risk(request: RiskAnalysisRequest) -> Dict[str, Any]:
    """
    Analizar el riesgo fiscal de un perfil de negocio mexicano.
    
    Evalúa el cumplimiento actual y proporciona un score de riesgo
    con recomendaciones específicas para mejorar la situación fiscal.
    """
    try:
        # Convertir a diccionario
        profile_data = request.dict()
        
        # Analizar riesgo con Gemini
        risk_analysis = await gemini_client.analyze_fiscal_risk(profile_data)
        
        return {
            'success': True,
            'data': risk_analysis,
            'message': f"Análisis de riesgo completado - Nivel: {risk_analysis.get('level', 'Desconocido')}"
        }
        
    except Exception as error:
        return {
            'success': False,
            'error': str(error),
            'message': "Error analizando riesgo fiscal"
        }

@mcp.tool()
async def search_fiscal_documents(request: SearchDocumentsRequest) -> Dict[str, Any]:
    """
    Buscar documentos fiscales similares usando embeddings semánticos.
    
    Encuentra documentos relevantes en la base de conocimiento
    basándose en similitud semántica con la consulta.
    """
    try:
        # Generar embedding de la consulta
        embedding = await gemini_client.generate_embedding(request.query)
        
        # Buscar documentos similares
        documents = await supabase_client.search_similar_documents(
            embedding, 
            request.limit
        )
        
        return {
            'success': True,
            'data': {
                'documents': documents,
                'count': len(documents),
                'query': request.query
            },
            'message': f"Encontrados {len(documents)} documentos relevantes"
        }
        
    except Exception as error:
        return {
            'success': False,
            'error': str(error),
            'message': "Error buscando documentos fiscales"
        }

@mcp.tool()
async def get_user_fiscal_context(request: UserContextRequest) -> Dict[str, Any]:
    """
    Obtener el contexto fiscal completo de un usuario registrado.
    
    Incluye información del perfil del usuario y su historial
    de conversaciones para proporcionar asistencia personalizada.
    """
    try:
        # Obtener contexto del usuario
        user_context = await supabase_client.get_user_context(request.user_id)
        
        if not user_context:
            return {
                'success': False,
                'error': "Usuario no encontrado",
                'message': f"No se encontró contexto para el usuario {request.user_id}"
            }
        
        # Obtener historial de chat
        chat_history = await supabase_client.get_chat_history(request.user_id, 10)
        
        return {
            'success': True,
            'data': {
                'user_context': user_context,
                'chat_history': chat_history,
                'history_count': len(chat_history)
            },
            'message': f"Contexto obtenido para usuario {request.user_id}"
        }
        
    except Exception as error:
        return {
            'success': False,
            'error': str(error),
            'message': "Error obteniendo contexto del usuario"
        }

# ====== PROMPTS MCP ======

@mcp.prompt()
async def fiscal_consultation(
    business_type: str,
    annual_income: Optional[str] = None,
    state: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Generar consulta fiscal personalizada detallada.
    
    Crea un prompt estructurado para obtener recomendaciones
    fiscales específicas basadas en el tipo de negocio e ingresos.
    
    Args:
        business_type: Tipo de negocio o actividad económica
        annual_income: Ingresos anuales estimados (opcional)
        state: Estado de la República Mexicana (opcional)
    """
    income_text = f"${int(annual_income):,} MXN" if annual_income and annual_income.isdigit() else "No especificado"
    
    prompt_text = f"""Como experto asesor fiscal mexicano, proporciona una consulta detallada para:

**Información del Negocio:**
- Tipo de negocio: {business_type}
- Ingresos anuales: {income_text}
- Estado: {state or 'No especificado'}

**Solicitud de Análisis:**
Proporciona una recomendación fiscal completa que incluya:

1. **Régimen Fiscal Recomendado** con justificación detallada
2. **Pasos Específicos** para la formalización paso a paso
3. **Obligaciones Fiscales** y calendario de cumplimiento
4. **Checklist de Documentos** necesarios para el trámite
5. **Estimación Realista de Costos** de formalización y mantenimiento
6. **Beneficios Concretos** del régimen recomendado
7. **Alternativas Viables** si aplican según el perfil
8. **Cronograma Sugerido** de implementación

**Formato Requerido:**
- Usa **negrita** para títulos y conceptos importantes
- Usa *cursiva* para notas y observaciones adicionales
- Incluye ejemplos numéricos específicos cuando sea relevante
- Mantén un lenguaje claro y accesible para micro-negocios

**Contexto:**
Enfócate en las necesidades de micro y pequeñas empresas mexicanas, considerando las últimas actualizaciones fiscales y los beneficios disponibles para emprendedores."""

    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": prompt_text
            }
        }
    ]

@mcp.prompt()
async def risk_assessment(current_status: str) -> List[Dict[str, Any]]:
    """
    Generar evaluación integral de riesgo fiscal.
    
    Crea un prompt para análisis detallado de riesgo fiscal
    basado en la situación actual del contribuyente.
    
    Args:
        current_status: Estado fiscal actual del negocio
    """
    prompt_text = f"""Como experto en cumplimiento fiscal mexicano, realiza un análisis integral de riesgo para:

**Estado Fiscal Actual:**
{current_status}

**Análisis Requerido:**

1. **Evaluación de Riesgo**
   - Nivel de riesgo (Bajo/Medio/Alto) con puntuación numérica (0-100)
   - Justificación detallada del nivel asignado

2. **Identificación de Factores de Riesgo**
   - Factores críticos que requieren atención inmediata
   - Factores moderados que necesitan seguimiento
   - Oportunidades de mejora identificadas

3. **Análisis de Consecuencias**
   - Consecuencias potenciales de mantener el estado actual
   - Riesgos específicos de incumplimiento
   - Impacto económico estimado

4. **Plan de Mitigación Estructurado**
   - Acciones correctivas prioritarias
   - Pasos de implementación detallados
   - Recursos necesarios para cada acción

5. **Cronograma de Implementación**
   - Fases de implementación con fechas sugeridas
   - Hitos de seguimiento y evaluación
   - Indicadores de éxito medibles

6. **Análisis Costo-Beneficio**
   - Costos estimados de regularización
   - Beneficios esperados del cumplimiento
   - ROI de las acciones propuestas

7. **Recomendaciones Específicas**
   - Acciones inmediatas (0-30 días)
   - Acciones a mediano plazo (1-6 meses)
   - Estrategia a largo plazo (6+ meses)

**Formato de Respuesta:**
- Estructura clara con secciones bien definidas
- Uso de **negrita** para puntos críticos
- Ejemplos numéricos cuando sea aplicable
- Recomendaciones accionables y específicas

**Contexto Regulatorio:**
Considera las últimas disposiciones fiscales mexicanas y las mejores prácticas para contribuyentes del perfil analizado."""

    return [
        {
            "role": "user", 
            "content": {
                "type": "text",
                "text": prompt_text
            }
        }
    ]

# ====== FUNCIÓN PRINCIPAL ======

def main():
    """Función principal para ejecutar el servidor MCP"""
    try:
        print("🚀 Iniciando FiscAI MCP Server con FastMCP...")
        print("📋 Herramientas registradas:")
        print("   ✅ get_fiscal_advice - Recomendaciones fiscales personalizadas")
        print("   ✅ chat_with_fiscal_assistant - Chat con Juan Pablo")
        print("   ✅ analyze_fiscal_risk - Análisis de riesgo fiscal")
        print("   ✅ search_fiscal_documents - Búsqueda de documentos")
        print("   ✅ get_user_fiscal_context - Contexto del usuario")
        print("💬 Prompts registrados:")
        print("   ✅ fiscal_consultation - Consulta fiscal personalizada")
        print("   ✅ risk_assessment - Evaluación de riesgo fiscal")
        print("🎯 Servidor MCP listo para recibir peticiones...")
        
        # Ejecutar el servidor FastMCP (maneja su propio event loop)
        mcp.run()
        
    except Exception as error:
        print(f"❌ Error iniciando el servidor MCP: {error}")
        raise error

if __name__ == "__main__":
    # Ejecutar el servidor
    main()