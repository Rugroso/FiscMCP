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
from .places import search_places

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
    Obtener recomendaciones fiscales personalizadas usando RAG (Retrieval-Augmented Generation).
    
    Implementa el flujo completo:
    1. Genera query semántica enriquecida del perfil
    2. Busca documentos relevantes con embeddings (top-k)
    3. Construye contexto con documentos encontrados
    4. Genera recomendación con Gemini usando el contexto
    
    Proporciona análisis detallado del régimen fiscal más conveniente,
    pasos de formalización, obligaciones y estimación de costos.
    """
    try:
        # Convertir a diccionario para compatibilidad
        profile_data = request.dict()
        
        # 1. Generar query semántica enriquecida (como profile_to_query de Python)
        query_parts = [
            f"Actividad: {request.actividad}",
            f"Ingresos anuales estimados: {request.ingresos_anuales or 'No especificado'}",
            f"Entidad federativa: {request.estado or 'No especificado'}",
            f"¿Tiene RFC?: {'Sí' if request.tiene_rfc else 'No'}",
        ]
        
        if request.regimen_actual:
            query_parts.append(f"Régimen actual: {request.regimen_actual}")
        if request.contexto_adicional:
            query_parts.append(f"Contexto: {request.contexto_adicional}")
        
        semantic_query = (
            "Perfil fiscal. Necesito sugerir régimen, pasos de formalización, "
            "obligaciones y calendario básico, citando fuentes del SAT:\n" + 
            "\n".join(query_parts)
        )
        
        print(f"[RAG] Query generada: {semantic_query[:200]}...")
        
        # 2. Generar embedding de la query
        print("[RAG] Generando embedding...")
        query_embedding = await gemini_client.generate_embedding(semantic_query)
        
        # 3. Buscar documentos relevantes (top-k = 6, threshold = 0.6)
        print("[RAG] Buscando documentos relevantes...")
        documents = await supabase_client.search_similar_documents(
            query_embedding, 
            limit=6,
            threshold=0.6
        )
        
        print(f"[RAG] Encontrados {len(documents)} documentos relevantes")
        
        # 4. Construir contexto estructurado (como build_context de Python)
        context_blocks = []
        for i, doc in enumerate(documents, start=1):
            title = doc.get('title', 'Documento')
            scope = doc.get('scope', 'General')
            url = doc.get('source_url', 'SAT')
            content = doc.get('content', '')
            
            block = f"[{i}] {title} — {scope}\nFuente: {url}\n{content}"
            context_blocks.append(block)
        
        context = "\n\n".join(context_blocks)
        
        # 5. Generar recomendación con Gemini usando RAG
        print("[RAG] Generando recomendación con contexto...")
        recommendation = await gemini_client.generate_recommendation(
            profile_data,
            context
        )
        
        # 6. Retornar resultado estructurado
        return {
            'success': True,
            'data': {
                'recommendation': recommendation,
                'sources': [
                    {
                        'title': doc.get('title', 'Documento'),
                        'scope': doc.get('scope', 'General'),
                        'url': doc.get('source_url', 'SAT'),
                        'similarity': doc.get('similarity', 0.8)
                    }
                    for doc in documents
                ],
                'matches_count': len(documents),
                'profile': profile_data
            },
            'message': f"Recomendación fiscal generada para {request.actividad} usando {len(documents)} fuentes"
        }
        
    except Exception as error:
        print(f"[RAG] Error: {error}")
        import traceback
        traceback.print_exc()
        
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
async def search_places_tool(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Buscar lugares (bancos, oficinas SAT, etc.) usando Google Places via EXPO_PUBLIC_GOOGLE_MAPS_API_KEY.
    Acepta request con keys: query (required), lat (optional), lng (optional), limit (optional)
    Retorna { success: true, data: { query, results: [...] } }
    """
    try:
        # soportar varios envoltorios: request puede venir directo o como objeto pydantic
        if isinstance(request, dict) and request.get('request'):
            body = request.get('request')
        else:
            body = request if isinstance(request, dict) else {}

        query = body.get('query') or body.get('textQuery') or ''
        if not query:
            return {'success': False, 'error': 'Falta query', 'message': 'Se requiere query'}

        lat = body.get('lat')
        lng = body.get('lng')
        limit = int(body.get('limit', 5))

        # Llamar la implementación de places
        result = search_places(query=query, lat=float(lat) if lat else None, lng=float(lng) if lng else None, limit=limit)

        return {
            'success': True,
            'data': result,
            'message': f"Encontrados {len(result.get('results', []))} lugares para '{query}'"
        }
    except Exception as e:
        print('[search_places_tool] Error:', e)
        return {'success': False, 'error': str(e), 'message': 'Error buscando lugares'}

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

@mcp.tool()
async def open_map_location(location_type: str, place_id: Optional[str] = None, search_query: Optional[str] = None) -> Dict[str, Any]:
    """
    Generar un deep link para abrir el mapa en la app con una ubicación específica.
    
    Esta herramienta permite al chatbot dirigir al usuario al mapa interactivo
    mostrando bancos o oficinas del SAT cercanas, o un lugar específico.
    
    Args:
        location_type: Tipo de lugar a buscar ("bank" para Banorte o "sat" para oficinas SAT)
        place_id: ID opcional de un lugar específico de Google Places para enfocar el mapa
        search_query: Query opcional para buscar un lugar específico (ej: "Banorte Reforma")
    
    Returns:
        Dict con el deep link de la app y la información para mostrar al usuario
    """
    try:
        # Validar el tipo de ubicación
        if location_type not in ["bank", "sat"]:
            return {
                'success': False,
                'error': "Tipo de ubicación inválido",
                'message': "location_type debe ser 'bank' o 'sat'"
            }
        
        # Construir el deep link para la app
        # Formato: fiscai://map?type=bank&placeId=ChIJ...
        base_url = "fiscai://map"
        params = [f"type={location_type}"]
        
        if place_id:
            params.append(f"placeId={place_id}")
        
        if search_query:
            params.append(f"query={search_query}")
        
        deep_link = f"{base_url}?{'&'.join(params)}"
        
        # Construir mensaje descriptivo
        location_name = "Banorte" if location_type == "bank" else "oficinas del SAT"
        
        if place_id:
            message = f"Abriendo mapa enfocado en un {location_name} específico"
        elif search_query:
            message = f"Abriendo mapa buscando: {search_query}"
        else:
            message = f"Abriendo mapa con {location_name} cercanos"
        
        return {
            'success': True,
            'data': {
                'deep_link': deep_link,
                'location_type': location_type,
                'place_id': place_id,
                'search_query': search_query,
                'user_message': f"📍 {message}. El mapa se abrirá automáticamente."
            },
            'message': message
        }
        
    except Exception as error:
        return {
            'success': False,
            'error': str(error),
            'message': "Error generando enlace al mapa"
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
        print("   ✅ search_places_tool - Búsqueda de lugares (bancos, SAT)")
        print("   ✅ get_user_fiscal_context - Contexto del usuario")
        print("   ✅ open_map_location - Abrir mapa en ubicación específica")
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