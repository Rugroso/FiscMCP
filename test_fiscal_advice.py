#!/usr/bin/env python3
"""
Test para get_fiscal_advice tool
Prueba el flujo completo de RAG con diferentes escenarios
"""
import asyncio
import sys
import os
from pathlib import Path

# Agregar directorio raíz al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))
os.chdir(root_dir)

# Importar el modelo
from src.main import FiscalAdviceRequest

# Acceder a la función wrapped dentro del decorador
from src.main import get_fiscal_advice as fiscal_advice_tool

# Obtener la función original
get_fiscal_advice = fiscal_advice_tool.fn

async def test_fiscal_advice():
    """Test de get_fiscal_advice con 3 escenarios"""
    
    print("=" * 80)
    print("🧪 TEST: get_fiscal_advice - Recomendaciones Fiscales con RAG")
    print("=" * 80)
    
    # Escenario 1: Restaurante sin RFC
    print("\n📋 ESCENARIO 1: Restaurante pequeño sin RFC")
    print("-" * 80)
    
    request1 = FiscalAdviceRequest(
        actividad='Restaurante de comida mexicana',
        ingresos_anuales=800000,
        estado='Ciudad de México',
        tiene_rfc=False,
        contexto_adicional='Negocio familiar con 2 años operando, queremos formalizarnos'
    )
    
    result1 = await get_fiscal_advice(request1)
    
    print(f"✅ Success: {result1.get('success')}")
    print(f"📊 Documentos encontrados: {result1.get('data', {}).get('matches_count', 0)}")
    print(f"💡 Mensaje: {result1.get('message', 'N/A')}")
    
    if result1.get('success'):
        recommendation = result1.get('data', {}).get('recommendation', '')
        print(f"\n📝 Recomendación (primeros 500 chars):")
        print(recommendation[:500] + "...")
        
        sources = result1.get('data', {}).get('sources', [])
        print(f"\n📚 Fuentes consultadas ({len(sources)}):")
        for i, source in enumerate(sources[:3], 1):
            print(f"  {i}. {source.get('title')} - Similitud: {source.get('similarity', 0):.2f}")
    else:
        print(f"❌ Error: {result1.get('error', 'Desconocido')}")
    
    # Escenario 2: Freelancer con RFC
    print("\n" + "=" * 80)
    print("📋 ESCENARIO 2: Freelancer con RFC buscando optimización fiscal")
    print("-" * 80)
    
    request2 = FiscalAdviceRequest(
        actividad='Desarrollador de software freelance',
        ingresos_anuales=600000,
        estado='Jalisco',
        tiene_rfc=True,
        regimen_actual='RESICO',
        contexto_adicional='Quiero saber si estoy en el régimen correcto y cómo optimizar mis deducciones'
    )
    
    result2 = await get_fiscal_advice(request2)
    
    print(f"✅ Success: {result2.get('success')}")
    print(f"📊 Documentos encontrados: {result2.get('data', {}).get('matches_count', 0)}")
    print(f"💡 Mensaje: {result2.get('message', 'N/A')}")
    
    if result2.get('success'):
        recommendation = result2.get('data', {}).get('recommendation', '')
        print(f"\n📝 Recomendación (primeros 500 chars):")
        print(recommendation[:500] + "...")
        
        sources = result2.get('data', {}).get('sources', [])
        print(f"\n📚 Fuentes consultadas ({len(sources)}):")
        for i, source in enumerate(sources[:3], 1):
            print(f"  {i}. {source.get('title')} - Similitud: {source.get('similarity', 0):.2f}")
            print(f"     Scope: {source.get('scope', 'N/A')}")
    else:
        print(f"❌ Error: {result2.get('error', 'Desconocido')}")
    
    # Escenario 3: Tienda e-commerce mediana
    print("\n" + "=" * 80)
    print("📋 ESCENARIO 3: Tienda e-commerce mediana empresa")
    print("-" * 80)
    
    request3 = FiscalAdviceRequest(
        actividad='Venta de productos electrónicos por internet',
        ingresos_anuales=5000000,
        estado='Nuevo León',
        tiene_rfc=True,
        regimen_actual='Persona Moral',
        contexto_adicional='Tenemos 8 empleados, vendemos principalmente en Mercado Libre y Amazon'
    )
    
    result3 = await get_fiscal_advice(request3)
    
    print(f"✅ Success: {result3.get('success')}")
    print(f"📊 Documentos encontrados: {result3.get('data', {}).get('matches_count', 0)}")
    print(f"💡 Mensaje: {result3.get('message', 'N/A')}")
    
    if result3.get('success'):
        recommendation = result3.get('data', {}).get('recommendation', '')
        print(f"\n📝 Recomendación (primeros 500 chars):")
        print(recommendation[:500] + "...")
        
        sources = result3.get('data', {}).get('sources', [])
        print(f"\n📚 Fuentes consultadas ({len(sources)}):")
        for i, source in enumerate(sources[:3], 1):
            print(f"  {i}. {source.get('title')} - Similitud: {source.get('similarity', 0):.2f}")
            print(f"     URL: {source.get('url', 'N/A')}")
    else:
        print(f"❌ Error: {result3.get('error', 'Desconocido')}")
    
    # Resumen final
    print("\n" + "=" * 80)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 80)
    
    results = [result1, result2, result3]
    success_count = sum(1 for r in results if r.get('success'))
    
    print(f"✅ Exitosos: {success_count}/3")
    print(f"❌ Fallidos: {3 - success_count}/3")
    
    if success_count == 3:
        print("\n🎉 TODAS LAS PRUEBAS PASARON")
        
        # Análisis de calidad
        total_docs = sum(r.get('data', {}).get('matches_count', 0) for r in results if r.get('success'))
        avg_docs = total_docs / success_count if success_count > 0 else 0
        
        print(f"\n📈 Métricas de calidad:")
        print(f"   - Promedio de documentos encontrados: {avg_docs:.1f}")
        print(f"   - Total de fuentes consultadas: {total_docs}")
        
        # Verificar que cada resultado tiene recommendation
        all_have_recs = all(
            bool(r.get('data', {}).get('recommendation')) 
            for r in results if r.get('success')
        )
        print(f"   - Recomendaciones generadas: {'✅ Sí' if all_have_recs else '❌ No'}")
        
        # Verificar que hay fuentes
        all_have_sources = all(
            len(r.get('data', {}).get('sources', [])) > 0 
            for r in results if r.get('success')
        )
        print(f"   - Fuentes consultadas: {'✅ Sí' if all_have_sources else '❌ No'}")
        
    else:
        print("\n⚠️ ALGUNAS PRUEBAS FALLARON")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(test_fiscal_advice())
