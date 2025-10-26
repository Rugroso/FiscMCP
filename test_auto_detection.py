"""
Test para verificar la detección automática de ubicaciones en gemini.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.gemini import detect_user_intent

def test_detection():
    """Prueba la función detect_user_intent con varios casos"""
    
    test_cases = [
        # Casos de BANCOS que DEBEN detectarse
        {
            'message': '¿Dónde hay un Banorte?',
            'expected': {
                'is_location_query': True,
                'location_type': 'bank',
                'requires_map': True
            }
        },
        {
            'message': 'Busca un Banorte en Reforma',
            'expected': {
                'is_location_query': True,
                'location_type': 'bank',
                'requires_map': True,
                'search_query': 'reforma'
            }
        },
        {
            'message': 'necesito ir al banco',
            'expected': {
                'is_location_query': True,
                'location_type': 'bank',
                'requires_map': True
            }
        },
        {
            'message': '¿Hay alguna sucursal de Banorte cerca?',
            'expected': {
                'is_location_query': True,
                'location_type': 'bank',
                'requires_map': True
            }
        },
        {
            'message': 'Muéstrame bancos cerca de Polanco',
            'expected': {
                'is_location_query': True,
                'location_type': 'bank',
                'requires_map': True,
                'search_query': 'polanco'
            }
        },
        
        # Casos de SAT que DEBEN detectarse
        {
            'message': '¿Dónde está el SAT más cercano?',
            'expected': {
                'is_location_query': True,
                'location_type': 'sat',
                'requires_map': True
            }
        },
        {
            'message': 'Necesito ir al SAT',
            'expected': {
                'is_location_query': True,
                'location_type': 'sat',
                'requires_map': True
            }
        },
        {
            'message': '¿Dónde hay oficinas del SAT?',
            'expected': {
                'is_location_query': True,
                'location_type': 'sat',
                'requires_map': True
            }
        },
        {
            'message': 'busca el SAT en Santa Fe',
            'expected': {
                'is_location_query': True,
                'location_type': 'sat',
                'requires_map': True,
                'search_query': 'santa fe'
            }
        },
        
        # Casos que NO deben detectarse como ubicación
        {
            'message': '¿Qué es el SAT?',
            'expected': {
                'is_location_query': False,
                'requires_map': False
            }
        },
        {
            'message': '¿Cómo abro mi cuenta en el banco?',
            'expected': {
                'is_location_query': False,
                'requires_map': False
            }
        },
        {
            'message': 'Explícame el régimen fiscal',
            'expected': {
                'is_location_query': False,
                'requires_map': False
            }
        },
        {
            'message': '¿Cuánto se paga de impuestos?',
            'expected': {
                'is_location_query': False,
                'requires_map': False
            }
        }
    ]
    
    print("🧪 Iniciando pruebas de detección automática...")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        message = test['message']
        expected = test['expected']
        
        result = detect_user_intent(message)
        
        # Verificar resultados esperados
        success = True
        errors = []
        
        if result['is_location_query'] != expected['is_location_query']:
            success = False
            errors.append(f"is_location_query: esperado {expected['is_location_query']}, obtenido {result['is_location_query']}")
        
        if result['requires_map'] != expected['requires_map']:
            success = False
            errors.append(f"requires_map: esperado {expected['requires_map']}, obtenido {result['requires_map']}")
        
        if 'location_type' in expected and result['location_type'] != expected['location_type']:
            success = False
            errors.append(f"location_type: esperado {expected['location_type']}, obtenido {result['location_type']}")
        
        if 'search_query' in expected:
            # Verificar que existe un search_query (puede variar ligeramente)
            if not result['search_query']:
                success = False
                errors.append(f"search_query: esperado '{expected['search_query']}', obtenido None")
        
        # Imprimir resultado
        if success:
            print(f"✅ Test {i}: PASÓ")
            print(f"   Mensaje: '{message}'")
            print(f"   Resultado: {result}")
            passed += 1
        else:
            print(f"❌ Test {i}: FALLÓ")
            print(f"   Mensaje: '{message}'")
            print(f"   Esperado: {expected}")
            print(f"   Obtenido: {result}")
            print(f"   Errores: {', '.join(errors)}")
            failed += 1
        
        print("-" * 60)
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    print(f"✅ Pasaron: {passed}/{len(test_cases)}")
    print(f"❌ Fallaron: {failed}/{len(test_cases)}")
    
    if failed == 0:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
        return True
    else:
        print(f"\n⚠️  {failed} prueba(s) fallaron")
        return False

if __name__ == '__main__':
    success = test_detection()
    sys.exit(0 if success else 1)
