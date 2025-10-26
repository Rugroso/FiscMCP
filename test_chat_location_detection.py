"""
Test para verificar que el chatbot genera deep links correctamente
cuando detecta preguntas sobre ubicaciones de bancos o SAT
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
import json
from src.gemini import gemini_client

async def test_chat_with_location_detection():
    """Prueba el chat con detección automática de ubicaciones"""
    
    print("🧪 Probando detección automática en chat_with_assistant...")
    print("=" * 60)
    
    test_cases = [
        {
            'message': '¿Dónde hay un Banorte?',
            'expected_type': 'bank',
            'expected_deep_link_contains': 'fiscai://map?type=bank'
        },
        {
            'message': 'Busca un Banorte en Reforma',
            'expected_type': 'bank',
            'expected_deep_link_contains': 'fiscai://map?type=bank&query=reforma'
        },
        {
            'message': 'Necesito ir al SAT',
            'expected_type': 'sat',
            'expected_deep_link_contains': 'fiscai://map?type=sat'
        },
        {
            'message': '¿Dónde está el SAT en Santa Fe?',
            'expected_type': 'sat',
            'expected_deep_link_contains': 'fiscai://map?type=sat&query=santa'
        },
        {
            'message': '¿Qué es el RFC?',
            'expected_type': None,
            'expected_deep_link_contains': None
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        message = test['message']
        expected_type = test['expected_type']
        expected_deep_link = test['expected_deep_link_contains']
        
        print(f"\n📝 Test {i}: '{message}'")
        print("-" * 60)
        
        try:
            # Llamar al chat
            response = await gemini_client.chat_with_assistant(message)
            
            # Parsear respuesta JSON
            response_data = json.loads(response)
            
            print(f"   Respuesta: {response_data.get('text', '')}")
            print(f"   Deep Link: {response_data.get('deep_link', 'None')}")
            print(f"   Tool Used: {response_data.get('tool_used', 'chat')}")
            
            # Verificar si es una pregunta de ubicación
            if expected_type:
                # Debe tener deep_link
                if not response_data.get('deep_link'):
                    print(f"   ❌ FALLÓ: Se esperaba deep_link pero no se generó")
                    failed += 1
                    continue
                
                # Verificar que el deep_link contiene el tipo correcto
                deep_link = response_data['deep_link']
                if expected_deep_link.lower() not in deep_link.lower():
                    print(f"   ❌ FALLÓ: Deep link esperado contiene '{expected_deep_link}' pero se obtuvo '{deep_link}'")
                    failed += 1
                    continue
                
                # Verificar tool_used
                if response_data.get('tool_used') != 'open_map_location':
                    print(f"   ❌ FALLÓ: Se esperaba tool_used='open_map_location' pero se obtuvo '{response_data.get('tool_used')}'")
                    failed += 1
                    continue
                
                print(f"   ✅ PASÓ: Deep link generado correctamente")
                passed += 1
                
            else:
                # No debe tener deep_link (pregunta no relacionada con ubicación)
                if response_data.get('deep_link'):
                    print(f"   ❌ FALLÓ: No se esperaba deep_link pero se generó: {response_data['deep_link']}")
                    failed += 1
                    continue
                
                # Debe usar 'chat' como tool
                if response_data.get('tool_used') != 'chat':
                    print(f"   ❌ FALLÓ: Se esperaba tool_used='chat' pero se obtuvo '{response_data.get('tool_used')}'")
                    failed += 1
                    continue
                
                print(f"   ✅ PASÓ: Procesado correctamente como chat normal")
                passed += 1
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    print(f"✅ Pasaron: {passed}/{len(test_cases)}")
    print(f"❌ Fallaron: {failed}/{len(test_cases)}")
    
    if failed == 0:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("✨ El chatbot detecta ubicaciones y genera deep links correctamente")
        return True
    else:
        print(f"\n⚠️  {failed} prueba(s) fallaron")
        return False

if __name__ == '__main__':
    success = asyncio.run(test_chat_with_location_detection())
    sys.exit(0 if success else 1)
