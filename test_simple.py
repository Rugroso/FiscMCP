#!/usr/bin/env python3
"""
Script de prueba simple basado en simulate_recomendation.py que funciona
Este script usa exactamente la misma lógica que funciona
"""

import os
import sys
import asyncio
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dotenv import load_dotenv
from src.config import config
from src.gemini import gemini_client
from src.supabase_client import supabase_client

async def test_simple_rag():
    """Prueba simple del flujo RAG usando la lógica que funciona"""
    
    print("="*60)
    print("TEST RAG - Usando lógica de simulate_recomendation.py")
    print("="*60)
    
    # Perfil de prueba (igual al de simulate_recomendation.py)
    profile = {
        "actividad": "Diseñador gráfico freelance",
        "ingresos_anuales": 450000,
        "empleados": 0,
        "metodos_pago": ["transferencia", "efectivo"],
        "estado": "Ciudad de México",
        "has_rfc": True,
        "has_efirma": True,
        "emite_cfdi": True,
        "declara_mensual": True
    }
    
    print(f"\n1. PERFIL:")
    print(f"   Actividad: {profile['actividad']}")
    print(f"   Ingresos: ${profile['ingresos_anuales']:,}")
    print(f"   Estado: {profile['estado']}")
    
    # Generar query semántica (igual a profile_to_query)
    parts = []
    parts.append(f"Actividad: {profile.get('actividad','')}")
    parts.append(f"Ingresos anuales estimados: {profile.get('ingresos_anuales','')}")
    parts.append(f"Número de empleados: {profile.get('empleados','')}")
    parts.append(f"Métodos de pago: {', '.join(profile.get('metodos_pago', []))}")
    parts.append(f"Entidad federativa: {profile.get('estado','')}")
    parts.append(f"¿Tiene RFC?: {profile.get('has_rfc')}")
    parts.append(f"¿Tiene e.firma?: {profile.get('has_efirma')}")
    parts.append(f"¿Emite CFDI?: {profile.get('emite_cfdi')}")
    parts.append(f"¿Presenta declaraciones mensuales?: {profile.get('declara_mensual')}")
    
    query = ("Perfil fiscal. Necesito sugerir régimen, pasos de formalización, "
             "obligaciones y calendario básico, citando fuentes del SAT: \n" + "\n".join(parts))
    
    print(f"\n2. QUERY GENERADA:")
    print(f"   {query[:150]}...")
    
    # Generar embedding
    print(f"\n3. GENERANDO EMBEDDING...")
    print(f"   Modelo: {config.GEMINI_EMBED_MODEL}")
    print(f"   Dimensión: {config.EMBED_DIM}")
    
    try:
        embedding = await gemini_client.generate_embedding(query)
        print(f"   ✅ Embedding generado: {len(embedding)} dimensiones")
        print(f"   Primeros 5 valores: {embedding[:5]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Buscar documentos
    print(f"\n4. BUSCANDO DOCUMENTOS EN SUPABASE...")
    print(f"   Threshold: {config.SIMILARITY_THRESHOLD}")
    print(f"   Top-K: {config.TOPK_DOCUMENTS}")
    
    try:
        documents = await supabase_client.search_similar_documents(
            embedding,
            limit=config.TOPK_DOCUMENTS,
            threshold=config.SIMILARITY_THRESHOLD
        )
        
        if documents:
            print(f"   ✅ Encontrados {len(documents)} documentos")
            for i, doc in enumerate(documents, 1):
                print(f"\n   Documento {i}:")
                print(f"   - Título: {doc.get('title', 'N/A')}")
                print(f"   - Scope: {doc.get('scope', 'N/A')}")
                print(f"   - Similitud: {doc.get('similarity', 0):.4f}")
                print(f"   - URL: {doc.get('source_url', 'N/A')[:50]}...")
        else:
            print(f"   ⚠️  No se encontraron documentos")
            print(f"\n   DIAGNÓSTICO:")
            print(f"   - Verifica que la tabla fiscai_documents tenga datos")
            print(f"   - Ejecuta: SELECT COUNT(*) FROM fiscai_documents;")
            print(f"   - Si está vacía, necesitas insertar documentos primero")
            return
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Construir contexto (igual a build_context)
    print(f"\n5. CONSTRUYENDO CONTEXTO...")
    blocks = []
    for i, r in enumerate(documents, start=1):
        title = r.get("title","")
        scope = r.get("scope","")
        url   = r.get("source_url","")
        txt   = r.get("content","")
        blocks.append(f"[{i}] {title} — {scope}\nFuente: {url}\n{txt}")
    
    context = "\n\n".join(blocks)
    print(f"   ✅ Contexto construido: {len(context)} caracteres")
    
    # Generar recomendación
    print(f"\n6. GENERANDO RECOMENDACIÓN CON GEMINI...")
    print(f"   Modelo: {config.GEMINI_MODEL}")
    
    try:
        recommendation = await gemini_client.generate_recommendation(profile, context)
        
        print(f"\n{'='*60}")
        print("RECOMENDACIÓN GENERADA:")
        print('='*60)
        print(recommendation)
        print('='*60)
        
        print(f"\n✅ ÉXITO:")
        print(f"   - Longitud: {len(recommendation)} caracteres")
        print(f"   - Fuentes utilizadas: {len(documents)}")
        print(f"   - Modelo generación: {config.GEMINI_MODEL}")
        print(f"   - Modelo embedding: {config.GEMINI_EMBED_MODEL}")
        
        return {
            'success': True,
            'recommendation': recommendation,
            'sources': documents,
            'matches_count': len(documents)
        }
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    load_dotenv()
    
    print("\n" + "="*60)
    print("CONFIGURACIÓN:")
    print("="*60)
    print(f"SUPABASE_URL: {config.SUPABASE_URL[:30]}...")
    print(f"GEMINI_MODEL: {config.GEMINI_MODEL}")
    print(f"GEMINI_EMBED_MODEL: {config.GEMINI_EMBED_MODEL}")
    print(f"EMBED_DIM: {config.EMBED_DIM}")
    print(f"SIMILARITY_THRESHOLD: {config.SIMILARITY_THRESHOLD}")
    print(f"TOPK_DOCUMENTS: {config.TOPK_DOCUMENTS}")
    print()
    
    result = await test_simple_rag()
    
    if result and result.get('success'):
        print("\n" + "="*60)
        print("✅ PRUEBA COMPLETADA EXITOSAMENTE")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ PRUEBA FALLÓ")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
