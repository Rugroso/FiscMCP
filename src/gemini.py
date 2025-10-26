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
        Similar al generate_recommendation del código Python original
        
        Args:
            profile: Perfil fiscal del usuario
            context: Contexto construido de documentos relevantes
            
        Returns:
            Recomendación detallada en formato markdown
        """
        try:
            import json
            
            system_instruction = (
                "Eres un asesor fiscal para micro-negocios en México. "
                "Responde SOLO con el CONTEXTO provisto. Si no es suficiente, indica claramente "
                "'Información insuficiente en la base'. Usa lenguaje claro. Incluye mini-citas de fuente."
            )
            
            user_prompt = f"""
PERFIL:
{json.dumps(profile, ensure_ascii=False, indent=2)}

TAREA:
1) Recomienda régimen fiscal (y alternativas si aplica).
2) Explica pasos de formalización (RFC, e.firma, CFDI, declaraciones).
3) Lista 5-8 tareas accionables (formato checklist).
4) Si procede, sugiere recordatorios calendario (mensual/anual).
5) Cierra con "Fuentes" (Título -> URL) basadas en los fragmentos usados.

CONTEXTO:
{context}
""".strip()

            # Crear modelo con system instruction
            model = genai.GenerativeModel(
                model_name=config.GEMINI_MODEL,
                system_instruction=system_instruction
            )
            
            # Configurar generación
            generation_config = {
                "temperature": 0.3,
                "max_output_tokens": 1200
            }
            
            response = await asyncio.to_thread(
                model.generate_content,
                user_prompt,
                generation_config=generation_config
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
        Chat con el asistente fiscal usando Gemini
        
        Args:
            message: Mensaje del usuario
            user_context: Contexto del usuario
            chat_history: Historial de conversación
            relevant_docs: Documentos relevantes
            
        Returns:
            Respuesta del asistente
        """
        try:
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
Eres Juan Pablo, un asistente fiscal experto en México especializado en ayudar a micro-negocios y emprendedores con su formalización fiscal.

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
            
            return response.text
            
        except Exception as error:
            print(f"Error en chat con asistente: {error}")
            raise ValueError("Lo siento, hubo un error al procesar tu mensaje. Por favor, intenta de nuevo.")
    
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