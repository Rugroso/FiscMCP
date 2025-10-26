"""
Test para verificar el tool get_fiscal_roadmap
Simula diferentes perfiles de usuarios y verifica el roadmap generado
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
from src.main import generate_fiscal_roadmap_logic

async def test_roadmap():
    """Prueba el tool get_fiscal_roadmap con diferentes perfiles"""
    
    print("🧪 Probando get_fiscal_roadmap...")
    print("=" * 60)
    
    test_cases = [
        {
            'name': 'Usuario nuevo (sin nada)',
            'params': {
                'actividad': 'Diseñador gráfico freelance',
                'ingresos_anuales': 350000,
                'tiene_rfc': False,
                'tiene_efirma': False,
                'emite_cfdi': False
            },
            'expected_current': 0,
            'expected_completed': 0
        },
        {
            'name': 'Usuario con RFC solamente',
            'params': {
                'actividad': 'Venta de comida preparada',
                'ingresos_anuales': 500000,
                'tiene_rfc': True,
                'tiene_efirma': False,
                'emite_cfdi': False
            },
            'expected_current': 1,
            'expected_completed': 1
        },
        {
            'name': 'Usuario con RFC y e.firma',
            'params': {
                'actividad': 'Consultoría TI',
                'ingresos_anuales': 800000,
                'tiene_rfc': True,
                'tiene_efirma': True,
                'emite_cfdi': False
            },
            'expected_current': 2,
            'expected_completed': 2
        },
        {
            'name': 'Usuario completamente formal',
            'params': {
                'actividad': 'E-commerce',
                'ingresos_anuales': 1200000,
                'tiene_rfc': True,
                'tiene_efirma': True,
                'emite_cfdi': True
            },
            'expected_current': 4,
            'expected_completed': 4
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        name = test['name']
        params = test['params']
        expected_current = test['expected_current']
        expected_completed = test['expected_completed']
        
        print(f"\n📝 Test {i}: {name}")
        print("-" * 60)
        print(f"   Actividad: {params['actividad']}")
        print(f"   Ingresos: ${params['ingresos_anuales']:,}")
        print(f"   RFC: {params['tiene_rfc']}, e.firma: {params['tiene_efirma']}, CFDI: {params['emite_cfdi']}")
        
        try:
            # Llamar a la lógica del tool (función auxiliar sin decorador)
            result = await generate_fiscal_roadmap_logic(**params)
            
            if not result['success']:
                print(f"   ❌ FALLÓ: {result.get('error', 'Error desconocido')}")
                failed += 1
                continue
            
            data = result['data']
            
            # Verificar estructura
            required_keys = ['steps', 'currentIndex', 'totalSteps', 'completedSteps', 'progressPercent', 'goal']
            missing_keys = [k for k in required_keys if k not in data]
            
            if missing_keys:
                print(f"   ❌ FALLÓ: Faltan keys: {missing_keys}")
                failed += 1
                continue
            
            # Verificar valores
            current = data['currentIndex']
            completed = data['completedSteps']
            total = data['totalSteps']
            progress = data['progressPercent']
            
            print(f"\n   📊 Resultado:")
            print(f"      Total pasos: {total}")
            print(f"      Completados: {completed}")
            print(f"      Índice actual: {current}")
            print(f"      Progreso: {progress}%")
            print(f"\n   📋 Pasos:")
            
            for step in data['steps']:
                status_icon = '✅' if step['status'] == 'done' else '🎯' if step['status'] == 'active' else '🔒'
                print(f"      {status_icon} {step['title']} - {step['status']}")
            
            print(f"\n   🎯 Meta: {data['goal']['title']}")
            
            # Verificar expectativas
            if completed != expected_completed:
                print(f"\n   ❌ FALLÓ: Se esperaban {expected_completed} pasos completados, se obtuvieron {completed}")
                failed += 1
                continue
            
            print(f"\n   ✅ PASÓ: Roadmap generado correctamente")
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
        print("✨ El tool get_fiscal_roadmap funciona correctamente")
        return True
    else:
        print(f"\n⚠️  {failed} prueba(s) fallaron")
        return False

if __name__ == '__main__':
    success = asyncio.run(test_roadmap())
    sys.exit(0 if success else 1)
