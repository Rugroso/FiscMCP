"""
Cliente para Supabase - Base de datos y funciones para FiscAI
"""
import asyncio
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from .config import config

if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("Faltan variables de entorno de Supabase")

class SupabaseClient:
    """Cliente para interactuar con Supabase"""
    
    def __init__(self):
        # Cliente principal con service role key
        self.client: Client = create_client(
            config.SUPABASE_URL,
            config.SUPABASE_SERVICE_ROLE_KEY
        )
    
    async def search_similar_documents(
        self, 
        embedding: List[float], 
        limit: int = 5,
        threshold: float = None
    ) -> List[Dict[str, Any]]:
        """
        Buscar documentos similares usando embeddings
        Compatible con match_fiscai_documents RPC
        
        Args:
            embedding: Vector de embedding para la búsqueda
            limit: Número máximo de documentos a retornar
            threshold: Umbral de similitud (default: 0.6)
            
        Returns:
            Lista de documentos similares con campos: title, scope, content, source_url, similarity
        """
        try:
            if threshold is None:
                threshold = config.SIMILARITY_THRESHOLD if hasattr(config, 'SIMILARITY_THRESHOLD') else 0.6
            
            print(f"[SUPABASE] Buscando documentos similares...")
            print(f"[SUPABASE] - Embedding dimension: {len(embedding)}")
            print(f"[SUPABASE] - Match threshold: {threshold}")
            print(f"[SUPABASE] - Match count: {limit}")
            
            # Preparar payload - usar query_embedding como en el script que funciona
            payload = {
                'query_embedding': embedding,  # float8[] - igual que simulate_recomendation.py
                'match_threshold': threshold,
                'match_count': limit
            }
            
            # Intentar con match_fiscai_documents primero
            try:
                print("[SUPABASE] Llamando match_fiscai_documents RPC...")
                response = await asyncio.to_thread(
                    lambda: self.client.rpc('match_fiscai_documents', payload).execute()
                )
                
                if response.data:
                    print(f"[SUPABASE] ✅ Encontrados {len(response.data)} documentos")
                    # Imprimir primer resultado para debug
                    if response.data:
                        first = response.data[0]
                        print(f"[SUPABASE] Ejemplo: {first.get('title', 'N/A')} (similarity: {first.get('similarity', 0)})")
                    return response.data
            except Exception as rpc_error:
                print(f"[SUPABASE] ⚠️  Error en match_fiscai_documents: {rpc_error}")
                import traceback
                traceback.print_exc()
                # Continuar con fallback
            
            # Fallback: intentar con match_documents
            print("[SUPABASE] Intentando fallback con match_documents...")
            response = await asyncio.to_thread(
                lambda: self.client.rpc('match_documents', payload).execute()
            )
            
            if response.data:
                print(f"[SUPABASE] ✅ Encontrados {len(response.data)} documentos (fallback)")
                return response.data
            
            print("[SUPABASE] ⚠️  No se encontraron documentos")
            return []
            
        except Exception as error:
            print(f"[SUPABASE] ❌ Error buscando documentos similares: {error}")
            import traceback
            traceback.print_exc()
            return []
    
    async def search_documents_by_scope(
        self, 
        embedding: List[float], 
        scope: str,
        limit: int = 5,
        threshold: float = None
    ) -> List[Dict[str, Any]]:
        """
        Buscar documentos similares filtrando por scope específico
        
        Args:
            embedding: Vector de embedding para la búsqueda
            scope: Scope a filtrar (ej: "beneficios", "regimenes", "obligaciones")
            limit: Número máximo de documentos a retornar
            threshold: Umbral de similitud (default: 0.5)
            
        Returns:
            Lista de documentos similares filtrados por scope
        """
        try:
            if threshold is None:
                threshold = 0.5
            
            print(f"[SUPABASE] Buscando documentos con scope '{scope}'...")
            print(f"[SUPABASE] - Embedding dimension: {len(embedding)}")
            print(f"[SUPABASE] - Match threshold: {threshold}")
            print(f"[SUPABASE] - Match count: {limit}")
            
            # Buscar todos los documentos similares primero
            all_docs = await self.search_similar_documents(
                embedding=embedding,
                limit=limit * 2,  # Buscar más para compensar el filtrado
                threshold=threshold
            )
            
            # Filtrar por scope
            filtered_docs = [
                doc for doc in all_docs 
                if doc.get('scope', '').lower() == scope.lower()
            ]
            
            # Limitar resultados
            filtered_docs = filtered_docs[:limit]
            
            print(f"[SUPABASE] ✅ Encontrados {len(filtered_docs)} documentos con scope '{scope}'")
            
            return filtered_docs
            
        except Exception as error:
            print(f"[SUPABASE] ❌ Error buscando documentos por scope: {error}")
            import traceback
            traceback.print_exc()
            return []
    
    async def get_user_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener contexto del usuario desde la base de datos
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Contexto del usuario o None si no se encuentra
        """
        try:
            response = await asyncio.to_thread(
                self.client.table('users').select('*').eq('id', user_id).single().execute
            )
            
            if response.data:
                return response.data
            return None
            
        except Exception as error:
            print(f"Error obteniendo contexto del usuario: {error}")
            return None
    
    async def save_chat_message(
        self,
        user_id: str,
        message: str,
        response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Guardar mensaje del chat
        
        Args:
            user_id: ID del usuario
            message: Mensaje del usuario
            response: Respuesta del asistente
            metadata: Metadatos adicionales
            
        Returns:
            Registro guardado o None si falló
        """
        try:
            import datetime
            
            data = {
                'user_id': user_id,
                'message': message,
                'response': response,
                'metadata': metadata or {},
                'created_at': datetime.datetime.now().isoformat()
            }
            
            response = await asyncio.to_thread(
                self.client.table('chat_history').insert(data).execute
            )
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as error:
            print(f"Error guardando mensaje: {error}")
            return None
    
    async def get_chat_history(
        self, 
        user_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtener historial de chat del usuario
        
        Args:
            user_id: ID del usuario
            limit: Número máximo de mensajes
            
        Returns:
            Lista de mensajes del historial
        """
        try:
            response = await asyncio.to_thread(
                self.client.table('chat_history')
                .select('*')
                .eq('user_id', user_id)
                .order('created_at', desc=True)
                .limit(limit)
                .execute
            )
            
            if response.data:
                return response.data
            return []
            
        except Exception as error:
            print(f"Error obteniendo historial: {error}")
            return []
    
    async def find_similar_fiscal_cases(
        self, 
        profile: Dict[str, Any], 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Buscar casos fiscales similares
        
        Args:
            profile: Perfil del usuario
            limit: Número máximo de casos
            
        Returns:
            Lista de casos similares
        """
        try:
            response = await asyncio.to_thread(
                self.client.rpc,
                'find_similar_fiscal_cases',
                {
                    'query_profile': profile,
                    'match_count': limit
                }
            )
            
            if response.data:
                return response.data
            return []
            
        except Exception as error:
            print(f"Error buscando casos similares: {error}")
            return []


# Instancia global del cliente
supabase_client = SupabaseClient()