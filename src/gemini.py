"""
Cliente para Google Gemini AI - Integración con FiscAI
"""
import asyncio
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from .config import config

# Configurar Gemini
if config.GEMINI_API_KEY:
    genai.configure(api_key=config.GEMINI_API_KEY)
else:
    raise ValueError("GEMINI_API_KEY no está configurada")

# System Prompt con detección de ubicaciones
SYSTEM_PROMPT = """
Eres Juan Pablo, un asistente fiscal experto en México especializado en ayudar a micro y pequeños negocios.

**CAPACIDADES ESPECIALES:**

1. **Ubicaciones de Bancos y SAT:**
   - Cuando el usuario pregunte sobre dónde encontrar un banco Banorte o una oficina del SAT
   - USA la herramienta 'open_map_location' para abrir el mapa
   - Ejemplos de preguntas que deben activar el mapa:
     * "¿Dónde hay un Banorte?"
     * "¿Dónde está el SAT más cercano?"
     * "Necesito ir a un banco"
     * "Muéstrame oficinas del SAT"
     * "Busca un Banorte en Reforma"
     * "¿Hay alguna oficina del SAT cerca?"
   
2. **Asesoría Fiscal:**
   - Proporciona información sobre régimen fiscal, obligaciones, trámites
   - USA la herramienta 'get_fiscal_advice' para consultas de formalización
   
3. **Análisis de Riesgo:**
   - Evalúa la situación fiscal del usuario
   - USA la herramienta 'analyze_fiscal_risk' cuando pregunten sobre su nivel de cumplimiento

**FORMATO DE RESPUESTA PARA UBICACIONES:**
Cuando uses 'open_map_location', tu respuesta debe ser breve y clara:
- "¡Claro! Te abro el mapa con los Banorte más cercanos."
- "Perfecto, te muestro las oficinas del SAT en tu zona."
- "Busco Banorte en Reforma para ti."

**NO incluyas las coordenadas o detalles técnicos en tu respuesta, eso lo maneja el mapa automáticamente.**

**Tono:** Cercano, profesional pero amigable, como un asesor de confianza.
"""

def detect_user_intent(message: str) -> Dict[str, Any]:
    """
    Detecta la intención del usuario antes de llamar a Gemini
    para optimizar el uso de herramientas
    """
    message_lower = message.lower()
    
    # Palabras clave para búsqueda de ubicaciones
    location_keywords = {
        'bank': ['banorte', 'banco', 'sucursal bancaria', 'ir al banco', 'sucursal'],
        'sat': ['sat', 'oficina del sat', 'servicio de administración tributaria', 
                'centro tributario', 'módulo de atención', 'oficina tributaria']
    }
    
    # Verbos que indican búsqueda de ubicación
    location_verbs = ['dónde', 'donde', 'ubica', 'encuentra', 'busca', 'hay', 
                      'mostrar', 'muestra', 'llevar', 'ir', 'cerca', 'cercano',
                      'necesito ir', 'quiero ir', 'cómo llegar']
    
    # Detectar tipo de ubicación
    location_type = None
    if any(keyword in message_lower for keyword in location_keywords['bank']):
        location_type = 'bank'
    elif any(keyword in message_lower for keyword in location_keywords['sat']):
        location_type = 'sat'
    
    # Detectar si es una pregunta de ubicación
    is_location_query = any(verb in message_lower for verb in location_verbs)
    
    # Extraer posible query específica (nombre de lugar)
    search_query = None
    location_indicators = [' en ', ' de ', ' cerca de ', ' por ']
    for indicator in location_indicators:
        if indicator in message_lower:
            parts = message_lower.split(indicator, 1)
            if len(parts) > 1:
                # Extraer hasta el siguiente espacio o final
                potential_query = parts[1].split('.')[0].split(',')[0].split('?')[0].strip()
                # Solo si no es muy corto
                if len(potential_query) > 2:
                    search_query = potential_query
                    break
    
    return {
        'is_location_query': is_location_query and location_type is not None,
        'location_type': location_type,
        'search_query': search_query,
        'requires_map': is_location_query and location_type is not None
    }

class GeminiClient:
    """Cliente para interactuar con Google Gemini AI"""
    
    def __init__(self):
        self.model = genai.GenerativeModel(config.GEMINI_MODEL)
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Genera embedding para un texto usando Gemini
        Compatible con el formato del código Python original
        
        Args:
            text: Texto para generar embedding
            
        Returns:
            Lista de números representando el embedding
        """
        try:
            result = await asyncio.to_thread(
                genai.embed_content,
                model=config.GEMINI_EMBED_MODEL,
                content=text,
                task_type="RETRIEVAL_QUERY",  # Mayúsculas como en simulate_recomendation.py
                output_dimensionality=config.EMBED_DIM
            )
            
            # Extraer embedding según la estructura de respuesta
            if isinstance(result, dict):
                if "embedding" in result:
                    emb = result["embedding"]
                    if isinstance(emb, dict) and "values" in emb:
                        return emb["values"]
                    if isinstance(emb, list):
                        return emb
                if "embeddings" in result and isinstance(result["embeddings"], list) and result["embeddings"]:
                    e0 = result["embeddings"][0]
                    if isinstance(e0, dict) and "values" in e0:
                        return e0["values"]
                    if isinstance(e0, list):
                        return e0
            
            # Si result tiene atributo embedding
            if hasattr(result, "embedding"):
                emb = getattr(result, "embedding")
                if isinstance(emb, dict) and "values" in emb:
                    return emb["values"]
                if hasattr(emb, "values"):
                    return emb.values
                if isinstance(emb, list):
                    return emb
            
            # Fallback
            if hasattr(result, "embeddings"):
                emb_list = getattr(result, "embeddings") or []
                if emb_list:
                    e0 = emb_list[0]
                    if isinstance(e0, dict) and "values" in e0:
                        return e0["values"]
                    if hasattr(e0, "values"):
                        return e0.values
                    if isinstance(e0, list):
                        return e0
            
            raise RuntimeError("No se pudo extraer embedding de la respuesta")
            
        except Exception as error:
            print(f"Error generando embedding: {error}")
            raise error
    
    async def generate_recommendation(
        self, 
        profile: Dict[str, Any], 
        context: str
    ) -> str:
        """
        Genera recomendación fiscal usando RAG (contexto de documentos relevantes)
        Usa el mismo prompt que simulate_recomendation.py que funciona
        
        Args:
            profile: Perfil fiscal del usuario
            context: Contexto construido de documentos relevantes
            
        Returns:
            Recomendación detallada en formato markdown
        """
        try:
            import json
            
            system_instruction = (
                "Eres un contador experto en México. "
                "Responde SOLO con el CONTEXTO provisto. Si no es suficiente, indica claramente "
                "'Información insuficiente en la base'. Usa lenguaje claro y profesional."
            )
            
            user_prompt = f"""
PERFIL:
{json.dumps(profile, ensure_ascii=False, indent=2)}

TAREA:
Como contador en México, necesito analizar este perfil y sugerir:

1) **Régimen fiscal más conveniente:**
   - Identifica el régimen fiscal óptimo para este perfil
   - Explica brevemente por qué es el más adecuado
   - Menciona alternativas si aplican

2) **Pasos específicos de formalización:**
   - Lista los pasos concretos para formalizarse (RFC, e.firma, CFDI, declaraciones)
   - Indica el orden recomendado
   - Menciona requisitos y documentos necesarios

3) **Fuentes oficiales del SAT consultadas:**
   - Lista las fuentes utilizadas con formato: Título -> URL
   - Usa solo las fuentes del CONTEXTO provisto
   - Cita las secciones relevantes

CONTEXTO:
{context}
""".strip()

            # Crear modelo con system instruction (igual que simulate_recomendation.py)
            model = genai.GenerativeModel(
                model_name=config.GEMINI_MODEL,
                system_instruction=system_instruction,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 1200
                }
            )
            
            # Generar contenido
            response = await asyncio.to_thread(
                model.generate_content,
                user_prompt
            )
            
            return response.text or "(Sin texto)"
            
        except Exception as error:
            print(f"Error generando recomendación RAG: {error}")
            import traceback
            traceback.print_exc()
            raise error
    
    async def enhance_recommendation(
        self, 
        lambda_response: Dict[str, Any], 
        similar_cases: List[Dict[str, Any]], 
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Enriquecer recomendación fiscal con Gemini
        
        Args:
            lambda_response: Respuesta base del sistema
            similar_cases: Casos similares encontrados
            user_context: Contexto del usuario
            
        Returns:
            Recomendación enriquecida
        """
        try:
            prompt = f"""
Eres un experto asesor fiscal mexicano. Basándote en la siguiente información, genera una recomendación personalizada y detallada:

**Recomendación Base:**
{lambda_response.get('recommendation', lambda_response)}

**Perfil del Usuario:**
{lambda_response.get('profile', {})}

**Casos Similares (para referencia):**
{similar_cases[:3]}

{f"**Contexto del Usuario:**\n{user_context}" if user_context else ""}

**Instrucciones:**
1. Mantén el formato de la recomendación original con sus secciones (Régimen Fiscal, Pasos, Checklist, etc.)
2. Usa texto en **negrita** para títulos importantes
3. Usa *cursiva* para notas adicionales
4. Mantén los bullets y numeración
5. Asegúrate de incluir las fuentes al final
6. Sé específico con montos, fechas y requisitos
7. Usa lenguaje claro y accesible para micro-negocios

Responde SOLO con la recomendación mejorada, sin comentarios adicionales.
"""

            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            enhanced_text = response.text
            
            return {
                **lambda_response,
                'recommendation': enhanced_text,
                'enhanced': True,
                'enhanced_at': asyncio.get_event_loop().time()
            }
            
        except Exception as error:
            print(f"Error enriqueciendo recomendación: {error}")
            # Si falla Gemini, devolver la respuesta original
            return lambda_response
    
    async def chat_with_assistant(
        self,
        message: str,
        user_context: Optional[Dict[str, Any]] = None,
        chat_history: List[Dict[str, Any]] = None,
        relevant_docs: List[Dict[str, Any]] = None
    ) -> str:
        """
        Chat con el asistente fiscal usando Gemini con detección automática de intenciones
        
        Args:
            message: Mensaje del usuario
            user_context: Contexto del usuario
            chat_history: Historial de conversación
            relevant_docs: Documentos relevantes
            
        Returns:
            Respuesta del asistente en formato JSON con texto, deep_link y tool_used
        """
        try:
            # 1. DETECCIÓN AUTOMÁTICA DE INTENCIONES
            intent = detect_user_intent(message)
            
            # 2. SI ES UNA CONSULTA DE UBICACIÓN, LLAMAR DIRECTAMENTE A open_map_location
            if intent['requires_map']:
                # Importar la función del mapa
                from .main import open_map_location
                
                # Llamar a la herramienta
                map_response = await open_map_location(
                    location_type=intent['location_type'],
                    search_query=intent['search_query']
                )
                
                # Retornar respuesta estructurada
                import json
                return json.dumps({
                    'text': map_response['user_message'],
                    'deep_link': map_response['deep_link'],
                    'tool_used': 'open_map_location',
                    'details': {
                        'location_type': intent['location_type'],
                        'search_query': intent['search_query']
                    }
                }, ensure_ascii=False)
            
            # 3. SI NO ES UBICACIÓN, CONTINUAR CON FLUJO NORMAL DE CHAT
            if chat_history is None:
                chat_history = []
            if relevant_docs is None:
                relevant_docs = []
            
            # Construir historial de chat para contexto
            history_context = ""
            if chat_history:
                history_items = []
                for h in chat_history[-5:]:  # Últimos 5 mensajes
                    history_items.append(f"Usuario: {h.get('message', '')}")
                    history_items.append(f"Asistente: {h.get('response', '')}")
                history_context = "\n\n".join(history_items)
            
            user_info = ""
            if user_context:
                user_info = f"""**Información del Usuario:**
- Nombre: {user_context.get('name', 'Usuario')}
- Email: {user_context.get('email', 'No disponible')}
- Actividad: {user_context.get('actividad', 'No especificada')}"""
                
                if user_context.get('ingresos_anuales'):
                    user_info += f"\n- Ingresos anuales: ${user_context['ingresos_anuales']:,}"
                    
                if user_context.get('estado'):
                    user_info += f"\n- Estado: {user_context['estado']}"
            
            docs_context = ""
            if relevant_docs:
                docs_list = []
                for doc in relevant_docs:
                    content = doc.get('content', '')[:200]
                    docs_list.append(f"- {doc.get('title', 'Documento')}: {content}...")
                docs_context = f"**Documentos de Referencia:**\n" + "\n".join(docs_list)
            
            prompt = f"""
{SYSTEM_PROMPT}

{user_info}

{f"**Conversación Previa:**\n{history_context}" if history_context else ""}

{docs_context}

**Pregunta Actual del Usuario:**
{message}

**Instrucciones:**
- Responde en español de manera clara y profesional
- Usa ejemplos prácticos y específicos para México
- Si mencionas montos o fechas, sé específico
- Usa **negrita** para conceptos importantes
- Usa *cursiva* para notas adicionales
- Si no tienes suficiente información, pregunta amablemente
- Mantén un tono amigable pero profesional
- Si la pregunta requiere información personal del usuario que no tienes, pídela

Responde de manera concisa pero completa:
"""

            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            # Retornar respuesta simple de chat
            import json
            return json.dumps({
                'text': response.text,
                'deep_link': None,
                'tool_used': 'chat',
                'details': {}
            }, ensure_ascii=False)
            
        except Exception as error:
            print(f"Error en chat con asistente: {error}")
            import json
            return json.dumps({
                'text': f"Lo siento, hubo un error al procesar tu mensaje: {str(error)}",
                'deep_link': None,
                'tool_used': 'error',
                'details': {'error': str(error)}
            }, ensure_ascii=False)
    
    async def analyze_fiscal_risk(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analizar perfil fiscal y calcular riesgo
        
        Args:
            profile: Perfil fiscal del usuario
            
        Returns:
            Análisis de riesgo
        """
        try:
            prompt = f"""
Analiza el siguiente perfil fiscal y calcula un nivel de riesgo:

**Perfil:**
{profile}

Responde en JSON con este formato exacto:
{{
  "score": <número del 0 al 100, donde 0 es sin riesgo y 100 es alto riesgo>,
  "level": "<Verde|Amarillo|Rojo>",
  "message": "<mensaje breve del estado>",
  "details": {{
    "has_rfc": <boolean>,
    "has_efirma": <boolean>,
    "emite_cfdi": <boolean>,
    "declara_mensual": <boolean>
  }},
  "recommendations": [
    "<lista de recomendaciones específicas>"
  ]
}}

Criterios de evaluación:
- Verde (0-30): Cumplimiento fiscal óptimo
- Amarillo (31-60): Requiere atención en algunas áreas
- Rojo (61-100): Alto riesgo fiscal, acción inmediata requerida
"""

            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            text = response.text
            
            # Extraer JSON de la respuesta
            import json
            import re
            
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                return json.loads(json_match.group(0))
            
            raise ValueError("No se pudo parsear la respuesta de análisis de riesgo")
            
        except Exception as error:
            print(f"Error analizando riesgo fiscal: {error}")
            # Respuesta por defecto en caso de error
            return {
                'score': 0,
                'level': 'Verde',
                'message': 'Análisis no disponible',
                'details': {
                    'has_rfc': profile.get('has_rfc', False),
                    'has_efirma': profile.get('has_efirma', False),
                    'emite_cfdi': profile.get('emite_cfdi', False),
                    'declara_mensual': profile.get('declara_mensual', False)
                },
                'recommendations': []
            }


# Instancia global del cliente
gemini_client = GeminiClient()